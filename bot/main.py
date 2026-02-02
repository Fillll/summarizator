"""Main application entry point."""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler as TelegramCommandHandler, MessageHandler, filters

from bot.utils.config import Config
from bot.storage.file_storage import FileStorage
from bot.prompts.manager import PromptManager
from bot.handlers.message_handler import MessageRouter
from bot.handlers.command_handler import CommandHandler


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SummarizatorBot:
    """Main Telegram bot application."""

    def __init__(self, config: Config):
        """Initialize bot.

        Args:
            config: Configuration object
        """
        self.config = config
        self.storage = FileStorage(config.data_dir)
        self.prompt_manager = PromptManager()
        self.message_router = MessageRouter(
            storage=self.storage,
            config=config,
            prompt_manager=self.prompt_manager
        )
        self.command_handler = CommandHandler(storage=self.storage)
        self.app = None

    def start(self):
        """Build and start the bot application."""
        # Build application
        self.app = Application.builder().token(self.config.telegram_token).build()

        # Register command handlers
        self.app.add_handler(
            TelegramCommandHandler("start", self.command_handler.handle_start)
        )
        self.app.add_handler(
            TelegramCommandHandler("help", self.command_handler.handle_help)
        )
        self.app.add_handler(
            TelegramCommandHandler("list", self._handle_list_command)
        )
        self.app.add_handler(
            TelegramCommandHandler("delete", self._handle_delete_command)
        )
        self.app.add_handler(
            TelegramCommandHandler("clear", self._handle_clear_command)
        )
        self.app.add_handler(
            TelegramCommandHandler("stats", self.command_handler.handle_stats)
        )

        # Register message handler (for non-command text messages)
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.message_router.route_message
            )
        )

        # Start bot
        logger.info("Starting bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def _handle_list_command(self, update: Update, context):
        """Wrapper for list command that provides RAG manager."""
        user_id = str(update.effective_user.id)
        rag_manager = self.message_router._get_rag_manager(user_id)
        await self.command_handler.handle_list(update, context, rag_manager)

    async def _handle_delete_command(self, update: Update, context):
        """Wrapper for delete command that provides RAG manager."""
        user_id = str(update.effective_user.id)
        rag_manager = self.message_router._get_rag_manager(user_id)
        await self.command_handler.handle_delete(update, context, rag_manager)

    async def _handle_clear_command(self, update: Update, context):
        """Wrapper for clear command that provides RAG manager."""
        user_id = str(update.effective_user.id)
        rag_manager = self.message_router._get_rag_manager(user_id)
        await self.command_handler.handle_clear(update, context, rag_manager)


def main():
    """Main entry point."""
    try:
        # Load configuration
        config = Config("data/config.json")

        # Create and start bot
        bot = SummarizatorBot(config)
        bot.start()

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please create data/config.json with your API keys")
        return

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    main()
