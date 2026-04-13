"""
MAX Dispatcher

Handles routing of updates to appropriate handlers.
Similar to aiogram's Dispatcher but adapted for maxapi.
"""

import asyncio
import logging
from typing import Callable, Awaitable

from app.bot.max_api import MAXBot
from app.bot.max_api.types import Update, Message, CallbackQuery

logger = logging.getLogger(__name__)


class MAXDispatcher:
    """
    Dispatcher for MAX API.
    
    Routes updates (messages, callbacks) to registered handlers.
    Supports polling mode for development.
    """
    
    def __init__(self) -> None:
        """Initialize dispatcher with empty handler lists."""
        self._message_handlers: list[dict] = []
        self._callback_handlers: list[dict] = []
        self._startup_handlers: list[Callable] = []
        self._shutdown_handlers: list[Callable] = []
        
        logger.info("MAX Dispatcher initialized")
    
    def message_handler(self, commands: list[str] | None = None, text: str | None = None):
        """
        Decorator for registering message handlers.
        
        Args:
            commands: List of commands to handle (e.g., ["start", "help"]).
            text: Exact text to match (optional).
            
        Example:
            @dispatcher.message_handler(commands=["start"])
            async def start_handler(update: Update):
                ...
        """
        def decorator(handler: Callable[[Update], Awaitable[None]]):
            self._message_handlers.append({
                "handler": handler,
                "commands": commands or [],
                "text": text,
            })
            return handler
        return decorator
    
    def callback_query_handler(self, filter: Callable[[str], bool] | None = None):
        """
        Decorator for registering callback query handlers.
        
        Args:
            filter: Function that takes callback data and returns True if handler should be called.
            
        Example:
            @dispatcher.callback_query_handler(lambda c: c.data.startswith("menu_"))
            async def menu_callback_handler(update: Update):
                ...
        """
        def decorator(handler: Callable[[Update], Awaitable[None]]):
            self._callback_handlers.append({
                "handler": handler,
                "filter": filter,
            })
            return handler
        return decorator
    
    def on_startup(self, handler: Callable[[], Awaitable[None]]):
        """Register startup handler."""
        self._startup_handlers.append(handler)
    
    def on_shutdown(self, handler: Callable[[], Awaitable[None]]):
        """Register shutdown handler."""
        self._shutdown_handlers.append(handler)
    
    async def process_update(self, update: Update, bot: MAXBot) -> None:
        """
        Process a single update and route to appropriate handler.
        
        Args:
            update: Update object from MAX API.
            bot: MAX Bot instance.
        """
        # Check if it's a message
        if update.message:
            await self._process_message(update)
        
        # Check if it's a callback query
        elif update.callback_query:
            await self._process_callback(update)
    
    async def _process_message(self, update: Update) -> None:
        """Process message update."""
        message = update.message
        text = message.text or ""
        
        # Extract command
        if text.startswith("/"):
            command = text.split()[0][1:].lower()  # Remove '/'
        else:
            command = None
        
        # Find matching handler
        for handler_info in self._message_handlers:
            # Check command match
            if command and command in handler_info["commands"]:
                await handler_info["handler"](update)
                return
            
            # Check exact text match
            if handler_info["text"] and text == handler_info["text"]:
                await handler_info["handler"](update)
                return
    
    async def _process_callback(self, update: Update) -> None:
        """Process callback query update."""
        callback_data = update.callback_query.data
        
        # Find matching handler
        for handler_info in self._callback_handlers:
            filter_func = handler_info.get("filter")
            
            if filter_func is None or filter_func(callback_data):
                await handler_info["handler"](update)
                return
    
    async def start_polling(
        self,
        bot: MAXBot,
        polling_interval: int = 1,
    ) -> None:
        """
        Start polling for updates.
        
        Args:
            bot: MAX Bot instance.
            polling_interval: Seconds between polls.
        """
        logger.info("Starting polling loop...")
        
        # Run startup handlers
        for handler in self._startup_handlers:
            try:
                await handler()
            except Exception as e:
                logger.error(f"Error in startup handler: {e}")
        
        try:
            offset = None
            
            while True:
                try:
                    # Get updates from MAX API
                    updates = await bot.get_updates(offset=offset, limit=100, timeout=30)
                    
                    for update_data in updates:
                        # Convert to Update object
                        update = self._convert_update(update_data)
                        
                        if update:
                            await self.process_update(update, bot)
                            offset = update.update_id + 1
                    
                    # Small delay to prevent tight loop
                    await asyncio.sleep(polling_interval)
                    
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
        
        except KeyboardInterrupt:
            logger.info("Polling stopped by user")
        
        finally:
            # Run shutdown handlers
            for handler in self._shutdown_handlers:
                try:
                    await handler()
                except Exception as e:
                    logger.error(f"Error in shutdown handler: {e}")
    
    def _convert_update(self, update_data: dict) -> Update | None:
        """
        Convert raw update data to Update object.
        
        Args:
            update_data: Raw update data from MAX API.
            
        Returns:
            Update object or None if invalid.
        """
        try:
            update_id = update_data.get("update_id")
            
            # Check for message
            if "message" in update_data:
                message_data = update_data["message"]
                message = Message(**message_data)
                return Update(
                    update_id=update_id,
                    event_type="message",
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    message=message,
                )
            
            # Check for callback query
            elif "callback_query" in update_data:
                callback_data = update_data["callback_query"]
                callback = CallbackQuery(**callback_data)
                return Update(
                    update_id=update_id,
                    event_type="callback_query",
                    chat_id=callback.message.chat.id if callback.message else None,
                    user_id=callback.from_user.id,
                    callback_query=callback,
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to convert update: {e}")
            return None
