"""
MAX API Types

Data types for MAX messenger API.
Designed to be compatible with our bot architecture.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


@dataclass
class User:
    """Represents a MAX user."""
    id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    created_at: datetime | None = None


@dataclass
class Message:
    """Represents a message from MAX."""
    message_id: int
    chat_id: int
    from_user: User
    text: str | None = None
    date: datetime = field(default_factory=datetime.now)
    
    # For compatibility
    @property
    def chat(self):
        """Return chat-like object for compatibility."""
        return type('Chat', (), {'id': self.chat_id})()


@dataclass
class CallbackQuery:
    """Represents a callback query from inline keyboard."""
    callback_query_id: str
    message: Message
    from_user: User
    data: str | None = None


class KeyboardButton:
    """Represents a keyboard button."""
    
    def __init__(self, text: str):
        self.text = text


class InlineKeyboardButton:
    """Represents an inline keyboard button."""
    
    def __init__(
        self,
        text: str,
        callback_data: str | None = None,
        url: str | None = None,
    ):
        self.text = text
        self.callback_data = callback_data
        self.url = url


class InlineKeyboardMarkup:
    """Represents an inline keyboard markup."""
    
    def __init__(self, inline_keyboard: list[list[InlineKeyboardButton]] | None = None):
        self.inline_keyboard = inline_keyboard or []
    
    def add(self, *buttons: InlineKeyboardButton) -> 'InlineKeyboardMarkup':
        """Add a row of buttons to the keyboard."""
        self.inline_keyboard.append(list(buttons))
        return self
    
    def row(self, *buttons: InlineKeyboardButton) -> 'InlineKeyboardMarkup':
        """Add a row of buttons (alias for add)."""
        return self.add(*buttons)
    
    @staticmethod
    def build(*buttons: InlineKeyboardButton) -> 'InlineKeyboardMarkup':
        """Build keyboard with all buttons in one row."""
        markup = InlineKeyboardMarkup()
        markup.add(*buttons)
        return markup


class ReplyKeyboardMarkup:
    """Represents a reply keyboard markup."""
    
    def __init__(self, keyboard: list[list[KeyboardButton]] | None = None, resize_keyboard: bool = True):
        self.keyboard = keyboard or []
        self.resize_keyboard = resize_keyboard
    
    def add(self, *buttons: KeyboardButton) -> 'ReplyKeyboardMarkup':
        """Add a row of buttons to the keyboard."""
        self.keyboard.append(list(buttons))
        return self
    
    def row(self, *buttons: KeyboardButton) -> 'ReplyKeyboardMarkup':
        """Add a row of buttons."""
        return self.add(*buttons)


@dataclass
class Update:
    """Represents an update from MAX API (webhook or polling)."""
    update_id: int
    message: Message | None = None
    callback_query: CallbackQuery | None = None
    
    @property
    def effective_user(self) -> User | None:
        """Get the user who triggered this update."""
        if self.message:
            return self.message.from_user
        if self.callback_query:
            return self.callback_query.from_user
        return None


class ParseMode(Enum):
    """Message parse modes."""
    HTML = "html"
    MARKDOWN = "markdown"
    MARKDOWN_V2 = "markdownv2"
