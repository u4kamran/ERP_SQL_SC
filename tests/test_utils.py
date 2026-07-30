"""Utility function tests."""

from unittest.mock import MagicMock

from app.utils import get_client_ip, parse_user_agent


def test_parse_user_agent_chrome():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    result = parse_user_agent(ua)
    assert "Chrome" in result["browser"]
    assert result["os"]


def test_get_client_ip_direct():
    request = MagicMock()
    request.headers = {}
    request.client.host = "192.168.1.1"
    assert get_client_ip(request) == "192.168.1.1"


def test_get_client_ip_cloudflare():
    request = MagicMock()
    request.headers = {"CF-Connecting-IP": "203.0.113.50"}
    request.client.host = "10.0.0.1"
    assert get_client_ip(request) == "203.0.113.50"
