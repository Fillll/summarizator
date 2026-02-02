"""Command handlers for the bot."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from bot.rag.rag_manager import RAGManager
from bot.storage.base import BaseStorage
from bot.utils.text_utils import format_document_list


class CommandHandler:
    """Handles bot commands."""

    def __init__(self, storage: BaseStorage):
        """Initialize command handler.

        Args:
            storage: Storage implementation
        """
        self.storage = storage

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """
Welcome to the Summarizator Bot!

I can help you:
- Summarize web pages, YouTube videos, PDFs, and GitHub repositories
- Store summaries in your personal knowledge base
- Answer questions based on your saved documents

How to use:
1. Send me a link to get a summary
2. Ask questions about your saved documents
3. Use commands to manage your collection:
   /help - Show this help message
   /list - List all your saved documents
   /delete <doc_id> - Delete a specific document
   /clear - Clear all your documents
   /stats - Show your statistics

Let's get started! Send me a link or ask a question.
"""
        await update.message.reply_text(welcome_message)

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """
Available commands:
/start - Welcome message and introduction
/help - Show this help message
/list - List all documents in your collection
/delete <doc_id> - Delete a specific document (use doc number from /list)
/clear - Clear all documents from your collection
/stats - Show your statistics (# docs, # messages, storage size)

How to use the bot:
1. Send a link (web page, YouTube, PDF, or GitHub) to get a summary
2. The summary will be added to your personal knowledge base
3. Ask questions about your saved documents anytime
4. I'll use your conversation history and relevant documents to answer

Supported link types:
- Web pages (any HTTP/HTTPS URL)
- YouTube videos (with closed captions)
- PDF documents
- GitHub repositories (README files)
"""
        await update.message.reply_text(help_message)

    async def handle_list(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        rag_manager: RAGManager
    ):
        """Handle /list command."""
        documents = await rag_manager.get_document_list()

        if not documents:
            await update.message.reply_text("You don't have any documents yet. Send me a link to get started!")
            return

        # Format document list with numbered items
        lines = ["Your document collection:\n"]
        for i, doc in enumerate(documents, 1):
            lines.append(f"{i}. [{doc.title}]({doc.url})")
            lines.append(f"   Type: {doc.content_type} | Added: {doc.added_at.strftime('%Y-%m-%d %H:%M')}\n")

        message = "\n".join(lines)
        try:
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except BadRequest:
            # Fallback to plain text if markdown fails
            await update.message.reply_text(message)

    async def handle_delete(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        rag_manager: RAGManager
    ):
        """Handle /delete command."""
        if not context.args or len(context.args) == 0:
            await update.message.reply_text("Usage: /delete <number>\nUse /list to see document numbers.")
            return

        try:
            doc_number = int(context.args[0])
            documents = await rag_manager.get_document_list()

            if doc_number < 1 or doc_number > len(documents):
                await update.message.reply_text(f"Invalid document number. You have {len(documents)} documents. Use /list to see them.")
                return

            doc = documents[doc_number - 1]
            success = await rag_manager.delete_document(doc.doc_id)

            if success:
                await update.message.reply_text(f"Deleted: {doc.title}")
            else:
                await update.message.reply_text("Failed to delete document.")

        except ValueError:
            await update.message.reply_text("Invalid number. Usage: /delete <number>")

    async def handle_clear(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        rag_manager: RAGManager
    ):
        """Handle /clear command."""
        documents = await rag_manager.get_document_list()

        if not documents:
            await update.message.reply_text("You don't have any documents to clear.")
            return

        # Simple confirmation (in a production bot, you might want a proper confirmation dialog)
        count = await rag_manager.clear_all_documents()
        await update.message.reply_text(f"Cleared {count} document(s) from your collection.")

    async def handle_stats(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /stats command."""
        user_id = str(update.effective_user.id)
        stats = await self.storage.get_user_stats(user_id)

        stats_message = f"""
Your Statistics:

Documents: {stats['num_documents']}
Messages: {stats['num_messages']}
Storage: {stats['storage_size_mb']} MB
"""
        await update.message.reply_text(stats_message)
