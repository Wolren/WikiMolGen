"""Tests for wikimolgen/core.py — mocked PubChemPy and source modules."""

from unittest.mock import MagicMock, patch

import pytest

from wikimolgen.core import (
    CompoundFetchError,
    SMILESValidationError,
    _parse_element_counts,
    enrich_compound_data,
    fetch_compound,
    validate_smiles,
)


class TestParseElementCounts:
    def test_simple_formula(self):
        assert _parse_element_counts("C9H8O4") == {"c_count": 9, "h_count": 8, "o_count": 4}

    def test_single_atom(self):
        assert _parse_element_counts("C") == {"c_count": 1}

    def test_with_nitrogen(self):
        assert _parse_element_counts("C8H10N4O2") == {
            "c_count": 8,
            "h_count": 10,
            "n_count": 4,
            "o_count": 2,
        }

    def test_empty_formula(self):
        assert _parse_element_counts("") == {}

    def test_formula_with_period(self):
        assert _parse_element_counts("C2H6O") == {"c_count": 2, "h_count": 6, "o_count": 1}

    def test_halogens(self):
        assert _parse_element_counts("CCl4") == {"c_count": 1, "cl_count": 4}


class TestEnrichCompoundData:
    def test_none_input(self):
        assert enrich_compound_data(None) is None

    def test_empty_dict(self):
        assert enrich_compound_data({}) == {}

    def test_no_cid_key(self):
        assert enrich_compound_data({"name": "aspirin"}) == {"name": "aspirin"}

    @patch("wikimolgen.core.fetch_substances", return_value={"pubchem_substance": "135398660"})
    @patch("wikimolgen.core.fetch_dailymed_id", return_value="some-uuid")
    @patch("wikimolgen.core.fetch_infobox", return_value={"atc_prefix": "N02"})
    @patch("wikimolgen.core.fetch_experimental_data", return_value={"melting_point": "135 °C"})
    @patch(
        "wikimolgen.core.query_wikidata",
        return_value={"wikidata_qid": "Q42", "wikipedia_title": "Aspirin", "unii": "R16CO5Y76E"},
    )
    @patch("wikimolgen.core.fetch_properties", return_value={"logp": 1.1})
    def test_all_sources_succeed(
        self, mock_props, mock_wd, mock_exp, mock_infobox, mock_dm, mock_sub
    ):
        data = {"cid": 2244, "name": "aspirin", "molecular_formula": "C9H8O4"}
        result = enrich_compound_data(data)
        assert result["cid"] == 2244
        assert result["name"] == "aspirin"
        assert result["wikidata_qid"] == "Q42"
        assert result["logp"] == 1.1
        assert result["melting_point"] == "135 °C"
        assert result["atc_prefix"] == "N02"
        assert result["c_count"] == 9
        assert result["h_count"] == 8
        assert result["o_count"] == 4
        assert result["dailymed_id"] == "some-uuid"
        assert result["pubchem_substance"] == "135398660"

    @patch("wikimolgen.core.fetch_substances", return_value={})
    @patch("wikimolgen.core.fetch_dailymed_id", return_value=None)
    @patch("wikimolgen.core.fetch_infobox", return_value={})
    @patch("wikimolgen.core.fetch_experimental_data", side_effect=Exception("Experimental down"))
    @patch("wikimolgen.core.query_wikidata", return_value={"wikidata_qid": "Q42"})
    @patch("wikimolgen.core.fetch_properties", side_effect=Exception("PubChem down"))
    def test_partial_failures_graceful(
        self, mock_props, mock_wd, mock_exp, mock_infobox, mock_dm, mock_sub
    ):
        data = {"cid": 2244}
        result = enrich_compound_data(data)
        assert result["cid"] == 2244
        assert result["wikidata_qid"] == "Q42"
        assert "logp" not in result
        assert "melting_point" not in result

    @patch("wikimolgen.core.fetch_substances", return_value={})
    @patch("wikimolgen.core.fetch_dailymed_id", return_value=None)
    @patch("wikimolgen.core.fetch_infobox", return_value={})
    @patch("wikimolgen.core.fetch_experimental_data", side_effect=Exception("Error"))
    @patch("wikimolgen.core.query_wikidata", side_effect=Exception("Error"))
    @patch("wikimolgen.core.fetch_properties", side_effect=Exception("Error"))
    def test_all_sources_fail(self, mock_props, mock_wd, mock_exp, mock_infobox, mock_dm, mock_sub):
        data = {"cid": 2244, "name": "test"}
        result = enrich_compound_data(data)
        assert result == {"cid": 2244, "name": "test"}


