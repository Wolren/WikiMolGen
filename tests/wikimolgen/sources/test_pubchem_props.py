"""Tests for wikimolgen/sources/pubchem_props.py — mocked HTTP."""

from unittest.mock import patch

import pytest
from requests import RequestException, Timeout

from wikimolgen.sources.pubchem_props import fetch_properties


class TestFetchProperties:
    MOCK_FULL = {
        "PropertyTable": {
            "Properties": [
                {
                    "MolecularWeight": 180.16,
                    "XLogP": 1.0,
                    "ExactMass": 180.042,
                    "MonoisotopicMass": 180.042,
                    "TPSA": 63.6,
                    "Complexity": 269,
                    "Charge": 0,
                    "HBondDonorCount": 1,
                    "HBondAcceptorCount": 4,
                    "RotatableBondCount": 2,
                    "HeavyAtomCount": 13,
                }
            ]
        }
    }

    def test_successful_fetch(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = self.MOCK_FULL
            result = fetch_properties(2244)
            assert result["molecular_weight"] == 180.16
            assert result["xlogp"] == 1.0
            assert result["exact_mass"] == 180.042
            assert result["tpsa"] == 63.6
            assert result["h_bond_donors"] == 1
            assert result["h_bond_acceptors"] == 4
            assert result["rotatable_bonds"] == 2
            assert result["charge"] == 0
            assert result["complexity"] == 269
            assert result["monoisotopic_mass"] == 180.042
            assert result["heavy_atoms"] == 13

    def test_empty_properties(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"PropertyTable": {"Properties": []}}
            assert fetch_properties(999999) == {}

    def test_no_property_table(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}
            assert fetch_properties(999999) == {}

    def test_partial_nulls_skipped(self):
        mock_response = {
            "PropertyTable": {
                "Properties": [
                    {
                        "MolecularWeight": 180.16,
                        "XLogP": None,
                        "ExactMass": None,
                        "HBondDonorCount": 1,
                    }
                ]
            }
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            result = fetch_properties(2244)
            assert result["molecular_weight"] == 180.16
            assert result["h_bond_donors"] == 1
            assert "xlogp" not in result

    def test_empty_string_skipped(self):
        mock_response = {
            "PropertyTable": {"Properties": [{"MolecularWeight": 180.16, "XLogP": ""}]}
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            result = fetch_properties(2244)
            assert result["molecular_weight"] == 180.16
            assert "xlogp" not in result

    def test_http_404(self):
        with patch("requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 404
            resp.raise_for_status.side_effect = RequestException("404 Not Found")
            with pytest.raises(RequestException, match="404 Not Found"):
                fetch_properties(999999)

    def test_http_429(self):
        with patch("requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 429
            resp.raise_for_status.side_effect = RequestException("429 Too Many Requests")
            with pytest.raises(RequestException, match="429 Too Many Requests"):
                fetch_properties(2244)

    def test_timeout(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Timeout("Connection timed out")
            with pytest.raises(Timeout, match="Connection timed out"):
                fetch_properties(2244, timeout=1)

    def test_network_error(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = RequestException("Network is unreachable")
            with pytest.raises(RequestException, match="Network is unreachable"):
                fetch_properties(2244)

    def test_invalid_json(self):
        with patch("requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 200
            resp.json.side_effect = ValueError("Invalid JSON")
            with pytest.raises(ValueError, match="Invalid JSON"):
                fetch_properties(2244)

    def test_string_cid(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = self.MOCK_FULL
            result = fetch_properties("2244")
            assert result["molecular_weight"] == 180.16

    def test_user_agent_header(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = self.MOCK_FULL
            fetch_properties(2244)
            call_kwargs = mock_get.call_args[1]
            assert "User-Agent" in call_kwargs.get("headers", {})
            assert "WikiMolGen" in call_kwargs["headers"]["User-Agent"]
