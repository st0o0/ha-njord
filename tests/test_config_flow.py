"""Tests for njord config flow.

NOTE: These tests require homeassistant test infrastructure and cannot
run in a plain Docker container. They are structured for future use with
pytest-homeassistant-custom-component or HA's test harness.
"""

import pytest


@pytest.mark.skip(reason="Requires homeassistant test infrastructure")
async def test_config_flow_success():
    """Test successful config flow with valid njord connection."""


@pytest.mark.skip(reason="Requires homeassistant test infrastructure")
async def test_config_flow_cannot_connect():
    """Test config flow handles connection failure."""


@pytest.mark.skip(reason="Requires homeassistant test infrastructure")
async def test_config_flow_duplicate_abort():
    """Test config flow aborts on duplicate host:port."""
