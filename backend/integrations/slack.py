"""
Slack Integration - Handles Slack data ingestion and processing
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import asyncio
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from core.config import settings

logger = logging.getLogger(__name__)


class SlackIntegration:
    """Integration for processing Slack data"""

    def __init__(self):
        self.client = None
        if settings.slack_bot_token:
            self.client = AsyncWebClient(token=settings.slack_bot_token)

    async def process_data(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Process Slack data and convert to documents

        Args:
            data: Slack-specific data (channels, messages, etc.)
            metadata: Additional metadata

        Returns:
            List of document dictionaries ready for vector storage
        """
        try:
            documents = []

            # Handle different types of Slack data
            if "messages" in data:
                # Direct message data
                documents.extend(await self._process_messages(data["messages"], metadata))
            elif "channel_id" in data:
                # Fetch messages from a specific channel
                documents.extend(await self._fetch_channel_messages(data["channel_id"], data.get("limit", 100)))
            elif "channels" in data:
                # Fetch messages from multiple channels
                for channel_id in data["channels"]:
                    channel_docs = await self._fetch_channel_messages(channel_id, data.get("limit", 100))
                    documents.extend(channel_docs)
            else:
                logger.warning("Unknown Slack data format")

            return documents

        except Exception as e:
            logger.error(f"Failed to process Slack data: {str(e)}")
            raise

    def _convert_slack_timestamp(self, ts: str) -> str:
        """Convert Slack timestamp to ISO format"""
        try:
            if not ts:
                return datetime.now(timezone.utc).isoformat()

            # Slack timestamps are in format "1234567890.123456"
            timestamp = float(ts)
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.isoformat()
        except (ValueError, TypeError):
            return datetime.now(timezone.utc).isoformat()

    async def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        if not self.client:
            return {"configured": False, "error": "No bot token provided"}

        try:
            # Test API connection
            response = await self.client.auth_test()
            return {
                "configured": True,
                "connected": True,
                "bot_user_id": response.get("user_id"),
                "team": response.get("team")
            }
        except SlackApiError as e:
            return {
                "configured": True,
                "connected": False,
                "error": e.response.get("error", "Unknown error")
            }

    def get_description(self) -> str:
        """Get integration description"""
        return "Slack workspace integration for ingesting messages and conversations"