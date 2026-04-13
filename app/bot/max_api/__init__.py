"""
MAX API Wrapper Module

This module provides a wrapper around the MAX messenger API.
Since MAX API documentation may vary, this wrapper is designed to be:
1. Easy to adapt to the actual MAX API
2. Compatible with our bot architecture
3. Similar to aiogram's interface for easier migration

TODO: Replace with actual MAX API implementation when documentation is available
"""

from .bot import MAXBot
from .types import (
    Message,
    User,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update,
)

__all__ = [
    "MAXBot",
    "Message",
    "User",
    "CallbackQuery",
    "InlineKeyboardMarkup",
    "InlineKeyboardButton",
    "ReplyKeyboardMarkup",
    "KeyboardButton",
    "Update",
]
