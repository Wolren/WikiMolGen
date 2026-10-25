"""Tests for the PubChem 3D conformer shortcut in MoleculeGenerator3D.

SDF output goes into a scratch dir the tests create and remove
themselves; pytest's tmp_path is unavailable under the DSH sandbox.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from rdkit import Chem

from wikimolgen.rendering.wikimol3d import MoleculeGenerator3D

SDF_3D = """
     RDKit          3D

  9  8  0  0  0  0  0  0  0  0999 V2000
    0.8817   -0.0448   -0.0147 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.5816   -0.3761    0.0511 C   0  0  0  0  0  0  0  0  0  0  0  0
   -1.3484    0.7520    0.1807 O   0  0  0  0  0  0  0  0  0  0  0  0
    1.2650    0.1742    1.0122 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.0165    0.8705   -0.6090 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.4768   -0.8948   -0.3919 H   0  0  0  0  0  0  0  0  0  0  0  0
   -0.7879   -0.9889    0.9648 H   0  0  0  0  0  0  0  0  0  0  0  0
   -0.8350   -1.0051   -0.8168 H   0  0  0  0  0  0  0  0  0  0  0  0
   -1.0871    1.5130   -0.3763 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0
  2  3  1  0
  1  4  1  0
  1  5  1  0
  1  6  1  0
  2  7  1  0
  2  8  1  0
  3  9  1  0
M  END
"""

SDF_2D = """
     RDKit          2D

  8  8  0  0  0  0  0  0  0  0999 V2000
   -2.3221   -0.3572    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -1.8762    1.0750    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.4129    1.4050    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.6045    0.3028    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.1586   -1.1294    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -1.3047   -1.4594    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.0677    0.6327    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    3.0851   -0.4695    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  2  0
  2  3  1  0
  3  4  2  0
  4  5  1  0
  5  6  2  0
  4  7  1  0
  7  8  1  0
  6  1  1  0
M  END
"""


@pytest.fixture
def scratch():
    path = Path(tempfile.mkdtemp(prefix="wikimolgen-test-"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _gen(identifier: str, compound_name: str = "aspirin") -> MoleculeGenerator3D:
    gen = MoleculeGenerator3D(identifier)
    gen.compound_name = compound_name
    gen._fetched = True
    gen.mol = Chem.MolFromSmiles("C")
    return gen


class TestPubchemIdentifier:
    def test_cid_is_sent_as_cid_namespace(self):
        assert _gen("2244")._pubchem_identifier() == ("2244", "cid")

    def test_digits_with_whitespace_still_cid(self):
        assert _gen(" 2244 ")._pubchem_identifier() == ("2244", "cid")

    def test_name_uses_name_namespace(self):
        assert _gen("aspirin")._pubchem_identifier() == ("aspirin", "name")

    def test_custom_smiles_marker_skips_lookup(self):
        assert _gen("CCO", compound_name="custom_smiles")._pubchem_identifier() is None

    def test_unfetched_generator_skips_lookup(self):
        gen = MoleculeGenerator3D("aspirin")
        assert gen._fetched is False
        assert gen._pubchem_identifier() is None


class TestLoadPubchemConformer:
    def test_loads_3d_record(self):
        gen = _gen("2244")
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=SDF_3D):
            assert gen._load_pubchem_conformer() is True
        assert gen.mol.GetConformer().Is3D()
        assert gen.mol.GetNumAtoms() == 9

    def test_smiles_reflects_loaded_conformer(self):
        gen = _gen("2244")
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=SDF_3D):
            gen._load_pubchem_conformer()
        assert Chem.MolFromSmiles(gen.smiles) is not None

    def test_flat_record_rejected(self):
        gen = _gen("2244")
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=SDF_2D):
            assert gen._load_pubchem_conformer() is False

    def test_missing_record_falls_back(self):
        gen = _gen("2244")
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=None):
            assert gen._load_pubchem_conformer() is False
        assert Chem.MolToSmiles(gen.mol) == "C"

    def test_unparseable_record_falls_back(self):
        gen = _gen("2244")
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value="not a molblock"):
            assert gen._load_pubchem_conformer() is False

    def test_multi_conformer_request_falls_back_to_embedding(self):
        """One downloaded pose cannot serve a multi-conformer request.

        The Conformers control must still work, so asking for more than
        one pose routes to local ETKDG instead of silently returning one.
        """
        gen = _gen("2244")
        gen.config.conformer.num_conformers = 10
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf") as mock_sdf:
            assert gen._load_pubchem_conformer() is False
            mock_sdf.assert_not_called()

    def test_single_conformer_default_uses_download(self):
        gen = _gen("2244")
        assert gen.config.conformer.num_conformers == 1
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=SDF_3D):
            assert gen._load_pubchem_conformer() is True

    def test_config_toggle_disables_download(self):
        gen = _gen("2244")
        gen.config.conformer.use_pubchem_3d = False
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf") as mock_sdf:
            assert gen._load_pubchem_conformer() is False
            mock_sdf.assert_not_called()

    def test_name_namespace_used_for_named_compound(self):
        gen = _gen("aspirin")
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=SDF_3D) as mock_sdf:
            gen._load_pubchem_conformer()
            mock_sdf.assert_called_once_with("aspirin", namespace="name")


class TestGenerateSkipsEmbedding:
    def test_pubchem_hit_skips_embed_and_optimize(self, scratch):
        gen = _gen("2244")
        with patch(
            "wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=SDF_3D,
        ), patch.object(gen, "_embed_conformer") as mock_embed, patch.object(
            gen, "_optimize_geometry",
        ) as mock_opt, patch.object(
            gen, "_save_sdf", return_value=scratch / "aspirin.sdf",
        ):
            sdf_path, png_path = gen.generate(
                optimize=True, render=False, output_base=str(scratch / "aspirin"),
            )
        mock_embed.assert_not_called()
        mock_opt.assert_not_called()
        assert sdf_path.name == "aspirin.sdf"
        assert png_path is None

    def test_miss_embeds_and_optimizes(self, scratch):
        gen = _gen("2244")
        gen.mol = Chem.AddHs(Chem.MolFromSmiles("CCO"))
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=None), patch.object(
            gen, "_embed_conformer",
        ) as mock_embed, patch.object(gen, "_optimize_geometry") as mock_opt, patch.object(
            gen, "_save_sdf", return_value=scratch / "ethanol.sdf",
        ):
            gen.generate(optimize=True, render=False, output_base=str(scratch / "ethanol"))
        mock_embed.assert_called_once()
        mock_opt.assert_called_once()

    def test_miss_without_optimize_skips_force_field(self, scratch):
        gen = _gen("2244")
        gen.mol = Chem.AddHs(Chem.MolFromSmiles("CCO"))
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=None), patch.object(
            gen, "_optimize_geometry",
        ) as mock_opt, patch.object(
            gen, "_save_sdf", return_value=scratch / "ethanol.sdf",
        ):
            gen.generate(optimize=False, render=False, output_base=str(scratch / "ethanol"))
        mock_opt.assert_not_called()

    def test_pubchem_hit_reports_no_energy(self, scratch, caplog):
        """The downloaded conformer never runs the force field, so no
        energy exists; silently printing a stale one would be a lie."""
        gen = _gen("2244")
        with patch("wikimolgen.rendering.wikimol3d.fetch_3d_sdf", return_value=SDF_3D), patch.object(
            gen, "_save_sdf", return_value=scratch / "aspirin.sdf",
        ), caplog.at_level("INFO"):
            gen.generate(optimize=True, render=False, output_base=str(scratch / "aspirin"))
        assert "not computed" in caplog.text
        assert gen.energy is None
