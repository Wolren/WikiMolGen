"""Tests for wikimolgen.sources._client.get_with_retry."""

from unittest.mock import patch

import pytest
from requests import RequestException, Timeout

from wikimolgen.sources._client import get_with_retry


class TestGetWithRetry:
    def test_success_first_try(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            resp = get_with_retry("http://example.com", attempts=3)
            assert resp.status_code == 200
            assert mock_get.call_count == 1

    def test_retries_on_429_then_succeeds(self):
        with patch("requests.get") as mock_get, patch("time.sleep"):
            mock_get.side_effect = [
                _resp(429),
                _resp(429),
                _resp(200),
            ]
            resp = get_with_retry("http://example.com", attempts=3)
            assert resp.status_code == 200
            assert mock_get.call_count == 3

    def test_retries_on_500_then_succeeds(self):
        with patch("requests.get") as mock_get, patch("time.sleep"):
            mock_get.side_effect = [_resp(503), _resp(200)]
            resp = get_with_retry("http://example.com", attempts=3)
            assert resp.status_code == 200
            assert mock_get.call_count == 2

    def test_404_not_retried(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 404
            resp = get_with_retry("http://example.com", attempts=3)
            assert resp.status_code == 404
            assert mock_get.call_count == 1

    def test_retries_on_network_error_then_raises(self):
        with patch("requests.get") as mock_get, patch("time.sleep"):
            mock_get.side_effect = RequestException("Network is unreachable")
            with pytest.raises(RequestException, match="Network is unreachable"):
                get_with_retry("http://example.com", attempts=3)
            assert mock_get.call_count == 3

    def test_retries_on_timeout_then_raises(self):
        with patch("requests.get") as mock_get, patch("time.sleep"):
            mock_get.side_effect = Timeout("Connection timed out")
            with pytest.raises(Timeout, match="Connection timed out"):
                get_with_retry("http://example.com", attempts=2)
            assert mock_get.call_count == 2

    def test_exhausts_retries_on_persistent_429(self):
        with patch("requests.get") as mock_get, patch("time.sleep"):
            mock_get.return_value.status_code = 429
            resp = get_with_retry("http://example.com", attempts=3)
            assert resp.status_code == 429  # last response returned, caller raises
            assert mock_get.call_count == 3

    def test_parameters_forwarded(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            get_with_retry(
                "http://example.com/api",
                params={"q": "x"},
                headers={"User-Agent": "test"},
                timeout=7,
            )
            mock_get.assert_called_once_with(
                "http://example.com/api",
                params={"q": "x"},
                headers={"User-Agent": "test"},
                timeout=7,
            )


def _resp(status: int):
    m = type("R", (), {})()
    m.status_code = status
    return m
