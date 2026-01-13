"""CLI entry point using Click."""

import click

@click.group()
@click.version_option()
def main():
    """Prompt Runner - Schedule prompts to LLMs with web search capabilities."""
    pass

@main.command()
@click.argument("prompt_name")
@click.option("--profile", "-p", help="Path to profile YAML file")
@click.option("--dry-run", is_flag=True, help="Validate without running")
def run(prompt_name: str, profile: str | None, dry_run: bool):
    """Run a prompt configuration."""
    click.echo(f"Running prompt: {prompt_name}")
    if profile:
        click.echo(f"Using profile: {profile}")
    if dry_run:
        click.echo("(dry-run mode)")

@main.command()
def list():
    """List available prompts."""
    click.echo("Available prompts: (none configured)")

if __name__ == "__main__":
    main()
