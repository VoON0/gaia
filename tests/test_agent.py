"""Tests for MiMo Smart Agent."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mimo_agent.agent import MiMoAgent, Step, AgentResult
from mimo_agent.tools import get_tool, list_tools


class TestTools:
    """Test the tool system."""
    
    def test_list_tools(self):
        tools = list_tools()
        assert len(tools) > 0
        assert "web_search" in tools
        assert "file_ops" in tools
    
    def test_get_tool(self):
        tool = get_tool("web_search")
        assert tool is not None
        assert tool.name == "web_search"
    
    def test_get_nonexistent_tool(self):
        tool = get_tool("nonexistent_tool")
        assert tool is None


class TestAgent:
    """Test the agent class."""
    
    def test_agent_init(self):
        agent = MiMoAgent(api_key="test-key", model="MiMo-V2.5-Pro")
        assert agent.model == "MiMo-V2.5-Pro"
        assert len(agent.tools) == 3


class TestStep:
    """Test the Step dataclass."""
    
    def test_step_defaults(self):
        step = Step(id=1, action="test")
        assert step.id == 1
        assert step.action == "test"
        assert step.status == "pending"
        assert step.duration == 0.0
        assert step.tokens_used == 0


class TestAgentResult:
    """Test the AgentResult dataclass."""
    
    def test_result_defaults(self):
        result = AgentResult(
            task="test",
            steps=[],
            output="done",
            usage={},
            total_duration=1.0,
            success=True
        )
        assert result.task == "test"
        assert result.success is True
        assert result.output == "done"
