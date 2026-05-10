"""Tests for Tools."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mimo_agent.tools import FileOpsTool, CodeExecTool, GitOpsTool


class TestFileOpsTool:
    """Test file operations tool."""
    
    def test_list_current_dir(self):
        tool = FileOpsTool()
        result = tool.execute(action="list", path=".")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_unknown_action(self):
        tool = FileOpsTool()
        result = tool.execute(action="invalid")
        assert "Unknown" in result


class TestCodeExecTool:
    """Test code execution tool."""
    
    def test_unsupported_language(self):
        tool = CodeExecTool()
        result = tool.execute(code="test", language="rust")
        assert "not supported" in result
