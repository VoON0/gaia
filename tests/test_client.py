"""Tests for MiMo API Client."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mimo_agent.client import MiMoClient


class TestMiMoClient:
    """Test the MiMo client initialization."""
    
    def test_client_init(self):
        client = MiMoClient(api_key="test-key")
        assert client.model == "MiMo-V2.5-Pro"
        assert client.temperature == 0.7
        assert client.base_url == "https://platform.xiaomimimo.com/api/v1"
    
    def test_client_custom_values(self):
        client = MiMoClient(
            api_key="custom-key",
            model="MiMo-V2.5",
            temperature=0.3,
            max_tokens=4096,
        )
        assert client.api_key == "custom-key"
        assert client.model == "MiMo-V2.5"
        assert client.temperature == 0.3
        assert client.max_tokens == 4096
