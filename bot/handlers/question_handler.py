"""Question/RAG query handler."""
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from bot.rag.rag_manager import RAGManager
from bot.storage.base import BaseStorage
from bot.storage.models import Message
from bot.utils.config import Config


class QuestionHandler:
    """Handles question/RAG query messages."""

    def __init__(self, storage: BaseStorage, config: Config):
        """Initialize question handler.

        Args:
            storage: Storage implementation
            config: Configuration object
        """
        self.storage = storage
        self.config = config

    async def handle(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        question: str,
        rag_manager: RAGManager
    ):
        """Handle question message.

        Args:
            update: Telegram update
            context: Telegram context
            question: User's question
            rag_manager: RAG manager for user
        """
        user_id = str(update.effective_user.id)
        message_id = str(update.message.message_id)

        # Send thinking status
        status_msg = await update.message.reply_text("Thinking...")

        try:
            # 1. Load conversation history
            conversation_history = await self.storage.get_messages(
                user_id,
                limit=self.config.conversation_history_limit
            )

            # 2. Query RAG
            answer = await rag_manager.query(
                question=question,
                conversation_history=conversation_history,
                n_results=3  # Retrieve top 3 relevant documents
            )

            # 3. Send answer
            await status_msg.delete()
            answer_msg = await update.message.reply_text(answer)

            # 4. Save messages
            # Save user question
            user_message = Message(
                message_id=message_id,
                user_id=user_id,
                timestamp=datetime.fromtimestamp(update.message.date.timestamp()),
                content=question,
                is_bot=False
            )
            await self.storage.save_message(user_id, user_message)

            # Save bot answer
            bot_message = Message(
                message_id=str(answer_msg.message_id),
                user_id=user_id,
                timestamp=datetime.now(),
                content=answer,
                is_bot=True
            )
            await self.storage.save_message(user_id, bot_message)

        except Exception as e:
            await status_msg.delete()
            error_message = f"Sorry, I encountered an error: {str(e)}"
            await update.message.reply_text(error_message)

            # Save user message even on error
            user_message = Message(
                message_id=message_id,
                user_id=user_id,
                timestamp=datetime.fromtimestamp(update.message.date.timestamp()),
                content=question,
                is_bot=False
            )
            await self.storage.save_message(user_id, user_message)
