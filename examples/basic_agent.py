"""
Basic MiMo Agent Example
Demonstrates the simplest usage of the MiMo Smart Agent.
"""

import os
from dotenv import load_dotenv

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mimo_agent.agent import MiMoAgent


def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("MIMO_API_KEY")
    if not api_key:
        print("❌ Please set MIMO_API_KEY in .env file")
        print("   Copy .env.example to .env and edit it")
        return
    
    # Initialize agent
    agent = MiMoAgent(
        api_key=api_key,
        model="MiMo-V2.5-Pro",
        tools=["web_search", "file_ops", "code_exec", "git_ops"],
    )
    
    print("🤖 MiMo Smart Agent - Basic Example")
    print("=" * 50)
    
    # Run a simple task
    task = "Explain the key features of MiMo-V2.5-Pro and how it compares to other open-source LLMs."
    
    print(f"\n📋 Task: {task}")
    print("-" * 50)
    
    result = agent.run(task)
    
    print(f"\n📝 Result:")
    print(result.output)
    print("-" * 50)
    print(f"📊 Stats: {len(result.steps)} steps, "
          f"{result.usage.get('total_tokens', 'N/A')} tokens, "
          f"{result.total_duration:.2f}s")


if __name__ == "__main__":
    main()