class TestEnrichPriority:
    """Priority: base > props > experimental > wikidata > substances > infobox"""

    @patch("wikimolgen.core.fetch_substances", return_value={})
    @patch("wikimolgen.core.fetch_dailymed_id", return_value=None)
    @patch("wikimolgen.core.fetch_infobox", return_value={"medlineplus": "infobox_val"})
    @patch("wikimolgen.core.fetch_experimental_data", return_value={})
    @patch("wikimolgen.core.query_wikidata", return_value={"medlineplus": "wd_val"})
    @patch("wikimolgen.core.fetch_properties", return_value={})
    def test_wikidata_overrides_infobox(
        self, mock_props, mock_wd, mock_exp, mock_infobox, mock_dm, mock_sub
    ):
        """Wikidata wins over Wikipedia infobox for overlapping keys."""
        result = enrich_compound_data({"cid": 2244, "molecular_formula": "C9H8O4"})
        assert result["medlineplus"] == "wd_val"

    @patch("wikimolgen.core.fetch_substances", return_value={})
    @patch("wikimolgen.core.fetch_dailymed_id", return_value=None)
    @patch(
        "wikimolgen.core.fetch_infobox",
        return_value={
            "medlineplus": "infobox_val",
            "iuphar_ligand": "infobox_iuphar",
            "pdb_ligand": "infobox_pdb",
            "niaid_chemdb": "infobox_niaid",
        },
    )
    @patch("wikimolgen.core.fetch_experimental_data", return_value={})
    @patch(
        "wikimolgen.core.query_wikidata",
        return_value={
            "medlineplus": "wd_val",
            "iuphar_ligand": "wd_iuphar",
            "pdb_ligand": "wd_pdb",
            "niaid_chemdb": "wd_niaid",
            "wikipedia_title": "Aspirin",
        },
    )
    @patch("wikimolgen.core.fetch_properties", return_value={})
    def test_wikidata_wins_all_overlaps(
        self, mock_props, mock_wd, mock_exp, mock_infobox, mock_dm, mock_sub
    ):
        """All Wikidata overlapping keys beat infobox."""
        result = enrich_compound_data({"cid": 2244, "molecular_formula": "C9H8O4"})
        assert result["medlineplus"] == "wd_val"
        assert result["iuphar_ligand"] == "wd_iuphar"
        assert result["pdb_ligand"] == "wd_pdb"
        assert result["niaid_chemdb"] == "wd_niaid"

    @patch("wikimolgen.core.fetch_substances", return_value={"pubchem_substance": "substances_val"})
    @patch("wikimolgen.core.fetch_dailymed_id", return_value=None)
    @patch(
        "wikimolgen.core.fetch_infobox",
        return_value={
            "pubchem_substance": "infobox_val",
            "iuphar_ligand": "infobox_val",
            "wikipedia_title": "Aspirin",
        },
    )
    @patch("wikimolgen.core.fetch_experimental_data", return_value={})
    @patch(
        "wikimolgen.core.query_wikidata",
        return_value={
            "iuphar_ligand": "wd_val",
            "wikipedia_title": "Aspirin",
        },
    )
    @patch("wikimolgen.core.fetch_properties", return_value={})
    def test_substances_overrides_infobox(
        self, mock_props, mock_wd, mock_exp, mock_infobox, mock_dm, mock_sub
    ):
        """PubChem Substances beats infobox; infobox fills only missing."""
        result = enrich_compound_data({"cid": 2244})
        assert result["pubchem_substance"] == "substances_val"

    @patch("wikimolgen.core.fetch_substances", return_value={})
    @patch("wikimolgen.core.fetch_dailymed_id", return_value=None)
    @patch("wikimolgen.core.fetch_infobox", return_value={"drugs_com": "aspirin"})
    @patch("wikimolgen.core.fetch_experimental_data", return_value={})
    @patch("wikimolgen.core.query_wikidata", return_value={"wikipedia_title": "Aspirin"})
    @patch("wikimolgen.core.fetch_properties", return_value={})
    def test_infobox_fills_missing_keys(
        self, mock_props, mock_wd, mock_exp, mock_infobox, mock_dm, mock_sub
    ):
        """Infobox-only keys (drugs_com) appear when no other source has them."""
        result = enrich_compound_data({"cid": 2244})
        assert result["drugs_com"] == "aspirin"

    @patch("wikimolgen.core.fetch_substances", return_value={})
    @patch("wikimolgen.core.fetch_dailymed_id", return_value=None)
    @patch("wikimolgen.core.fetch_infobox", return_value={"medlineplus": "infobox_med"})
    @patch("wikimolgen.core.fetch_experimental_data", return_value={})
    @patch("wikimolgen.core.query_wikidata", return_value={"wikipedia_title": "Aspirin"})
    @patch("wikimolgen.core.fetch_properties", return_value={"molecular_weight": 999.99})
    def test_base_data_overrides_props(
        self, mock_props, mock_wd, mock_exp, mock_infobox, mock_dm, mock_sub
    ):
        """Base PubChemPy molecular_weight beats Properties."""
        result = enrich_compound_data({"cid": 2244, "molecular_weight": 180.16})
        assert result["molecular_weight"] == 180.16

    @patch("wikimolgen.core.fetch_substances", return_value={})
    @patch("wikimolgen.core.fetch_dailymed_id", return_value=None)
    @patch("wikimolgen.core.fetch_infobox", return_value={"medlineplus": "infobox_med"})
    @patch("wikimolgen.core.fetch_experimental_data", return_value={})
    @patch("wikimolgen.core.query_wikidata", return_value={"wikipedia_title": "Aspirin"})
    @patch("wikimolgen.core.fetch_properties", return_value={})
    def test_infobox_never_overwrites_existing_keys(
        self, mock_props, mock_wd, mock_exp, mock_infobox, mock_dm, mock_sub
    ):
        """Infobox does not clobber keys already set by any higher-priority source."""
        result = enrich_compound_data({"cid": 2244, "medlineplus": "base_val"})
        assert result["medlineplus"] == "base_val"


