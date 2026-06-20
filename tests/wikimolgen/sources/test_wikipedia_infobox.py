"""Tests for wikimolgen/sources/wikipedia_infobox.py — mocked MediaWiki API."""

from unittest.mock import patch

import pytest

from wikimolgen.sources.wikipedia_infobox import fetch_infobox


_ASPIRIN_WIKITEXT = """{{Infobox drug
| image = Aspirin structure.png
| width = 200px
| ATC_prefix = N02
| ATC_suffix = BA01
| legal_status = Generally recognized as safe (GRAS)
| legal_US = OTC
| legal_UK = P
| pregnancy_category = C
| routes_of_administration = Oral, rectal, intravenous
| class = NSAID
| bioavailability = 80-100%
| metabolism = Hepatic
| elimination_half-life = 2-3 hours
}}"""

_CHEMICAL_WIKITEXT = """{{Infobox chemical
| IUPACName = Sodium chloride
| OtherNames = Table salt
}}"""


class TestFetchInfobox:
    def test_drug_infobox_success(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "parse": {"wikitext": {"*": _ASPIRIN_WIKITEXT}}
            }
            result = fetch_infobox("Aspirin")
            assert result["atc_prefix"] == "N02"
            assert result["atc_suffix"] == "BA01"
            assert result["legal_status"] == "Generally recognized as safe (GRAS)"
            assert result["legal_us"] == "OTC"
            assert result["legal_uk"] == "P"
            assert result["pregnancy_category"] == "C"
            assert result["routes_of_administration"] == "Oral, rectal, intravenous"
            assert result["drug_class"] == "NSAID"
            assert result["bioavailability"] == "80-100%"
            assert result["metabolism"] == "Hepatic"
            assert result["elimination_half_life"] == "2-3 hours"

    def test_chemical_infobox_returns_no_pharma_fields(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "parse": {"wikitext": {"*": _CHEMICAL_WIKITEXT}}
            }
            result = fetch_infobox("Sodium chloride")
            assert result == {}

    def test_no_infobox_found(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "parse": {"wikitext": {"*": "Some text without an infobox"}}
            }
            result = fetch_infobox("Nonexistent")
            assert result == {}

    def test_no_wikitext_returned(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"parse": {}}
            result = fetch_infobox("Missing")
            assert result == {}

    def test_api_error(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Wikipedia API error")
            with pytest.raises(Exception, match="Wikipedia API error"):
                fetch_infobox("Aspirin")

    def test_missing_page(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}
            result = fetch_infobox("NoPageHere")
            assert result == {}

    def test_partial_data(self):
        partial = "{{Infobox drug\n| ATC_prefix = N02\n| class = NSAID\n}}"
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"parse": {"wikitext": {"*": partial}}}
            result = fetch_infobox("PartialDrug")
            assert result["atc_prefix"] == "N02"
            assert result["drug_class"] == "NSAID"
            assert "legal_status" not in result
