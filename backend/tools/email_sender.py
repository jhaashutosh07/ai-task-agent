import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from .base import BaseTool, ToolResult

try:
    import aiosmtplib
    SMTP_AVAILABLE = True
except ImportError:
    SMTP_AVAILABLE = False


class EmailSenderTool(BaseTool):
    """Send emails via SMTP"""

    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        require_confirmation: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.require_confirmation = require_confirmation
        self.pending_email = None

    @property
    def name(self) -> str:
        return "send_email"

    @property
    def description(self) -> str:
        return """Send an email via SMTP.
Requires SMTP configuration and user confirmation before sending."""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Recipient email addresses"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                },
                "html": {
                    "type": "boolean",
                    "description": "Send as HTML email",
                    "default": False
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CC recipients"
                }
            },
            "required": ["to", "subject", "body"]
        }

    @property
    def is_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    async def execute(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: bool = False,
        cc: List[str] = None
    ) -> ToolResult:
        if not SMTP_AVAILABLE:
            return ToolResult(
                success=False,
                output="",
                error="aiosmtplib is not installed. Run: pip install aiosmtplib"
            )

        if not self.is_configured:
            return ToolResult(
                success=False,
                output="",
                error="Email not configured. Set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD in .env"
            )

        # Store pending email for confirmation
        if self.require_confirmation:
            self.pending_email = {
                "to": to,
                "cc": cc,
                "subject": subject,
                "body": body,
                "html": html
            }

            preview = f"""**Email Preview (requires confirmation):**

**To:** {', '.join(to)}
**CC:** {', '.join(cc) if cc else 'None'}
**Subject:** {subject}

**Body:**
{body[:500]}{'...' if len(body) > 500 else ''}

---
Call `confirm_send_email` to send this email."""

            return ToolResult(
                success=True,
                output=preview
            )

        # Send email directly (if confirmation not required)
        return await self._send_email(to, cc, subject, body, html)

    async def confirm_send(self) -> ToolResult:
        """Confirm and send pending email"""
        if not self.pending_email:
            return ToolResult(
                success=False,
                output="",
                error="No pending email to send"
            )

        email = self.pending_email
        self.pending_email = None

        return await self._send_email(
            email["to"],
            email["cc"],
            email["subject"],
            email["body"],
            email["html"]
        )

    async def _send_email(
        self,
        to: List[str],
        cc: List[str],
        subject: str,
        body: str,
        html: bool
    ) -> ToolResult:
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = ", ".join(to)

            if cc:
                msg["Cc"] = ", ".join(cc)

            # Add body
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # All recipients
            all_recipients = to + (cc or [])

            # Send
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True
            )

            return ToolResult(
                success=True,
                output=f"""**Email Sent Successfully**

**To:** {', '.join(to)}
**Subject:** {subject}
**Recipients:** {len(all_recipients)}"""
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to send email: {str(e)}"
            )
