"""Tests for wikimolgen.sources.pubchem_sdf.fetch_3d_sdf."""

from unittest.mock import MagicMock, patch

import pytest

from wikimolgen.sources.pubchem_sdf import MAX_SDF_BYTES, fetch_3d_sdf

SDF_OK = """2244
  -OEChem-10252612403D

 21 21  0     0  0  0  0  0  0999 V2000
    1.2333   -0.5546    0.0186 C   0  0
M  END
$$$$
"""


class TestFetch3DSdf:
    def test_returns_sdf_for_200(self):
        with patch("wikimolgen.sources.pubchem_sdf.get_with_retry") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = SDF_OK
            assert fetch_3d_sdf(2244) == SDF_OK
            assert mock_get.call_count == 1

    def test_requests_3d_record_type(self):
        with patch("wikimolgen.sources.pubchem_sdf.get_with_retry") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = SDF_OK
            fetch_3d_sdf(2244)
            assert mock_get.call_args.kwargs["params"] == {"record_type": "3d"}

    def test_cid_goes_into_cid_namespace(self):
        with patch("wikimolgen.sources.pubchem_sdf.get_with_retry") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = SDF_OK
            fetch_3d_sdf(2244)
            assert "/compound/cid/2244/record/SDF" in mock_get.call_args.args[0]

    def test_name_goes_into_name_namespace_and_is_quoted(self):
        with patch("wikimolgen.sources.pubchem_sdf.get_with_retry") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = SDF_OK
            fetch_3d_sdf("4-MeO DiPT", namespace="name")
            assert "/compound/name/4-MeO%20DiPT/record/SDF" in mock_get.call_args.args[0]

    def test_404_returns_none(self):
        with patch("wikimolgen.sources.pubchem_sdf.get_with_retry") as mock_get:
            mock_get.return_value = MagicMock(status_code=404, text="")
            assert fetch_3d_sdf(999999999) is None

    def test_network_error_returns_none(self):
        with patch("wikimolgen.sources.pubchem_sdf.get_with_retry") as mock_get:
            mock_get.side_effect = OSError("network down")
            assert fetch_3d_sdf(2244) is None

    def test_non_sdf_body_returns_none(self):
        with patch("wikimolgen.sources.pubchem_sdf.get_with_retry") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, text="<html>oops</html>")
            assert fetch_3d_sdf(2244) is None

    def test_oversized_body_returns_none(self):
        with patch("wikimolgen.sources.pubchem_sdf.get_with_retry") as mock_get:
            body = "V2000" + "x" * MAX_SDF_BYTES
            mock_get.return_value = MagicMock(status_code=200, text=body)
            assert fetch_3d_sdf(2244) is None

    def test_v3000_accepted(self):
        with patch("wikimolgen.sources.pubchem_sdf.get_with_retry") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, text="x\n  y\n\n  0  0  0  0  0  0  0  0  0  0999 V3000\nM  END\n$$$$\n")
            assert fetch_3d_sdf(2244) is not None

    def test_unknown_namespace_raises(self):
        with pytest.raises(ValueError, match="namespace"):
            fetch_3d_sdf("x", namespace="smiles")
