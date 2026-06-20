"""Extended error-handling tests for wikidata.py — HTTP 4xx, 5xx, 429, timeout, etc."""

from unittest.mock import patch

import pytest
from requests import RequestException, Timeout

from wikimolgen.sources.wikidata import SPARQL_ENDPOINT, query_wikidata

MOCK_OK = {
    "results": {
        "bindings": [
            {
                "qid": {"value": "Q27108473"},
                "wikipedia": {"value": "https://en.wikipedia.org/wiki/Aspirin"},
            }
        ]
    }
}


class TestQueryWikidataExtended:
    def test_http_404(self):
        with patch("requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 404
            resp.raise_for_status.side_effect = RequestException("404 Not Found")
            with pytest.raises(RequestException, match="404 Not Found"):
                query_wikidata(999999)

    def test_http_429(self):
        with patch("requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 429
            resp.raise_for_status.side_effect = RequestException("429 Too Many Requests")
            with pytest.raises(RequestException, match="429 Too Many Requests"):
                query_wikidata(2244)

    def test_http_500(self):
        with patch("requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 500
            resp.raise_for_status.side_effect = RequestException("500 Server Error")
            with pytest.raises(RequestException, match="500 Server Error"):
                query_wikidata(2244)

    def test_timeout(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Timeout("SPARQL query timed out")
            with pytest.raises(Timeout, match="SPARQL query timed out"):
                query_wikidata(2244, timeout=1)

    def test_network_error(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = RequestException("DNS resolution failed")
            with pytest.raises(RequestException, match="DNS resolution failed"):
                query_wikidata(2244)

    def test_invalid_json(self):
        with patch("requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 200
            resp.json.side_effect = ValueError("Invalid JSON from SPARQL endpoint")
            with pytest.raises(ValueError, match="Invalid JSON from SPARQL endpoint"):
                query_wikidata(2244)

    def test_malformed_response_no_results_key(self):
        with patch("requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 200
            resp.json.return_value = {"wrong_key": {}}
            assert query_wikidata(2244) == {}

    def test_malformed_binding_missing_value(self):
        with patch("requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 200
            resp.json.return_value = {"results": {"bindings": [{"qid": {"no_value": "Q42"}}]}}
            assert query_wikidata(42) == {}

    def test_wikipedia_url_parsing(self):
        urls = [
            ("https://en.wikipedia.org/wiki/Aspirin", "Aspirin"),
            ("https://en.wikipedia.org/wiki/Caffeine", "Caffeine"),
            ("https://en.wikipedia.org/wiki/Ibuprofen", "Ibuprofen"),
        ]
        for url, expected in urls:
            with patch("requests.get") as mock_get:
                resp = mock_get.return_value
                resp.status_code = 200
                resp.json.return_value = {
                    "results": {
                        "bindings": [{"qid": {"value": "Q42"}, "wikipedia": {"value": url}}]
                    }
                }
                result = query_wikidata(42)
                assert result["wikipedia_title"] == expected

    def test_bad_cid_negative(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = ValueError("invalid literal for int()")
            with pytest.raises(ValueError):
                query_wikidata(-1)

    def test_user_agent_header(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_OK
            query_wikidata(2244)
            call_kwargs = mock_get.call_args[1]
            assert "User-Agent" in call_kwargs.get("headers", {})
            assert "WikiMolGen" in call_kwargs["headers"]["User-Agent"]

    def test_uses_sparql_endpoint(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_OK
            query_wikidata(2244)
            url = mock_get.call_args[0][0]
            assert url == SPARQL_ENDPOINT
