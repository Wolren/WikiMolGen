"""Tests for wikimolgen/sources/pubchem_substance.py — mocked PubChem API."""

from unittest.mock import patch

import pytest

from wikimolgen.sources.pubchem_substance import fetch_substances


class TestFetchSubstances:
    def test_successful_fetch(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "IdentifierList": {"CID": [2244], "SID": [135398660, 153484647]}
            }
            result = fetch_substances(2244)
            assert result["pubchem_substance"] == "135398660"
            assert result["pubchem_substances"] == ["135398660", "153484647"]

    def test_no_sids(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"IdentifierList": {"CID": [2244], "SID": []}}
            result = fetch_substances(2244)
            assert result == {}

    def test_no_identifier_list(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}
            result = fetch_substances(2244)
            assert result == {}

    def test_network_error(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("PubChem API error")
            with pytest.raises(Exception, match="PubChem API error"):
                fetch_substances(2244)

    def test_string_cid(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "IdentifierList": {"CID": [2244], "SID": [135398660]}
            }
            result = fetch_substances("2244")
            assert result["pubchem_substance"] == "135398660"
