"""
MAX Bot Wrapper

Integration layer for maxapi library.
This module provides compatibility with our architecture while using
the official maxapi library for MAX messenger API.

Documentation:
- MAX API: https://dev.max.ru/docs-api
- maxapi library: https://github.com/love-apples/maxapi
"""

import logging
from typing import Any

from maxapi import Bot as MAXAPIClient
from maxapi.types import InlineKeyboardAttachment, Message

from .types import (
    InlineKeyboardMarkup,
    ParseMode,
    ReplyKeyboardMarkup,
)

logger = logging.getLogger(__name__)


class MAXBot:
    """
    MAX Bot wrapper around maxapi library.
    
    This class provides a familiar interface similar to aiogram's Bot class
    while using the official maxapi library underneath.
    """
    
    def __init__(
        self,
        token: str,
        base_url: str = "https://platform-api.max.ru",
    ):
        """
        Initialize MAX Bot.
        
        Args:
            token: Bot authentication token from MAX.
            base_url: MAX API base URL (default: platform-api.max.ru).
        """
        self.token = token
        self.base_url = base_url
        self._client = MAXAPIClient(token=token)
        
        logger.info("MAX Bot initialized with maxapi library")
    
    @property
    def client(self) -> MAXAPIClient:
        """Get underlying maxapi client for direct access."""
        return self._client
    
    async def get_me(self) -> dict[str, Any]:
        """
        Get bot information.
        
        Returns:
            Dictionary with bot information:
            - user_id: int
            - name: str
            - username: str
            - is_bot: bool
            - last_activity_time: int
        """
        try:
            me = await self._client.get_me()
            logger.debug(f"Bot info retrieved: {me.username}")
            return me
        except Exception as e:
            logger.error(f"Failed to get bot info: {e}")
            raise
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: ParseMode | None = None,
        reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
        disable_web_page_preview: bool = True,
    ) -> Message:
        """
        Send a message to a chat.
        
        Args:
            chat_id: Target chat ID.
            text: Message text (supports HTML/Markdown formatting).
            parse_mode: Message parse mode (HTML or Markdown).
            reply_markup: Keyboard markup.
            disable_web_page_preview: Disable link previews.
            
        Returns:
            Message object from maxapi.
        """
        try:
            # Prepare format
            format_mode = None
            if parse_mode == ParseMode.HTML:
                format_mode = "html"
            elif parse_mode in (ParseMode.MARKDOWN, ParseMode.MARKDOWN_V2):
                format_mode = "markdown"
            
            # Build attachments for inline keyboard
            attachments = []
            if reply_markup and isinstance(reply_markup, InlineKeyboardMarkup):
                keyboard_attachment = InlineKeyboardAttachment(
                    buttons=reply_markup.inline_keyboard
                )
                attachments.append(keyboard_attachment)
            
            # Send message using maxapi
            message = await self._client.send_message(
                chat_id=chat_id,
                text=text,
                format=format_mode,
                attachments=attachments if attachments else None,
            )
            
            logger.debug(f"Message sent to {chat_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            raise
    
    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: ParseMode | None = None,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> Message:
        """
        Edit a message text.
        
        Args:
            chat_id: Chat ID.
            message_id: Message ID to edit.
            text: New message text.
            parse_mode: Message parse mode.
            reply_markup: New keyboard markup.
            
        Returns:
            Updated Message object.
        """
        try:
            # Prepare format
            format_mode = None
            if parse_mode == ParseMode.HTML:
                format_mode = "html"
            elif parse_mode in (ParseMode.MARKDOWN, ParseMode.MARKDOWN_V2):
                format_mode = "markdown"
            
            # Build attachments
            attachments = []
            if reply_markup:
                keyboard_attachment = InlineKeyboardAttachment(
                    buttons=reply_markup.inline_keyboard
                )
                attachments.append(keyboard_attachment)
            
            # Edit message
            message = await self._client.edit_message(
                message_id=message_id,
                text=text,
                format=format_mode,
                attachments=attachments if attachments else None,
            )
            
            logger.debug(f"Message {message_id} edited")
            return message
            
        except Exception as e:
            logger.error(f"Failed to edit message {message_id}: {e}")
            raise
    
    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        """
        Delete a message.
        
        Args:
            chat_id: Chat ID.
            message_id: Message ID to delete.
            
        Returns:
            True if deleted successfully.
        """
        try:
            await self._client.delete_message(message_id=message_id)
            logger.debug(f"Message {message_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            return False
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        show_alert: bool = False,
    ) -> bool:
        """
        Answer a callback query.
        
        Args:
            callback_query_id: Callback query ID.
            text: Answer text (optional).
            show_alert: Show alert popup.
            
        Returns:
            True if successful.
        """
        try:
            await self._client.answer_callback(
                callback_id=callback_query_id,
                text=text,
                show_alert=show_alert,
            )
            logger.debug(f"Callback query {callback_query_id} answered")
            return True
        except Exception as e:
            logger.error(f"Failed to answer callback {callback_query_id}: {e}")
            return False
    
    async def set_webhook(self, url: str) -> bool:
        """
        Set webhook for receiving updates.
        
        Args:
            url: Webhook URL (must be HTTPS).
            
        Returns:
            True if successful.
        """
        try:
            await self._client.set_webhook(url=url)
            logger.info(f"Webhook set to: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return False
    
    async def delete_webhook(self) -> bool:
        """
        Delete webhook.
        
        Returns:
            True if successful.
        """
        try:
            await self._client.delete_webhook()
            logger.info("Webhook deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False
    
    async def get_webhook_info(self) -> dict[str, Any]:
        """
        Get webhook information.
        
        Returns:
            Dictionary with webhook info.
        """
        try:
            info = await self._client.get_webhook_info()
            return info
        except Exception as e:
            logger.error(f"Failed to get webhook info: {e}")
            return {"url": "", "has_custom_certificate": False, "pending_update_count": 0}
    
    async def close(self):
        """Close bot session."""
        try:
            await self._client.close()
            logger.info("MAX Bot session closed")
        except Exception as e:
            logger.error(f"Error closing bot session: {e}")
    
    async def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 30,
    ) -> list[dict]:
        """
        Get updates from MAX API (polling mode).
        
        Args:
            offset: ID of first update to return.
            limit: Maximum number of updates to retrieve.
            timeout: Timeout in seconds for long polling.
            
        Returns:
            List of update dictionaries.
        """
        try:
            params = {
                "offset": offset,
                "limit": limit,
                "timeout": timeout,
            }
            
            response = await self._client.get_updates(**params)
            
            # Convert response to list of dicts
            if isinstance(response, list):
                return response
            elif hasattr(response, '__iter__'):
                return [update.__dict__ if hasattr(update, '__dict__') else update for update in response]
            else:
                logger.warning(f"Unexpected response format from get_updates: {type(response)}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get updates: {e}")
            return []
