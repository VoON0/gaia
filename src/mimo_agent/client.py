# MiMo Agent - MiMo API Client

import json
import time
from typing import Generator

import httpx


class MiMoClient:
    """Client for Xiaomi MiMo API."""

    def __init__(
        self,
        api_key: str,
        model: str = "MiMo-V2.5-Pro",
        base_url: str = "https://platform.xiaomimimo.com/api/v1",
        temperature: float = 0.7,
        max_tokens: int = 8192,
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def chat(self, messages: list[dict], **kwargs) -> dict:
        """Send a chat completion request."""
        return self._request("chat/completions", {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": False,
        })

    def chat_stream(self, messages: list[dict], **kwargs) -> Generator[dict, None, None]:
        """Stream a chat completion response."""
        response = self._request("chat/completions", {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": True,
        })
        
        # Handle SSE streaming
        for line in response.iter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    yield json.loads(data)
                except json.JSONDecodeError:
                    continue

    def embeddings(self, texts: list[str], **kwargs) -> list[list[float]]:
        """Generate embeddings for texts."""
        response = self._request("embeddings", {
            "model": kwargs.get("model", "MiMo-V2.5"),
            "input": texts,
        })
        return [item["embedding"] for item in response.get("data", [])]

    def agent_complete(self, task: str, tools: list[dict], **kwargs) -> dict:
        """Agent mode completion with tool definitions."""
        return self._request("agent/completions", {
            "model": kwargs.get("model", self.model),
            "task": task,
            "tools": tools,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        })

    def _request(self, endpoint: str, payload: dict) -> dict:
        """Make an API request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        response = self._client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        if payload.get("stream"):
            return response  # Return raw response for streaming
        
        result = response.json()
        
        # Normalize response format
        if "choices" in result:
            choice = result["choices"][0]
            return {
                "content": choice.get("message", {}).get("content", ""),
                "usage": result.get("usage", {}),
                "model": result.get("model", self.model),
            }
        
        return result

    def close(self):
        """Close the HTTP client."""
        self._client.close()
