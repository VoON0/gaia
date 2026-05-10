"""
MiMo Smart Agent - Core Agent Engine

A powerful agent framework powered by Xiaomi MiMo-V2.5-Pro,
featuring intelligent task planning, tool calling, and memory management.
"""

import json
import logging
import time
from typing import Any, Generator
from dataclasses import dataclass, field

from .client import MiMoClient
from .tools import get_tool, list_tools

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """A single step in the agent's execution plan."""
    id: int
    action: str
    tool: str | None = None
    input: dict | None = None
    output: Any = None
    status: str = "pending"  # pending | running | completed | failed
    duration: float = 0.0
    tokens_used: int = 0


@dataclass
class AgentResult:
    """Result of an agent execution."""
    task: str
    steps: list[Step]
    output: Any
    usage: dict
    total_duration: float
    success: bool
    error: str | None = None


class MiMoAgent:
    """Core agent that uses MiMo-V2.5-Pro for intelligent task execution."""

    def __init__(
        self,
        api_key: str,
        model: str = "MiMo-V2.5-Pro",
        tools: list[str] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        max_steps: int = 20,
    ):
        self.client = MiMoClient(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.model = model
        self.max_steps = max_steps
        self.tools = tools or ["web_search", "file_ops", "code_exec"]
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt with tool definitions."""
        tool_descriptions = []
        for name in self.tools:
            tool = get_tool(name)
            if tool:
                tool_descriptions.append(f"  - {tool.name}: {tool.description}")
        
        tools_str = "\n".join(tool_descriptions)

        return f"""You are MiMo Smart Agent, powered by Xiaomi MiMo-V2.5-Pro.

You are an intelligent agent that can plan and execute complex tasks.
You have access to the following tools:

{tools_str}

For each task:
1. Analyze the request and break it into steps
2. For each step, decide if you need a tool
3. Execute tools one at a time
4. Use previous outputs to inform subsequent steps
5. Provide a final comprehensive answer

Format your responses clearly and include all relevant details.
When using tools, specify the exact tool name and parameters.
"""

    def run(self, task: str, context: dict | None = None) -> AgentResult:
        """Execute a task with the agent."""
        start_time = time.time()
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if context:
            messages.append({"role": "system", "content": f"Context: {json.dumps(context)}"})
        
        messages.append({"role": "user", "content": task})
        
        steps = []
        all_tokens = 0
        
        for step_num in range(self.max_steps):
            step_start = time.time()
            step = Step(id=step_num + 1, action="thinking")
            
            try:
                response = self.client.chat(messages)
                content = response.get("content", "")
                usage = response.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                all_tokens += tokens
                
                step.status = "completed"
                step.output = content
                step.tokens_used = tokens
                step.duration = time.time() - step_start
                
                # Check if there's a tool call in the response
                tool_call = self._parse_tool_call(content)
                if tool_call and step_num < self.max_steps - 1:
                    step.tool = tool_call["name"]
                    step.action = f"calling tool: {tool_call['name']}"
                    
                    # Execute the tool
                    tool = get_tool(tool_call["name"])
                    if tool:
                        try:
                            tool_result = tool.execute(**tool_call["params"])
                            messages.append({"role": "assistant", "content": content})
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.get("id", ""),
                                "content": str(tool_result)
                            })
                        except Exception as e:
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.get("id", ""),
                                "content": f"Error executing tool: {str(e)}"
                            })
                else:
                    # Final response - no more tool calls
                    step.status = "completed"
                    steps.append(step)
                    break
                    
            except Exception as e:
                step.status = "failed"
                step.output = str(e)
                step.duration = time.time() - step_start
                steps.append(step)
                return AgentResult(
                    task=task,
                    steps=steps,
                    output=None,
                    usage={"total_tokens": all_tokens},
                    total_duration=time.time() - start_time,
                    success=False,
                    error=str(e)
                )
            
            steps.append(step)

        # Get final output
        final_output = steps[-1].output if steps else ""
        
        return AgentResult(
            task=task,
            steps=steps,
            output=final_output,
            usage={"total_tokens": all_tokens},
            total_duration=time.time() - start_time,
            success=True
        )

    def run_stream(self, task: str) -> Generator[str, None, AgentResult]:
        """Execute a task with streaming output (NOT IMPLEMENTED YET)."""
        raise NotImplementedError("Streaming execution coming soon!")

    def plan(self, task: str) -> list[Step]:
        """Generate a task plan without executing it."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": "You are in planning mode. Do NOT execute any tools. Instead, output a numbered plan of steps."},
            {"role": "user", "content": f"Create a detailed execution plan for: {task}"}
        ]
        
        response = self.client.chat(messages)
        content = response.get("content", "")
        
        # Parse the plan into steps
        lines = content.strip().split("\n")
        steps = []
        for i, line in enumerate(lines):
            if line.strip():
                steps.append(Step(
                    id=i + 1,
                    action=line.strip(),
                    status="planned"
                ))
        
        return steps

    def _parse_tool_call(self, content: str) -> dict | None:
        """Parse tool call from agent response."""
        # Try to find tool call in structured format
        # Format: TOOL_CALL: tool_name | param1=value1 | param2=value2
        if content.startswith("TOOL_CALL:"):
            parts = content.replace("TOOL_CALL:", "").strip().split("|")
            name = parts[0].strip()
            params = {}
            for p in parts[1:]:
                if "=" in p:
                    key, value = p.split("=", 1)
                    params[key.strip()] = value.strip()
            return {"name": name, "params": params, "id": f"call_{int(time.time())}"}
        return None