class TestFetchCompound:
    @patch("pubchempy.Compound.from_cid")
    def test_cid_returns_smiles_and_name(self, mock_from_cid):
        mock_compound = MagicMock()
        mock_compound.smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
        mock_compound.canonical_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
        mock_compound.iupac_name = "Aspirin"
        mock_from_cid.return_value = mock_compound

        smiles, name = fetch_compound("2244")
        assert smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
        assert name == "Aspirin"

    @patch("pubchempy.Compound.from_cid")
    def test_cid_fallback_to_canonical_smiles(self, mock_from_cid):
        mock_compound = MagicMock()
        mock_compound.smiles = None
        mock_compound.canonical_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
        mock_compound.iupac_name = "Aspirin"
        mock_from_cid.return_value = mock_compound

        smiles, name = fetch_compound("2244")
        assert smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"

    @patch("pubchempy.Compound.from_cid")
    def test_cid_without_iupac_name(self, mock_from_cid):
        mock_compound = MagicMock()
        mock_compound.smiles = "CC(=O)O"
        mock_compound.iupac_name = None
        mock_from_cid.return_value = mock_compound

        _, name = fetch_compound("2244")
        assert name == "CID_2244"

    @patch("pubchempy.Compound.from_cid")
    def test_cid_fetch_failure(self, mock_from_cid):
        mock_from_cid.side_effect = Exception("PubChem API error")
        with pytest.raises(CompoundFetchError, match="Failed to fetch PubChem CID 2244"):
            fetch_compound("2244")

    @patch("pubchempy.get_compounds")
    def test_name_lookup_success(self, mock_get_compounds):
        mock_compound = MagicMock()
        mock_compound.smiles = "C8H10N4O2"
        mock_compound.canonical_smiles = "C8H10N4O2"
        mock_compound.iupac_name = "Caffeine"
        mock_get_compounds.return_value = [mock_compound]

        smiles, name = fetch_compound("caffeine")
        assert name == "Caffeine"

    @patch("pubchempy.get_compounds")
    def test_name_lookup_empty_then_smiles(self, mock_get_compounds):
        mock_get_compounds.return_value = []

        with patch("rdkit.Chem.MolFromSmiles", return_value=MagicMock()):
            smiles, name = fetch_compound("CCO")
            assert smiles == "CCO"
            assert name == "custom_smiles"

    @patch("pubchempy.get_compounds")
    def test_name_lookup_failure_then_smiles_failure(self, mock_get_compounds):
        mock_get_compounds.return_value = []

        with patch("rdkit.Chem.MolFromSmiles", return_value=None):
            with pytest.raises(
                CompoundFetchError,
                match="Could not interpret 'xyzzy' as PubChem CID, compound name, or valid SMILES",
            ):
                fetch_compound("xyzzy")


class TestValidateSmiles:
    def test_valid_smiles(self):
        mol = validate_smiles("CCO")
        assert mol is not None

    def test_invalid_smiles(self):
        with pytest.raises(SMILESValidationError, match="Invalid SMILES"):
            validate_smiles("not_a_smiles")
