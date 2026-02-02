"""Message routing handler."""
from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.link_handler import LinkHandler
from bot.handlers.question_handler import QuestionHandler
from bot.rag.rag_manager import RAGManager
from bot.storage.base import BaseStorage
from bot.utils.link_detector import LinkDetector
from bot.utils.config import Config
from bot.prompts.manager import PromptManager


class MessageRouter:
    """Routes messages to appropriate handlers."""

    def __init__(
        self,
        storage: BaseStorage,
        config: Config,
        prompt_manager: PromptManager
    ):
        """Initialize message router.

        Args:
            storage: Storage implementation
            config: Configuration object
            prompt_manager: Prompt manager instance
        """
        self.storage = storage
        self.config = config
        self.prompt_manager = prompt_manager

        # Initialize handlers
        self.link_handler = LinkHandler(storage, config, prompt_manager)
        self.question_handler = QuestionHandler(storage, config)
        self.link_detector = LinkDetector()

        # Cache RAG managers per user
        self._rag_managers = {}

    def _get_rag_manager(self, user_id: str) -> RAGManager:
        """Get or create RAG manager for user.

        Args:
            user_id: User's unique identifier

        Returns:
            RAG manager instance
        """
        if user_id not in self._rag_managers:
            self._rag_managers[user_id] = RAGManager(
                user_id=user_id,
                storage=self.storage,
                config=self.config,
                prompt_manager=self.prompt_manager
            )
        return self._rag_managers[user_id]

    async def route_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Route message to appropriate handler.

        Args:
            update: Telegram update
            context: Telegram context
        """
        if not update.message or not update.message.text:
            return

        message_text = update.message.text
        user_id = str(update.effective_user.id)

        # Get RAG manager for user
        rag_manager = self._get_rag_manager(user_id)

        try:
            # Check if message contains a URL
            url = self.link_detector.extract_url(message_text)

            if url:
                # Handle as link
                await self.link_handler.handle(update, context, url, rag_manager)
            else:
                # Handle as question
                await self.question_handler.handle(update, context, message_text, rag_manager)

        except Exception as e:
            # Catch-all error handler
            error_message = f"Sorry, something went wrong: {str(e)}"
            await update.message.reply_text(error_message)
