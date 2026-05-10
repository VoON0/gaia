# MIMO Agent Tools

"""
Tool system for MiMo Smart Agent.
Each tool provides a specific capability that the agent can use.
"""

import subprocess
import os
from typing import Any


class Tool:
    """Base class for agent tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool. Override in subclass."""
        raise NotImplementedError


class WebSearchTool(Tool):
    """Search the web for information."""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for current information. Parameters: query (str)"
        )
    
    def execute(self, query: str = "", **kwargs) -> str:
        """Execute a web search."""
        # Uses curl/requests to fetch search results
        try:
            import requests
            url = f"https://cn.bing.com/search?q={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            return f"Search results for '{query}': {resp.text[:2000]}"
        except Exception as e:
            return f"Search failed: {str(e)}"


class FileOpsTool(Tool):
    """Read, write, and list files in the workspace."""
    
    def __init__(self):
        super().__init__(
            name="file_ops",
            description="File operations: read, write, list. Parameters: action (str), path (str), content (str, optional)"
        )
    
    def execute(self, action: str = "list", path: str = ".", content: str = "", **kwargs) -> str:
        """Execute file operations."""
        try:
            if action == "list":
                files = os.listdir(path)
                return "\n".join(files[:50])  # Limit to 50 files
            
            elif action == "read":
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()[:5000]  # Limit to 5000 chars
            
            elif action == "write":
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Written {len(content)} bytes to {path}"
            
            return f"Unknown action: {action}"
        except Exception as e:
            return f"File operation failed: {str(e)}"


class CodeExecTool(Tool):
    """Execute Python or shell code in a sandboxed environment."""
    
    def __init__(self):
        super().__init__(
            name="code_exec",
            description="Execute Python code. Parameters: code (str), language (str)"
        )
    
    def execute(self, code: str = "", language: str = "python", **kwargs) -> str:
        """Execute code."""
        try:
            if language == "python":
                result = subprocess.run(
                    ["python3", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout or result.stderr
                return output[:3000]
            else:
                return f"Language '{language}' not supported yet"
        except subprocess.TimeoutExpired:
            return "Execution timed out"
        except Exception as e:
            return f"Execution failed: {str(e)}"


class GitOpsTool(Tool):
    """Git operations for repository management."""
    
    def __init__(self):
        super().__init__(
            name="git_ops",
            description="Git operations: status, diff, log. Parameters: action (str), args (str, optional)"
        )
    
    def execute(self, action: str = "status", args: str = "", **kwargs) -> str:
        """Execute git operations."""
        try:
            git_cmds = {
                "status": ["git", "status", "--short"],
                "diff": ["git", "diff"] + (args.split() if args else []),
                "log": ["git", "log", "--oneline", "-10"],
                "branch": ["git", "branch", "-a"],
                "commit": ["git", "commit", "-m", args or "Auto commit"],
            }
            
            cmd = git_cmds.get(action)
            if not cmd:
                return f"Unknown action: {action}. Available: {list(git_cmds.keys())}"
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout[:3000] or result.stderr[:3000]
        except Exception as e:
            return f"Git operation failed: {str(e)}"


# Tool registry
_TOOL_REGISTRY = {}

def register_tool(tool: Tool):
    """Register a tool in the global registry."""
    _TOOL_REGISTRY[tool.name] = tool

def get_tool(name: str) -> Tool | None:
    """Get a tool by name."""
    return _TOOL_REGISTRY.get(name)

def list_tools() -> list[str]:
    """List all registered tool names."""
    return list(_TOOL_REGISTRY.keys())

# Register built-in tools
register_tool(WebSearchTool())
register_tool(FileOpsTool())
register_tool(CodeExecTool())
register_tool(GitOpsTool())
