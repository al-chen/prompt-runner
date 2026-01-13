"""OpenAI LLM provider with web search support."""

import os

from openai import OpenAI, APIError, RateLimitError, APIConnectionError

from prompt_runner.llm.base import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    WebSearchResult,
    LLMAPIError,
    LLMConfigError,
    LLMRateLimitError,
)


class OpenAIProvider(LLMProvider):
    """OpenAI provider using the Responses API with web_search support.

    This provider uses OpenAI's Responses API which supports built-in tools
    like web_search for models such as o3, o4-mini, and gpt-4o.

    Example:
        >>> config = LLMConfig(model="o4-mini", enable_web_search=True)
        >>> provider = OpenAIProvider(config, api_key="sk-...")
        >>> response = provider.complete("What's the latest AI news?")
        >>> print(response.content)
    """

    def __init__(
        self,
        config: LLMConfig,
        api_key: str | None = None,
    ) -> None:
        """Initialize the OpenAI provider.

        Args:
            config: LLM configuration specifying model, parameters, etc.
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.

        Raises:
            LLMConfigError: If no API key is available.
        """
        super().__init__(config)
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise LLMConfigError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self._client = OpenAI(api_key=self._api_key)

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "openai"

    def complete(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        """Send a prompt to OpenAI and get a response.

        Uses the Responses API which supports built-in tools like web_search.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt for context.

        Returns:
            LLMResponse with the model's response and any web search results.

        Raises:
            LLMRateLimitError: If rate limited by OpenAI.
            LLMAPIError: If the API call fails.
        """
        try:
            # Build the request parameters
            params = self._build_request_params(prompt, system_prompt)

            # Call the Responses API
            response = self._client.responses.create(**params)

            # Parse the response
            return self._parse_response(response)

        except RateLimitError as e:
            raise LLMRateLimitError(
                f"OpenAI rate limit exceeded: {e}",
                status_code=429,
                provider=self.name,
            ) from e
        except APIConnectionError as e:
            raise LLMAPIError(
                f"Failed to connect to OpenAI API: {e}",
                provider=self.name,
            ) from e
        except APIError as e:
            raise LLMAPIError(
                f"OpenAI API error: {e}",
                status_code=getattr(e, "status_code", None),
                provider=self.name,
            ) from e

    def _build_request_params(
        self, prompt: str, system_prompt: str | None
    ) -> dict:
        """Build the request parameters for the Responses API.

        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt.

        Returns:
            Dictionary of parameters for the API call.
        """
        params: dict = {
            "model": self.config.model,
            "input": prompt,
        }

        # Add system instructions if provided
        if system_prompt:
            params["instructions"] = system_prompt

        # Add temperature if not using default
        if self.config.temperature != 1.0:
            params["temperature"] = self.config.temperature

        # Add max tokens if specified
        if self.config.max_tokens is not None:
            params["max_output_tokens"] = self.config.max_tokens

        # Enable web search if requested
        if self.config.enable_web_search:
            params["tools"] = [{"type": "web_search"}]

        # Add any extra provider-specific options
        params.update(self.config.extra)

        return params

    def _parse_response(self, response) -> LLMResponse:
        """Parse the OpenAI Responses API response.

        Args:
            response: The raw response from OpenAI.

        Returns:
            Parsed LLMResponse object.
        """
        content = ""
        web_search_results: list[WebSearchResult] = []

        # Parse output items from the response
        for item in response.output:
            if item.type == "message":
                # Extract text content from message
                for content_block in item.content:
                    if content_block.type == "output_text":
                        content += content_block.text
            elif item.type == "web_search_call":
                # Web search was performed - results may be embedded
                pass
            elif item.type == "web_search_result":
                # Parse web search results
                web_search_results.extend(self._parse_web_search_results(item))

        # Parse usage information
        usage = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": getattr(response.usage, "input_tokens", 0),
                "completion_tokens": getattr(response.usage, "output_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }

        return LLMResponse(
            content=content,
            model=response.model,
            web_search_results=web_search_results,
            usage=usage,
            raw_response=response,
        )

    def _parse_web_search_results(self, item) -> list[WebSearchResult]:
        """Parse web search results from a response item.

        Args:
            item: A web_search_result item from the response.

        Returns:
            List of WebSearchResult objects.
        """
        results = []
        if hasattr(item, "results"):
            for result in item.results:
                results.append(
                    WebSearchResult(
                        title=getattr(result, "title", ""),
                        url=getattr(result, "url", ""),
                        snippet=getattr(result, "snippet", ""),
                    )
                )
        return results
