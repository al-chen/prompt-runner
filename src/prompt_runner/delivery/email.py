"""Gmail SMTP delivery provider."""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .base import (
    DeliveryAuthError,
    DeliveryConfig,
    DeliveryConnectionError,
    DeliveryError,
    DeliveryProvider,
    DeliveryResult,
)

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


class EmailDeliveryProvider(DeliveryProvider):
    """Gmail SMTP delivery provider.

    Uses Gmail's SMTP server with an App Password for authentication.
    App Passwords are 16-character codes generated from your Google Account
    security settings when 2FA is enabled.

    Example:
        >>> config = DeliveryConfig(
        ...     recipients=["recipient@example.com"],
        ...     subject="Daily Briefing"
        ... )
        >>> provider = EmailDeliveryProvider(
        ...     sender="your.email@gmail.com",
        ...     app_password="xxxx xxxx xxxx xxxx",
        ...     config=config
        ... )
        >>> result = provider.deliver("Here's your daily briefing content...")
        >>> print(result.success)
    """

    def __init__(
        self,
        sender: str,
        app_password: str,
        config: DeliveryConfig,
        smtp_host: str = GMAIL_SMTP_HOST,
        smtp_port: int = GMAIL_SMTP_PORT,
    ) -> None:
        """Initialize the email delivery provider.

        Args:
            sender: The Gmail address to send from.
            app_password: Gmail App Password (16 characters, spaces optional).
            config: Delivery configuration with recipients and subject.
            smtp_host: SMTP server hostname (default: smtp.gmail.com).
            smtp_port: SMTP server port (default: 587 for STARTTLS).
        """
        super().__init__(config)
        self.sender = sender
        self.app_password = app_password.replace(" ", "")
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    @property
    def name(self) -> str:
        """Return the name of this provider."""
        return "email"

    def validate_config(self) -> None:
        """Validate the email configuration."""
        super().validate_config()
        if not self.sender:
            raise ValueError("Sender email must be specified")
        if not self.app_password:
            raise ValueError("App password must be specified")
        if len(self.app_password) != 16:
            raise ValueError("App password must be 16 characters")

    def deliver(self, content: str, content_html: str | None = None) -> DeliveryResult:
        """Deliver a message via Gmail SMTP.

        Args:
            content: The plain text content of the email.
            content_html: Optional HTML version of the content.

        Returns:
            DeliveryResult indicating success or failure.

        Raises:
            DeliveryAuthError: If authentication fails.
            DeliveryConnectionError: If connection to SMTP server fails.
            DeliveryError: For other delivery failures.
        """
        msg = self._build_message(content, content_html)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender, self.app_password)
                server.send_message(msg)

            return DeliveryResult(
                success=True,
                recipients_count=len(self.config.recipients),
            )

        except smtplib.SMTPAuthenticationError as e:
            raise DeliveryAuthError(f"SMTP authentication failed: {e}") from e
        except smtplib.SMTPConnectError as e:
            raise DeliveryConnectionError(f"Failed to connect to SMTP server: {e}") from e
        except smtplib.SMTPException as e:
            raise DeliveryError(f"SMTP error: {e}") from e
        except OSError as e:
            raise DeliveryConnectionError(f"Network error: {e}") from e

    def _build_message(self, content: str, content_html: str | None) -> MIMEMultipart:
        """Build a MIME message with plain text and optional HTML.

        Args:
            content: Plain text content.
            content_html: Optional HTML content.

        Returns:
            A MIMEMultipart message ready to send.
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = self.config.subject or "Prompt Runner"
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.config.recipients)

        msg.attach(MIMEText(content, "plain"))
        if content_html:
            msg.attach(MIMEText(content_html, "html"))

        return msg
