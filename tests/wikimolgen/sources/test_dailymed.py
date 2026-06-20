"""Tests for wikimolgen/sources/dailymed.py — mocked DailyMed API."""

from unittest.mock import patch

import pytest

from wikimolgen.sources.dailymed import fetch_dailymed_id


class TestFetchDailymedId:
    def test_successful_lookup(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "data": [{"setid": "85c02768-7b96-4c48-8e67-6716fccd46fe"}]
            }
            result = fetch_dailymed_id("R16CO5Y76E")
            assert result == "85c02768-7b96-4c48-8e67-6716fccd46fe"

    def test_no_match(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"data": []}
            result = fetch_dailymed_id("NONEXISTENT")
            assert result is None

    def test_empty_response(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}
            result = fetch_dailymed_id("R16CO5Y76E")
            assert result is None

    def test_network_error(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("DailyMed API error")
            with pytest.raises(Exception, match="DailyMed API error"):
                fetch_dailymed_id("R16CO5Y76E")
