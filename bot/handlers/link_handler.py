"""Link processing handler."""
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from openai import AsyncOpenAI

from bot.rag.rag_manager import RAGManager
from bot.storage.base import BaseStorage
from bot.storage.models import Message
from bot.content_processors.web_processor import WebProcessor
from bot.content_processors.youtube_processor import YouTubeProcessor
from bot.content_processors.pdf_processor import PDFProcessor
from bot.content_processors.github_processor import GitHubProcessor
from bot.prompts.manager import PromptManager
from bot.utils.link_detector import LinkDetector
from bot.utils.config import Config
from bot.utils.text_utils import format_document_list


class LinkHandler:
    """Handles link processing messages."""

    def __init__(
        self,
        storage: BaseStorage,
        config: Config,
        prompt_manager: PromptManager
    ):
        """Initialize link handler.

        Args:
            storage: Storage implementation
            config: Configuration object
            prompt_manager: Prompt manager instance
        """
        self.storage = storage
        self.config = config
        self.prompt_manager = prompt_manager
        self.openai_client = AsyncOpenAI(api_key=config.openai_api_key)

        # Initialize content processors
        self.processors = {
            'web': WebProcessor(),
            'youtube': YouTubeProcessor(),
            'pdf': PDFProcessor(),
            'github': GitHubProcessor()
        }

    async def handle(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        url: str,
        rag_manager: RAGManager
    ):
        """Handle link message.

        Args:
            update: Telegram update
            context: Telegram context
            url: Extracted URL
            rag_manager: RAG manager for user
        """
        user_id = str(update.effective_user.id)
        message_id = str(update.message.message_id)

        # Send processing status
        status_msg = await update.message.reply_text("Processing your link...")

        try:
            # 1. Classify URL type
            content_type = LinkDetector.classify_url(url)

            # 2. Get appropriate processor
            processor = self.processors[content_type]

            # 3. Extract content
            await status_msg.edit_text(f"Extracting content from {content_type} link...")
            content = await processor.extract_content(url)

            # 4. Get document name
            doc_name = await processor.get_document_name(url, content)

            # 5. Generate summary
            await status_msg.edit_text("Generating summary...")
            summary = await self._generate_summary(content, content_type, processor)

            # 6. Send summary to user
            await status_msg.delete()
            summary_text = f"**Summary of {doc_name}:**\n\n{summary}"
            try:
                summary_msg = await update.message.reply_text(
                    summary_text,
                    parse_mode='Markdown'
                )
            except BadRequest:
                # Fallback to plain text if markdown fails
                summary_msg = await update.message.reply_text(summary_text)

            # 7. Add document to RAG
            await update.message.reply_text("Adding to your knowledge base...")
            document = await rag_manager.add_document(
                url=url,
                content=content,
                title=doc_name,
                content_type=content_type
            )

            # 8. Get and send document list
            documents = await rag_manager.get_document_list()
            doc_list_text = format_document_list(documents)
            try:
                await update.message.reply_text(
                    doc_list_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except BadRequest:
                # Fallback to plain text if markdown fails
                await update.message.reply_text(doc_list_text)

            # 9. Save messages to storage
            # Save user message
            user_message = Message(
                message_id=message_id,
                user_id=user_id,
                timestamp=datetime.fromtimestamp(update.message.date.timestamp()),
                content=update.message.text,
                is_bot=False
            )
            await self.storage.save_message(user_id, user_message)

            # Save bot summary message
            bot_message = Message(
                message_id=str(summary_msg.message_id),
                user_id=user_id,
                timestamp=datetime.now(),
                content=f"Summary of {doc_name}: {summary}",
                is_bot=True,
                metadata={'doc_id': document.doc_id, 'url': url}
            )
            await self.storage.save_message(user_id, bot_message)

        except Exception as e:
            # Error handling - don't add to RAG if extraction fails
            await status_msg.delete()
            error_message = f"Sorry, I couldn't process this link. Error: {str(e)}"
            await update.message.reply_text(error_message)

            # Save user message even on error
            user_message = Message(
                message_id=message_id,
                user_id=user_id,
                timestamp=datetime.fromtimestamp(update.message.date.timestamp()),
                content=update.message.text,
                is_bot=False
            )
            await self.storage.save_message(user_id, user_message)

    async def _generate_summary(self, content: str, content_type: str, processor) -> str:
        """Generate summary using OpenAI.

        Args:
            content: Content to summarize
            content_type: Type of content
            processor: Content processor instance

        Returns:
            Generated summary
        """
        # Get prompt template
        prompt_template = self.prompt_manager.get_summarization_prompt(content_type)

        # Fill in template (truncate content if too long)
        max_content_length = 15000  # Reasonable limit for GPT-4
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[Content truncated...]"

        # Format prompt based on content type
        if content_type == "youtube":
            # For YouTube videos, get duration
            duration = "Unknown"
            from bot.content_processors.youtube_processor import YouTubeProcessor
            if isinstance(processor, YouTubeProcessor):
                duration = processor.get_video_duration()
            prompt = prompt_template.format(content=content, duration=duration)
        else:
            # For other content types, only use content
            prompt = prompt_template.format(content=content)

        # Call OpenAI API
        response = await self.openai_client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content
