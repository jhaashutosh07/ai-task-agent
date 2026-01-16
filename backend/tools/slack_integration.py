"""
Slack integration tool for sending messages and reading channel history.
"""

import logging
import os
from typing import Optional, List
from datetime import datetime, timezone

import httpx

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class SlackIntegrationTool(BaseTool):
    """Tool for Slack integration."""

    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN")
        self.base_url = "https://slack.com/api"

    @property
    def name(self) -> str:
        return "slack"

    @property
    def description(self) -> str:
        return "Send messages to Slack channels, read channel history, and manage Slack interactions"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["send_message", "read_history", "list_channels", "get_user_info", "upload_file"],
                    "description": "The Slack action to perform"
                },
                "channel": {
                    "type": "string",
                    "description": "Channel ID or name (e.g., #general or C1234567890)"
                },
                "message": {
                    "type": "string",
                    "description": "Message text to send"
                },
                "thread_ts": {
                    "type": "string",
                    "description": "Thread timestamp to reply to a thread"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of messages to retrieve (default: 10, max: 100)",
                    "default": 10
                },
                "user_id": {
                    "type": "string",
                    "description": "User ID for get_user_info action"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to file for upload_file action"
                },
                "file_title": {
                    "type": "string",
                    "description": "Title for uploaded file"
                },
                "blocks": {
                    "type": "array",
                    "description": "Rich message blocks (Slack Block Kit format)"
                }
            },
            "required": ["action"]
        }

    async def execute(
        self,
        action: str,
        channel: Optional[str] = None,
        message: Optional[str] = None,
        thread_ts: Optional[str] = None,
        limit: int = 10,
        user_id: Optional[str] = None,
        file_path: Optional[str] = None,
        file_title: Optional[str] = None,
        blocks: Optional[List[dict]] = None,
        **kwargs
    ) -> ToolResult:
        """Execute Slack action."""

        if not self.token:
            return ToolResult(
                success=False,
                output="",
                error="SLACK_BOT_TOKEN environment variable not set. Please configure your Slack bot token."
            )

        try:
            if action == "send_message":
                return await self._send_message(channel, message, thread_ts, blocks)
            elif action == "read_history":
                return await self._read_history(channel, limit)
            elif action == "list_channels":
                return await self._list_channels()
            elif action == "get_user_info":
                return await self._get_user_info(user_id)
            elif action == "upload_file":
                return await self._upload_file(channel, file_path, file_title, message)
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown action: {action}"
                )

        except Exception as e:
            logger.error(f"Slack action failed: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Slack action failed: {str(e)}"
            )

    async def _send_message(
        self,
        channel: Optional[str],
        message: Optional[str],
        thread_ts: Optional[str],
        blocks: Optional[List[dict]]
    ) -> ToolResult:
        """Send a message to a Slack channel."""
        if not channel:
            return ToolResult(
                success=False,
                output="",
                error="Channel is required for send_message action"
            )

        if not message and not blocks:
            return ToolResult(
                success=False,
                output="",
                error="Message or blocks required for send_message action"
            )

        payload = {
            "channel": channel,
        }

        if message:
            payload["text"] = message
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat.postMessage",
                headers={"Authorization": f"Bearer {self.token}"},
                json=payload
            )

            data = response.json()

            if data.get("ok"):
                logger.info(f"Message sent to {channel}")
                return ToolResult(
                    success=True,
                    output=f"Message sent successfully to {channel}. Timestamp: {data.get('ts')}"
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Slack API error: {data.get('error', 'Unknown error')}"
                )

    async def _read_history(self, channel: Optional[str], limit: int) -> ToolResult:
        """Read message history from a channel."""
        if not channel:
            return ToolResult(
                success=False,
                output="",
                error="Channel is required for read_history action"
            )

        limit = min(limit, 100)  # Cap at 100

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/conversations.history",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"channel": channel, "limit": limit}
            )

            data = response.json()

            if data.get("ok"):
                messages = data.get("messages", [])
                formatted_messages = []

                for msg in messages:
                    ts = float(msg.get("ts", 0))
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    formatted_messages.append({
                        "user": msg.get("user", "unknown"),
                        "text": msg.get("text", ""),
                        "timestamp": dt.isoformat(),
                        "thread_ts": msg.get("thread_ts"),
                        "reply_count": msg.get("reply_count", 0)
                    })

                import json
                return ToolResult(
                    success=True,
                    output=json.dumps(formatted_messages, indent=2)
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Slack API error: {data.get('error', 'Unknown error')}"
                )

    async def _list_channels(self) -> ToolResult:
        """List available Slack channels."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/conversations.list",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"types": "public_channel,private_channel", "limit": 100}
            )

            data = response.json()

            if data.get("ok"):
                channels = data.get("channels", [])
                formatted_channels = [
                    {
                        "id": ch.get("id"),
                        "name": ch.get("name"),
                        "is_private": ch.get("is_private", False),
                        "num_members": ch.get("num_members", 0)
                    }
                    for ch in channels
                ]

                import json
                return ToolResult(
                    success=True,
                    output=json.dumps(formatted_channels, indent=2)
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Slack API error: {data.get('error', 'Unknown error')}"
                )

    async def _get_user_info(self, user_id: Optional[str]) -> ToolResult:
        """Get information about a Slack user."""
        if not user_id:
            return ToolResult(
                success=False,
                output="",
                error="user_id is required for get_user_info action"
            )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users.info",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"user": user_id}
            )

            data = response.json()

            if data.get("ok"):
                user = data.get("user", {})
                user_info = {
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "real_name": user.get("real_name"),
                    "email": user.get("profile", {}).get("email"),
                    "title": user.get("profile", {}).get("title"),
                    "is_admin": user.get("is_admin", False),
                    "is_bot": user.get("is_bot", False),
                    "timezone": user.get("tz")
                }

                import json
                return ToolResult(
                    success=True,
                    output=json.dumps(user_info, indent=2)
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Slack API error: {data.get('error', 'Unknown error')}"
                )

    async def _upload_file(
        self,
        channel: Optional[str],
        file_path: Optional[str],
        file_title: Optional[str],
        message: Optional[str]
    ) -> ToolResult:
        """Upload a file to Slack."""
        if not channel:
            return ToolResult(
                success=False,
                output="",
                error="Channel is required for upload_file action"
            )

        if not file_path:
            return ToolResult(
                success=False,
                output="",
                error="file_path is required for upload_file action"
            )

        from pathlib import Path
        path = Path(file_path)

        if not path.exists():
            return ToolResult(
                success=False,
                output="",
                error=f"File not found: {file_path}"
            )

        async with httpx.AsyncClient() as client:
            files = {"file": (path.name, path.read_bytes())}
            data = {
                "channels": channel,
            }
            if file_title:
                data["title"] = file_title
            if message:
                data["initial_comment"] = message

            response = await client.post(
                f"{self.base_url}/files.upload",
                headers={"Authorization": f"Bearer {self.token}"},
                data=data,
                files=files
            )

            result = response.json()

            if result.get("ok"):
                file_info = result.get("file", {})
                logger.info(f"File uploaded to {channel}: {file_info.get('name')}")
                return ToolResult(
                    success=True,
                    output=f"File uploaded successfully. File ID: {file_info.get('id')}, URL: {file_info.get('permalink')}"
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Slack API error: {result.get('error', 'Unknown error')}"
                )
