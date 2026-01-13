"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMConfig:
    """Configuration for an LLM provider.

    Attributes:
        model: The model identifier (e.g., 'o3', 'o4-mini', 'gpt-4o').
        temperature: Sampling temperature (0.0 to 2.0). Lower is more deterministic.
        max_tokens: Maximum tokens in the response. None means provider default.
        enable_web_search: Whether to enable web search capabilities.
        extra: Additional provider-specific configuration options.
    """

    model: str
    temperature: float = 1.0
    max_tokens: int | None = None
    enable_web_search: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSearchResult:
    """A single web search result returned by the LLM.

    Attributes:
        title: The title of the search result.
        url: The URL of the search result.
        snippet: A text snippet from the search result.
    """

    title: str
    url: str
    snippet: str


@dataclass
class LLMResponse:
    """Response from an LLM provider.

    Attributes:
        content: The text content of the response.
        model: The model that generated the response.
        web_search_results: List of web search results if web search was used.
        usage: Token usage information (prompt_tokens, completion_tokens, total_tokens).
        raw_response: The raw response object from the provider for debugging.
    """

    content: str
    model: str
    web_search_results: list[WebSearchResult] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    raw_response: Any = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Subclasses must implement the `complete` method to interact with their
    respective LLM APIs. This abstraction allows swapping between providers
    (OpenAI, Anthropic, Google, local models) without changing application code.

    Example:
        >>> config = LLMConfig(model="o4-mini", enable_web_search=True)
        >>> provider = OpenAIProvider(api_key="...", config=config)
        >>> response = provider.complete("What's the latest news on AI?")
        >>> print(response.content)
    """

    def __init__(self, config: LLMConfig) -> None:
        """Initialize the provider with configuration.

        Args:
            config: The LLM configuration specifying model, parameters, etc.
        """
        self.config = config

    @abstractmethod
    def complete(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        """Send a prompt to the LLM and get a response.

        Args:
            prompt: The user prompt to send to the LLM.
            system_prompt: Optional system prompt to set context/behavior.

        Returns:
            LLMResponse containing the model's response and metadata.

        Raises:
            LLMError: If the API call fails.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this provider (e.g., 'openai', 'anthropic')."""
        pass

    def validate_config(self) -> None:
        """Validate the provider configuration.

        Subclasses can override this to add provider-specific validation.

        Raises:
            ValueError: If the configuration is invalid.
        """
        if not self.config.model:
            raise ValueError("Model must be specified in config")
        if self.config.temperature < 0 or self.config.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        if self.config.max_tokens is not None and self.config.max_tokens <= 0:
            raise ValueError("max_tokens must be positive if specified")


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    pass


class LLMConfigError(LLMError):
    """Raised when there's a configuration error."""

    pass


class LLMAPIError(LLMError):
    """Raised when an API call fails.

    Attributes:
        status_code: HTTP status code if available.
        provider: The name of the provider that raised the error.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        provider: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.provider = provider


class LLMRateLimitError(LLMAPIError):
    """Raised when rate limited by the provider."""

    pass
