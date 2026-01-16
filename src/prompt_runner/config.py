"""YAML configuration loading for prompts and profiles."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


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


def load_prompt_config(path: Path) -> PromptConfig:
    """Load a prompt configuration from a YAML file.

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

    Returns:
        PromptConfig object.

    Raises:
        ConfigError: If the config is invalid.
    """
    data = load_yaml(path)

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
