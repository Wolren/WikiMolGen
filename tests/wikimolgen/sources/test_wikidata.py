"""Tests for wikimolgen/sources/wikidata.py — mocked SPARQL."""

from unittest.mock import patch

import pytest
from wikimolgen.sources.wikidata import query_wikidata


class TestQueryWikidata:
    def test_successful_query(self):
        mock_response = {
            "results": {
                "bindings": [
                    {
                        "qid": {"value": "Q27108473"},
                        "wikipedia": {"value": "https://en.wikipedia.org/wiki/Aspirin"},
                        "chembl_id": {"value": "CHEMBL123"},
                        "drugbank_id": {"value": "DB00945"},
                        "cas_number": {"value": "50-78-2"},
                        "chemspider_id": {"value": "2157"},
                        "unii": {"value": "R16CO5Y76E"},
                        "medlineplus": {"value": "a682875"},
                        "iuphar_ligand": {"value": "4139"},
                        "pdb_ligand": {"value": "AIN"},
                        "niaid_chemdb": {"value": "000001"},
                        "inn": {"value": "Aspirin"},
                    }
                ]
            }
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            result = query_wikidata(2244)
            assert result["wikidata_qid"] == "Q27108473"
            assert result["wikipedia_title"] == "Aspirin"
            assert result["chembl_id"] == "CHEMBL123"
            assert result["drugbank_id"] == "DB00945"
            assert result["cas_number"] == "50-78-2"
            assert result["chemspider_id"] == "2157"
            assert result["unii"] == "R16CO5Y76E"
            assert result["medlineplus"] == "a682875"
            assert result["iuphar_ligand"] == "4139"
            assert result["pdb_ligand"] == "AIN"
            assert result["niaid_chemdb"] == "000001"
            assert result["inn"] == "Aspirin"

    def test_no_results(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"results": {"bindings": []}}
            assert query_wikidata(999999) == {}

    def test_partial_results(self):
        mock_response = {
            "results": {
                "bindings": [
                    {
                        "qid": {"value": "Q42"},
                        "wikipedia": {"value": "https://en.wikipedia.org/wiki/Test"},
                    }
                ]
            }
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            result = query_wikidata(42)
            assert result["wikidata_qid"] == "Q42"
            assert result["wikipedia_title"] == "Test"
            assert "chembl_id" not in result

    def test_network_error(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("SPARQL failed")
            with pytest.raises(Exception, match="SPARQL failed"):
                query_wikidata(2244)

    def test_string_cid(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "results": {"bindings": [{"qid": {"value": "Q1"}}]}
            }
            assert query_wikidata("2244")["wikidata_qid"] == "Q1"
