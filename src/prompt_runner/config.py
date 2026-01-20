"""YAML configuration loading for prompts and profiles."""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jinja2 import BaseLoader, Environment, TemplateError, UndefinedError


@dataclass
class LLMSettings:
    """LLM settings from configuration.

    Attributes:
        provider: The LLM provider name (e.g., 'openai').
        model: The model identifier (e.g., 'o4-mini').
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in response.
        enable_web_search: Whether to enable web search.
    """

    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 1.0
    max_tokens: int | None = None
    enable_web_search: bool = False


@dataclass
class DeliverySettings:
    """Delivery settings from configuration.

    Attributes:
        provider: The delivery provider name (e.g., 'email').
        recipients: List of recipient addresses.
        subject: Subject line for the message.
    """

    provider: str = "email"
    recipients: list[str] = field(default_factory=list)
    subject: str | None = None


@dataclass
class PromptConfig:
    """Configuration for a prompt.

    Attributes:
        name: The prompt name/identifier.
        prompt: The prompt text to send to the LLM.
        system_prompt: Optional system prompt for context.
        llm: LLM settings.
        delivery: Delivery settings.
    """

    name: str
    prompt: str
    system_prompt: str | None = None
    llm: LLMSettings = field(default_factory=LLMSettings)
    delivery: DeliverySettings = field(default_factory=DeliverySettings)


class ConfigError(Exception):
    """Raised when there's a configuration error."""

    pass


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Dictionary of the parsed YAML content.

    Raises:
        ConfigError: If the file doesn't exist or is invalid YAML.
    """
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
            return data if data else {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}") from e


def load_profile(path: Path) -> dict[str, Any]:
    """Load profile YAML file."""
    return load_yaml(path)


def build_template_context(profile_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build context with built-ins and profile variables."""
    now = datetime.now()
    context = {
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M"),
        "current_datetime": now.isoformat(),
        "current_weekday": now.strftime("%A"),
        "env": os.environ,
        "profile": profile_data or {},
    }
    # Flatten profile at top level for convenience
    if profile_data:
        for key, value in profile_data.items():
            if key not in context:
                context[key] = value
    return context


def render_template(template_str: str, context: dict[str, Any]) -> str:
    """Render Jinja2 template. Raises ConfigError on failure."""
    try:
        env = Environment(loader=BaseLoader(), autoescape=False)
        template = env.from_string(template_str)
        return template.render(context)
    except UndefinedError as e:
        raise ConfigError(f"Template variable not defined: {e}") from e
    except TemplateError as e:
        raise ConfigError(f"Template rendering error: {e}") from e


def load_prompt_config(path: Path, profile_path: Path | None = None) -> PromptConfig:
    """Load a prompt configuration from a YAML file.

    Supports Jinja2 templating in YAML files. Template context includes:
    - current_date, current_time, current_datetime, current_weekday
    - env (access to environment variables)
    - profile (profile data if provided)
    - All top-level profile keys are also available directly

    Expected YAML format:
    ```yaml
    name: my-prompt
    prompt: |
      What's the latest news about AI?
    system_prompt: You are a helpful assistant.
    llm:
      provider: openai
      model: o4-mini
      enable_web_search: true
    delivery:
      provider: email
      recipients:
        - user@example.com
      subject: Daily AI News
    ```

    Args:
        path: Path to the prompt YAML file.
        profile_path: Optional path to a profile YAML file for template variables.

    Returns:
        PromptConfig object.

    Raises:
        ConfigError: If the config is invalid.
    """
    # Load profile if provided
    profile_data = load_profile(profile_path) if profile_path else None

    # Build template context
    context = build_template_context(profile_data)

    # Read raw YAML, render through Jinja2, then parse
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path) as f:
            raw_yaml = f.read()
    except OSError as e:
        raise ConfigError(f"Cannot read {path}: {e}") from e

    rendered_yaml = render_template(raw_yaml, context)

    try:
        data = yaml.safe_load(rendered_yaml)
        data = data if data else {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}") from e

    if "prompt" not in data:
        raise ConfigError(f"Missing required field 'prompt' in {path}")

    # Parse LLM settings
    llm_data = data.get("llm", {})
    llm = LLMSettings(
        provider=llm_data.get("provider", "openai"),
        model=llm_data.get("model", "gpt-4o"),
        temperature=llm_data.get("temperature", 1.0),
        max_tokens=llm_data.get("max_tokens"),
        enable_web_search=llm_data.get("enable_web_search", False),
    )

    # Parse delivery settings
    delivery_data = data.get("delivery", {})
    delivery = DeliverySettings(
        provider=delivery_data.get("provider", "email"),
        recipients=delivery_data.get("recipients", []),
        subject=delivery_data.get("subject"),
    )

    # Get name from config or derive from filename
    name = data.get("name", path.stem)

    return PromptConfig(
        name=name,
        prompt=data["prompt"],
        system_prompt=data.get("system_prompt"),
        llm=llm,
        delivery=delivery,
    )


def find_prompts_dir() -> Path | None:
    """Find the prompts directory.

    Searches for a 'prompts' directory in the current directory
    and parent directories.

    Returns:
        Path to the prompts directory, or None if not found.
    """
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        prompts_dir = parent / "prompts"
        if prompts_dir.is_dir():
            return prompts_dir
    return None


def list_prompts(prompts_dir: Path | None = None) -> list[str]:
    """List available prompt configurations.

    Args:
        prompts_dir: Directory to search for prompts. If None, auto-detect.

    Returns:
        List of prompt names (without .yml extension).
    """
    if prompts_dir is None:
        prompts_dir = find_prompts_dir()

    if prompts_dir is None or not prompts_dir.exists():
        return []

    prompts = []
    for path in prompts_dir.glob("*.yml"):
        prompts.append(path.stem)
    for path in prompts_dir.glob("*.yaml"):
        prompts.append(path.stem)

    return sorted(set(prompts))


def resolve_prompt_path(prompt_name: str, prompts_dir: Path | None = None) -> Path:
    """Resolve a prompt name to its file path.

    Args:
        prompt_name: Name of the prompt or path to YAML file.
        prompts_dir: Directory to search for prompts. If None, auto-detect.

    Returns:
        Path to the prompt YAML file.

    Raises:
        ConfigError: If the prompt cannot be found.
    """
    # If it looks like a path, use it directly
    path = Path(prompt_name)
    if path.suffix in (".yml", ".yaml") or path.exists():
        if not path.exists():
            raise ConfigError(f"Prompt file not found: {path}")
        return path

    # Otherwise, search in prompts directory
    if prompts_dir is None:
        prompts_dir = find_prompts_dir()

    if prompts_dir is None:
        raise ConfigError(
            f"Cannot find prompt '{prompt_name}': no prompts directory found"
        )

    # Try .yml and .yaml extensions
    for ext in (".yml", ".yaml"):
        candidate = prompts_dir / f"{prompt_name}{ext}"
        if candidate.exists():
            return candidate

    raise ConfigError(f"Prompt '{prompt_name}' not found in {prompts_dir}")
