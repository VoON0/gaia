"""
MiMo Code Reviewer Example
Demonstrates automated code review using MiMo Smart Agent.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mimo_agent.agent import MiMoAgent


def review_code(agent: MiMoAgent, path: str, output: str | None = None):
    """Review all code files in the given path."""
    
    # Collect files
    files_context = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules")]
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".go", ".rs", ".java", ".md")):
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp)
                try:
                    with open(fp, "r", encoding="utf-8") as fh:
                        content = fh.read(3000)
                    files_context.append(f"### {rel}\n```\n{content}\n```")
                except Exception:
                    files_context.append(f"### {rel}\n[Could not read file]")
    
    if not files_context:
        print("No code files found.")
        return
    
    task = f"""Review the following code files thoroughly:

{chr(10).join(files_context)}

For each file, evaluate:
1. **Correctness**: Are there any bugs or logical errors?
2. **Performance**: Any performance bottlenecks?
3. **Security**: Any security vulnerabilities?
4. **Style**: Follows best practices and conventions?
5. **Improvements**: Specific suggestions for improvement

Provide a structured review with severity levels (HIGH/MEDIUM/LOW) for each issue found.
"""
    
    print(f"🔍 Reviewing {len(files_context)} files...")
    result = agent.run(task)
    
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result.output)
        print(f"✅ Review saved to {output}")
    else:
        print(result.output)


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="MiMo Code Reviewer")
    parser.add_argument("path", help="Path to code directory")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--api-key", help="MiMo API key")
    args = parser.parse_args()
    
    api_key = args.api_key or os.getenv("MIMO_API_KEY")
    if not api_key:
        print("❌ Please set MIMO_API_KEY in .env file")
        return
    
    agent = MiMoAgent(api_key=api_key, model="MiMo-V2.5-Pro")
    review_code(agent, args.path, args.output)


if __name__ == "__main__":
    main()
