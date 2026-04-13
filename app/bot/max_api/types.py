"""
MAX API Types

Re-exports types from maxapi library and adds custom types for our application.
This provides a unified interface while using the official maxapi types.

Documentation:
- MAX API: https://dev.max.ru/docs-api
- maxapi types: https://love-apples.github.io/maxapi/
"""

# Re-export types from maxapi library
from maxapi.types import (
    BotStarted,
    CallbackQuery,
    InlineKeyboardButton,
    Message,
    MessageCreated,
    User,
)

# Import keyboard attachment for building inline keyboards
from maxapi.types import InlineKeyboardAttachment

# Local custom types
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


@dataclass
class Update:
    """
    Represents an update from MAX API.
    Wrapper for different event types.
    """
    update_id: int
    event_type: str  # 'message', 'callback', 'bot_started', etc.
    chat_id: int | None = None
    user_id: int | None = None
    message: Message | None = None
    callback_query: CallbackQuery | None = None
    
    @property
    def effective_user_id(self) -> int | None:
        """Get the user ID who triggered this update."""
        return self.user_id
    
    @property
    def effective_chat_id(self) -> int | None:
        """Get the chat ID of this update."""
        return self.chat_id


@dataclass 
class InlineKeyboardMarkup:
    """
    Inline keyboard markup compatible with MAX API.
    
    MAX API supports up to 210 buttons in 30 rows (up to 7 buttons per row).
    """
    
    def __init__(self, inline_keyboard: list[list[dict]] | None = None):
        """
        Initialize inline keyboard.
        
        Args:
            inline_keyboard: List of button rows. Each button is a dict with:
                - type: 'callback', 'link', 'message', 'clipboard', etc.
                - text: Button text
                - payload: Button payload (for callback/message/clipboard)
                - url: URL (for link buttons)
        """
        self.inline_keyboard = inline_keyboard or []
    
    def add(self, *buttons: dict) -> 'InlineKeyboardMarkup':
        """
        Add a row of buttons to the keyboard.
        
        Args:
            buttons: Button dicts to add in this row.
            
        Returns:
            Self for chaining.
        """
        self.inline_keyboard.append(list(buttons))
        return self
    
    def row(self, *buttons: dict) -> 'InlineKeyboardMarkup':
        """Add a row of buttons (alias for add)."""
        return self.add(*buttons)
    
    @staticmethod
    def callback_button(text: str, payload: str) -> dict:
        """
        Create a callback button.
        
        Args:
            text: Button text.
            payload: Callback data (sent to bot when pressed).
            
        Returns:
            Button dict.
        """
        return {
            "type": "callback",
            "text": text,
            "payload": payload,
        }
    
    @staticmethod
    def link_button(text: str, url: str) -> dict:
        """
        Create a link button.
        
        Args:
            text: Button text.
            url: URL to open (max 2048 characters).
            
        Returns:
            Button dict.
        """
        return {
            "type": "link",
            "text": text,
            "payload": url,
        }
    
    @staticmethod
    def message_button(text: str, payload: str) -> dict:
        """
        Create a message button (sends text to bot).
        
        Args:
            text: Button text.
            payload: Message to send to bot.
            
        Returns:
            Button dict.
        """
        return {
            "type": "message",
            "text": text,
            "payload": payload,
        }
    
    @staticmethod
    def clipboard_button(text: str, payload: str) -> dict:
        """
        Create a clipboard button (copies text to clipboard).
        
        Args:
            text: Button text.
            payload: Text to copy to clipboard.
            
        Returns:
            Button dict.
        """
        return {
            "type": "clipboard",
            "text": text,
            "payload": payload,
        }
    
    def to_attachment(self) -> InlineKeyboardAttachment:
        """Convert to InlineKeyboardAttachment for sending."""
        return InlineKeyboardAttachment(buttons=self.inline_keyboard)


class ReplyKeyboardMarkup:
    """
    Reply keyboard markup (legacy, not recommended for MAX).
    
    MAX primarily uses inline keyboards. This is kept for compatibility.
    """
    
    def __init__(self, keyboard: list | None = None, resize_keyboard: bool = True):
        self.keyboard = keyboard or []
        self.resize_keyboard = resize_keyboard
    
    def add(self, *buttons) -> 'ReplyKeyboardMarkup':
        """Add buttons (not implemented for MAX)."""
        raise NotImplementedError("ReplyKeyboardMarkup is not supported in MAX API. Use InlineKeyboardMarkup instead.")


class ParseMode(Enum):
    """Message parse modes supported by MAX."""
    HTML = "html"
    MARKDOWN = "markdown"
    # Note: MAX doesn't have markdownv2, just markdown


__all__ = [
    # From maxapi
    "BotStarted",
    "CallbackQuery",
    "InlineKeyboardButton",
    "Message",
    "MessageCreated",
    "User",
    "InlineKeyboardAttachment",
    # Custom
    "Update",
    "InlineKeyboardMarkup",
    "ReplyKeyboardMarkup",
    "ParseMode",
]
