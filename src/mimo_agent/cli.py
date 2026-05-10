"""
MiMo Smart Agent - Command Line Interface

Usage:
  mimo-agent run "your task description"
  mimo-agent code-review ./path
  mimo-agent doc-gen ./path --output output.md
  mimo-agent plan "your task description"
"""

import os
import sys
import json
import logging

import click
from dotenv import load_dotenv

from .agent import MiMoAgent


@click.group()
@click.option("--api-key", envvar="MIMO_API_KEY", help="MiMo API key")
@click.option("--model", default="MiMo-V2.5-Pro", help="Model name")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, api_key, model, verbose):
    """MiMo Smart Agent - Powered by Xiaomi MiMo-V2.5-Pro"""
    load_dotenv()
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    api_key = api_key or os.getenv("MIMO_API_KEY")
    if not api_key:
        click.echo("Error: MIMO_API_KEY not set. Set it in .env or pass --api-key")
        sys.exit(1)
    
    ctx.ensure_object(dict)
    ctx.obj["agent"] = MiMoAgent(
        api_key=api_key,
        model=model,
    )


@cli.command()
@click.argument("task")
@click.option("--output", "-o", help="Output file (JSON)")
@click.pass_context
def run(ctx, task, output):
    """Run an agent task."""
    agent = ctx.obj["agent"]
    click.echo(f"🤖 Running: {task}")
    
    with click.progressbar(length=1, label="Processing") as bar:
        result = agent.run(task)
        bar.update(1)
    
    click.echo("\n" + "=" * 50)
    click.echo(result.output)
    click.echo("=" * 50)
    click.echo(f"Steps: {len(result.steps)} | Tokens: {result.usage.get('total_tokens', 'N/A')}")
    
    if output:
        with open(output, "w") as f:
            json.dump({
                "task": result.task,
                "output": result.output,
                "steps": [{"id": s.id, "action": s.action, "status": s.status} for s in result.steps],
                "usage": result.usage,
            }, f, indent=2)
        click.echo(f"Results saved to {output}")


@cli.command()
@click.argument("path")
@click.option("--format", "-f", "fmt", default="markdown", help="Output format: markdown | json")
@click.option("--output", "-o", help="Output file")
@click.pass_context
def code_review(ctx, path, fmt, output):
    """Review code in the specified path."""
    agent = ctx.obj["agent"]
    
    # Build context from files
    files_context = _get_files_context(path)
    
    task = f"""Review the following code files for:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance optimization opportunities
4. Security concerns
5. Suggestions for improvement

Files to review:
{files_context}

Provide a detailed review in {fmt} format.
"""
    
    click.echo(f"🔍 Reviewing code in {path}...")
    result = agent.run(task)
    
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result.output)
        click.echo(f"Review saved to {output}")
    else:
        click.echo(result.output)


@cli.command()
@click.argument("path")
@click.option("--output", "-o", default="./docs", help="Output directory")
@click.pass_context
def doc_gen(ctx, path, output):
    """Generate documentation from source code."""
    agent = ctx.obj["agent"]
    files_context = _get_files_context(path)
    
    task = f"""Generate comprehensive documentation for the following source code.
Include:
1. Overview of the project
2. Module descriptions
3. Key functions and classes
4. Usage examples

Source code:
{files_context}
"""
    
    click.echo(f"📝 Generating docs for {path}...")
    result = agent.run(task)
    os.makedirs(output, exist_ok=True)
    
    doc_path = os.path.join(output, "README.md")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(result.output)
    click.echo(f"Documentation saved to {doc_path}")


@cli.command()
@click.argument("task")
@click.pass_context
def plan(ctx, task):
    """Create a plan for a task without executing."""
    agent = ctx.obj["agent"]
    
    click.echo(f"📋 Planning: {task}")
    steps = agent.plan(task)
    
    click.echo("\nExecution Plan:")
    for step in steps:
        click.echo(f"  [{step.id}] {step.action}")


def _get_files_context(path: str, max_files: int = 10) -> str:
    """Get context from source files for review."""
    context_parts = []
    count = 0
    
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "node_modules", ".venv", "venv")]
        
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".go", ".rs", ".java", ".yaml", ".yml", ".json", ".md")):
                if count >= max_files:
                    break
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read(2000)  # First 2000 chars
                    context_parts.append(f"\n### {relpath}\n```\n{content}\n```")
                    count += 1
                except Exception:
                    pass
    
    return "\n".join(context_parts)


def main():
    cli()


if __name__ == "__main__":
    main()
