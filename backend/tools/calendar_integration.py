"""
Calendar Integration Tool - Simple calendar event management
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List
from .base import BaseTool, ToolResult


class CalendarIntegrationTool(BaseTool):
    """
    Simple calendar event management tool.

    This tool provides local calendar functionality:
    - Create events
    - List events
    - Search events
    - Delete events
    - Set reminders

    Events are stored locally in JSON format. For production use,
    this could be integrated with Google Calendar, Outlook, etc.
    """

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.calendar_file = os.path.join(storage_path, "calendar.json")
        self._ensure_calendar_exists()

    def _ensure_calendar_exists(self):
        """Ensure the calendar storage file exists."""
        os.makedirs(self.storage_path, exist_ok=True)
        if not os.path.exists(self.calendar_file):
            self._save_events([])

    def _load_events(self) -> List[dict]:
        """Load events from storage."""
        try:
            with open(self.calendar_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_events(self, events: List[dict]):
        """Save events to storage."""
        with open(self.calendar_file, "w") as f:
            json.dump(events, f, indent=2, default=str)

    @property
    def name(self) -> str:
        return "calendar"

    @property
    def description(self) -> str:
        return """Manage calendar events. Can create, list, search, and delete events.
Available actions:
- create: Create a new event
- list: List upcoming events
- search: Search events by title/description
- delete: Delete an event by ID
- today: Show today's events
- upcoming: Show events for the next N days"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Calendar action to perform",
                    "enum": ["create", "list", "search", "delete", "today", "upcoming"]
                },
                "title": {
                    "type": "string",
                    "description": "Event title (for create/search)"
                },
                "description": {
                    "type": "string",
                    "description": "Event description (for create)"
                },
                "start_time": {
                    "type": "string",
                    "description": "Event start time (ISO format or natural language like '2024-01-15 14:00')"
                },
                "end_time": {
                    "type": "string",
                    "description": "Event end time (optional)"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID (for delete)"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days for upcoming events (default: 7)"
                },
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["action"]
        }

    async def execute(
        self,
        action: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        event_id: Optional[str] = None,
        days: int = 7,
        query: Optional[str] = None
    ) -> ToolResult:
        """Execute a calendar action."""

        try:
            if action == "create":
                return await self._create_event(title, description, start_time, end_time)
            elif action == "list":
                return await self._list_events(days)
            elif action == "search":
                return await self._search_events(query or title or "")
            elif action == "delete":
                return await self._delete_event(event_id)
            elif action == "today":
                return await self._get_today_events()
            elif action == "upcoming":
                return await self._get_upcoming_events(days)
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown action: {action}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Calendar operation failed: {str(e)}"
            )

    async def _create_event(
        self,
        title: str,
        description: Optional[str],
        start_time: str,
        end_time: Optional[str]
    ) -> ToolResult:
        """Create a new calendar event."""
        if not title:
            return ToolResult(
                success=False,
                output="",
                error="Event title is required"
            )

        if not start_time:
            return ToolResult(
                success=False,
                output="",
                error="Start time is required"
            )

        # Parse start time
        try:
            start_dt = self._parse_datetime(start_time)
        except ValueError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid start time: {e}"
            )

        # Parse end time if provided
        end_dt = None
        if end_time:
            try:
                end_dt = self._parse_datetime(end_time)
            except ValueError as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Invalid end time: {e}"
                )

        events = self._load_events()

        # Generate event ID
        event_id = f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(events)}"

        event = {
            "id": event_id,
            "title": title,
            "description": description or "",
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat() if end_dt else None,
            "created_at": datetime.now().isoformat()
        }

        events.append(event)
        self._save_events(events)

        return ToolResult(
            success=True,
            output=f"Event created successfully!\nID: {event_id}\nTitle: {title}\nStart: {start_dt.strftime('%Y-%m-%d %H:%M')}"
        )

    async def _list_events(self, days: int = 30) -> ToolResult:
        """List events within the specified number of days."""
        events = self._load_events()
        now = datetime.now()
        end_date = now + timedelta(days=days)

        upcoming = []
        for event in events:
            try:
                start = datetime.fromisoformat(event["start_time"])
                if now <= start <= end_date:
                    upcoming.append(event)
            except:
                continue

        # Sort by start time
        upcoming.sort(key=lambda e: e["start_time"])

        if not upcoming:
            return ToolResult(
                success=True,
                output=f"No events found in the next {days} days."
            )

        output = f"Events in the next {days} days:\n\n"
        for event in upcoming:
            start = datetime.fromisoformat(event["start_time"])
            output += f"- [{event['id']}] {event['title']}\n"
            output += f"  Date: {start.strftime('%Y-%m-%d %H:%M')}\n"
            if event.get("description"):
                output += f"  Description: {event['description'][:50]}...\n"
            output += "\n"

        return ToolResult(success=True, output=output)

    async def _search_events(self, query: str) -> ToolResult:
        """Search events by title or description."""
        if not query:
            return ToolResult(
                success=False,
                output="",
                error="Search query is required"
            )

        events = self._load_events()
        query_lower = query.lower()

        matches = [
            event for event in events
            if query_lower in event.get("title", "").lower() or
               query_lower in event.get("description", "").lower()
        ]

        if not matches:
            return ToolResult(
                success=True,
                output=f"No events found matching '{query}'"
            )

        output = f"Found {len(matches)} event(s) matching '{query}':\n\n"
        for event in matches:
            start = datetime.fromisoformat(event["start_time"])
            output += f"- [{event['id']}] {event['title']}\n"
            output += f"  Date: {start.strftime('%Y-%m-%d %H:%M')}\n"
            output += "\n"

        return ToolResult(success=True, output=output)

    async def _delete_event(self, event_id: str) -> ToolResult:
        """Delete an event by ID."""
        if not event_id:
            return ToolResult(
                success=False,
                output="",
                error="Event ID is required"
            )

        events = self._load_events()
        original_count = len(events)
        events = [e for e in events if e.get("id") != event_id]

        if len(events) == original_count:
            return ToolResult(
                success=False,
                output="",
                error=f"Event not found: {event_id}"
            )

        self._save_events(events)

        return ToolResult(
            success=True,
            output=f"Event {event_id} deleted successfully"
        )

    async def _get_today_events(self) -> ToolResult:
        """Get events for today."""
        events = self._load_events()
        today = datetime.now().date()

        today_events = []
        for event in events:
            try:
                start = datetime.fromisoformat(event["start_time"])
                if start.date() == today:
                    today_events.append(event)
            except:
                continue

        if not today_events:
            return ToolResult(
                success=True,
                output="No events scheduled for today."
            )

        # Sort by time
        today_events.sort(key=lambda e: e["start_time"])

        output = f"Today's events ({today.strftime('%Y-%m-%d')}):\n\n"
        for event in today_events:
            start = datetime.fromisoformat(event["start_time"])
            output += f"- {start.strftime('%H:%M')} - {event['title']}\n"
            if event.get("description"):
                output += f"  {event['description'][:50]}\n"
            output += "\n"

        return ToolResult(success=True, output=output)

    async def _get_upcoming_events(self, days: int = 7) -> ToolResult:
        """Get upcoming events for the next N days."""
        return await self._list_events(days)

    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parse a datetime string in various formats."""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y/%m/%d %H:%M",
            "%d/%m/%Y %H:%M",
            "%m/%d/%Y %H:%M",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(dt_str)
        except ValueError:
            pass

        raise ValueError(f"Could not parse datetime: {dt_str}")
