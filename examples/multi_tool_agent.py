"""
Multi-Tool Agent Example
Demonstrates the agent using multiple tools to complete a complex task.
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mimo_agent.agent import MiMoAgent


def main():
    load_dotenv()
    
    api_key = os.getenv("MIMO_API_KEY")
    if not api_key:
        print("❌ Please set MIMO_API_KEY in .env file")
        return
    
    agent = MiMoAgent(
        api_key=api_key,
        model="MiMo-V2.5-Pro",
        tools=["web_search", "file_ops", "code_exec"],
    )
    
    print("🛠️  MiMo Multi-Tool Agent Demo")
    print("=" * 60)
    
    task = """
    1. Search for the latest Python version and its new features
    2. Check if there are any Python files in the current directory
    3. Write a summary report to report.md
    """
    
    print(f"📋 Complex Task")
    print(task)
    print("=" * 60)
    
    result = agent.run(task)
    
    print("\n📝 Result:")
    print(result.output)
    print("-" * 60)
    print(f"📊 {len(result.steps)} steps | {result.total_duration:.2f}s")


if __name__ == "__main__":
    main()
