"""Abstract base class for delivery providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeliveryConfig:
    """Configuration for a delivery provider.

    Attributes:
        recipients: List of recipient addresses (email, user IDs, etc.).
        subject: Subject line for the message (if applicable).
        extra: Additional provider-specific configuration options.
    """

    recipients: list[str]
    subject: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliveryResult:
    """Result of a delivery attempt.

    Attributes:
        success: Whether the delivery was successful.
        message_id: Provider-specific message ID if available.
        recipients_count: Number of recipients the message was sent to.
        error: Error message if delivery failed.
    """

    success: bool
    message_id: str | None = None
    recipients_count: int = 0
    error: str | None = None


class DeliveryProvider(ABC):
    """Abstract base class for delivery providers.

    Subclasses must implement the `deliver` method to send messages through
    their respective channels. This abstraction allows swapping between delivery
    methods (email, Slack, Discord, webhooks) without changing application code.

    Example:
        >>> config = DeliveryConfig(recipients=["user@example.com"], subject="Daily Briefing")
        >>> provider = EmailDeliveryProvider(sender="me@gmail.com", app_password="...", config=config)
        >>> result = provider.deliver("Here's your daily briefing...")
        >>> print(result.success)
    """

    def __init__(self, config: DeliveryConfig) -> None:
        """Initialize the provider with configuration.

        Args:
            config: The delivery configuration specifying recipients, etc.
        """
        self.config = config

    @abstractmethod
    def deliver(self, content: str, content_html: str | None = None) -> DeliveryResult:
        """Deliver a message to the configured recipients.

        Args:
            content: The plain text content to deliver.
            content_html: Optional HTML version of the content.

        Returns:
            DeliveryResult indicating success or failure.

        Raises:
            DeliveryError: If the delivery fails.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this provider (e.g., 'email', 'slack')."""
        pass

    def validate_config(self) -> None:
        """Validate the provider configuration.

        Subclasses can override this to add provider-specific validation.

        Raises:
            ValueError: If the configuration is invalid.
        """
        if not self.config.recipients:
            raise ValueError("At least one recipient must be specified")


class DeliveryError(Exception):
    """Base exception for delivery-related errors."""

    pass


class DeliveryConfigError(DeliveryError):
    """Raised when there's a configuration error."""

    pass


class DeliveryConnectionError(DeliveryError):
    """Raised when connection to the delivery service fails."""

    pass


class DeliveryAuthError(DeliveryError):
    """Raised when authentication fails."""

    pass
