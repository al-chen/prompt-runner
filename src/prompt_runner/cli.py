"""CLI entry point using Click."""

import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from prompt_runner.config import (
    ConfigError,
    list_prompts,
    load_prompt_config,
    resolve_prompt_path,
)
from prompt_runner.delivery.base import DeliveryConfig, DeliveryError
from prompt_runner.delivery.email import EmailDeliveryProvider
from prompt_runner.llm.base import LLMConfig, LLMError
from prompt_runner.llm.openai_provider import OpenAIProvider
from prompt_runner.rendering import markdown_to_html

# Instructions appended to system prompt for one-off automated deliveries
ONE_OFF_DELIVERY_INSTRUCTIONS = """
IMPORTANT: This is a one-off automated delivery (not a live chat).
- Provide complete, final answers
- Do NOT ask follow-up questions or request clarification
- Do NOT use phrases like "let me know if..." or "reply with..."
- Include all relevant information in your response"""


@click.group()
@click.version_option()
def main():
    """Prompt Runner - Schedule prompts to LLMs with web search capabilities."""
    load_dotenv()


@main.command()
@click.argument("prompt_name")
@click.option("--profile", "-p", help="Path to profile YAML file")
@click.option("--dry-run", is_flag=True, help="Validate and show prompt without running")
@click.option("--no-deliver", is_flag=True, help="Run LLM but skip delivery")
@click.option("--output", "-o", type=click.Path(), help="Write response to file")
def run(
    prompt_name: str,
    profile: str | None,
    dry_run: bool,
    no_deliver: bool,
    output: str | None,
):
    """Run a prompt configuration.

    PROMPT_NAME can be a prompt name (e.g., 'daily-briefing') or a path to a
    YAML file (e.g., './prompts/my-prompt.yml').
    """
    try:
        # Load the prompt configuration
        prompt_path = resolve_prompt_path(prompt_name)
        profile_path = Path(profile) if profile else None
        config = load_prompt_config(prompt_path, profile_path=profile_path)

        click.echo(f"Prompt: {config.name}")
        click.echo(f"Model: {config.llm.provider}/{config.llm.model}")
        if config.llm.enable_web_search:
            click.echo("Web search: enabled")

        if dry_run:
            # Show the effective system prompt with one-off delivery instructions
            if config.system_prompt:
                effective_system_prompt = config.system_prompt + ONE_OFF_DELIVERY_INSTRUCTIONS
            else:
                effective_system_prompt = ONE_OFF_DELIVERY_INSTRUCTIONS.strip()

            click.echo("\n--- Dry Run Mode ---")
            click.echo(f"\nSystem prompt:\n{effective_system_prompt}")
            click.echo(f"\nPrompt:\n{config.prompt}")
            if config.delivery.recipients:
                click.echo(f"\nWould deliver to: {', '.join(config.delivery.recipients)}")
            return

        # Create LLM provider
        llm_config = LLMConfig(
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            enable_web_search=config.llm.enable_web_search,
        )

        if config.llm.provider == "openai":
            provider = OpenAIProvider(llm_config)
        else:
            raise ConfigError(f"Unknown LLM provider: {config.llm.provider}")

        # Construct system prompt with one-off delivery instructions
        if config.system_prompt:
            system_prompt = config.system_prompt + ONE_OFF_DELIVERY_INSTRUCTIONS
        else:
            system_prompt = ONE_OFF_DELIVERY_INSTRUCTIONS.strip()

        # Call the LLM
        click.echo("\nCalling LLM...")
        response = provider.complete(config.prompt, system_prompt)

        click.echo(f"Response received ({response.usage.get('total_tokens', '?')} tokens)")

        if response.web_search_results:
            click.echo(f"Web search: {len(response.web_search_results)} results")

        # Output response
        if output:
            with open(output, "w") as f:
                f.write(response.content)
            click.echo(f"Response written to: {output}")
        else:
            click.echo("\n--- Response ---")
            click.echo(response.content)

        # Deliver if configured
        if not no_deliver and config.delivery.recipients:
            click.echo("\nDelivering response...")
            _deliver_response(config, response.content)
            click.echo("Delivery complete!")

    except ConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except LLMError as e:
        click.echo(f"LLM error: {e}", err=True)
        sys.exit(1)
    except DeliveryError as e:
        click.echo(f"Delivery error: {e}", err=True)
        sys.exit(1)


def _deliver_response(config, content: str) -> None:
    """Deliver the response using the configured delivery provider."""
    if config.delivery.provider != "email":
        raise ConfigError(f"Unknown delivery provider: {config.delivery.provider}")

    sender = os.environ.get("GMAIL_SENDER")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not sender or not app_password:
        raise ConfigError(
            "Email delivery requires GMAIL_SENDER and GMAIL_APP_PASSWORD environment variables"
        )

    delivery_config = DeliveryConfig(
        recipients=config.delivery.recipients,
        subject=config.delivery.subject or f"Prompt Runner: {config.name}",
    )

    provider = EmailDeliveryProvider(
        sender=sender,
        app_password=app_password,
        config=delivery_config,
    )

    content_html = markdown_to_html(content)
    result = provider.deliver(content, content_html)
    if not result.success:
        raise DeliveryError(result.error or "Delivery failed")


@main.command()
@click.argument("prompt_name")
@click.option("--profile", "-p", help="Path to profile YAML file")
def validate(prompt_name: str, profile: str | None):
    """Validate a prompt configuration without running it."""
    try:
        prompt_path = resolve_prompt_path(prompt_name)
        profile_path = Path(profile) if profile else None
        config = load_prompt_config(prompt_path, profile_path=profile_path)

        click.echo(f"✓ Prompt '{config.name}' is valid")
        click.echo(f"  Model: {config.llm.provider}/{config.llm.model}")
        click.echo(f"  Web search: {'enabled' if config.llm.enable_web_search else 'disabled'}")
        if config.delivery.recipients:
            click.echo(f"  Delivery: {len(config.delivery.recipients)} recipient(s)")
        else:
            click.echo("  Delivery: not configured")

    except ConfigError as e:
        click.echo(f"✗ Invalid configuration: {e}", err=True)
        sys.exit(1)


@main.command("list")
def list_cmd():
    """List available prompts."""
    prompts = list_prompts()

    if not prompts:
        click.echo("No prompts found.")
        click.echo("Create a 'prompts/' directory with .yml files to get started.")
        return

    click.echo("Available prompts:")
    for name in prompts:
        click.echo(f"  - {name}")


if __name__ == "__main__":
    main()
