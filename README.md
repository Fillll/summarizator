# Summarizator - Telegram RAG Bot

A modular Telegram bot that processes links (web pages, YouTube videos, PDFs, GitHub repositories), summarizes them, stores them in a per-user RAG (Retrieval-Augmented Generation) knowledge base, and answers questions using conversation context.

## Features

- **Multi-format Content Processing**: Supports web pages, YouTube videos, PDFs, and GitHub repositories
- **Automatic Summarization**: Generates concise summaries using OpenAI GPT-4
- **Personal Knowledge Base**: Each user gets their own RAG index with vector embeddings
- **Conversational Q&A**: Ask questions about your saved documents with conversation history context
- **Modular Architecture**: Easy to extend with new content types and storage backends
- **Full Command Suite**: Manage your document collection with intuitive commands

## Supported Content Types

- **Web Pages**: Any HTTP/HTTPS URL (HTML converted to markdown)
- **YouTube Videos**: Videos with closed captions (transcript extraction)
- **PDF Documents**: PDF files (text extraction)
- **GitHub Repositories**: Repository README files

## Installation

### Prerequisites

- Python 3.9 or higher
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
- OpenAI API Key (get from [OpenAI Platform](https://platform.openai.com/api-keys))

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd summarizator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the bot**

   Copy the example config and add your API keys:
   ```bash
   cp data/config.example.json data/config.json
   # Edit data/config.json with your API keys
   ```

   Required configuration:
   - `telegram_token`: Get from [@BotFather](https://t.me/botfather) on Telegram
   - `openai_api_key`: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

   Alternatively, you can use environment variables (create a `.env` file):
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. **Run the bot**
   ```bash
   python -m bot.main
   ```

## Usage

### Basic Workflow

1. **Send a link** to the bot
   - Bot extracts and converts content to markdown
   - Generates a summary (without RAG retrieval)
   - Adds document to your personal knowledge base
   - Sends you the summary and updated document list

2. **Ask questions** about your saved documents
   - Bot retrieves relevant documents from your RAG index
   - Uses conversation history for context
   - Generates answers based on retrieved information

### Commands

- `/start` - Welcome message and introduction
- `/help` - Show help and usage instructions
- `/list` - List all documents in your collection
- `/delete <number>` - Delete a specific document (use number from /list)
- `/clear` - Clear all documents from your collection
- `/stats` - Show your statistics (documents, messages, storage size)

### Examples

**Example 1: Summarize a web article**
```
You: https://example.com/article-about-ai
Bot: Processing your link...
Bot: [Summary of the article]
Bot: Your document collection:
     1. Article About AI (https://example.com/article-about-ai)
```

**Example 2: Summarize a YouTube video**
```
You: https://youtube.com/watch?v=abc123
Bot: Processing your link...
Bot: [Summary of video transcript]
Bot: Your document collection:
     1. Awesome Video Title (https://youtube.com/watch?v=abc123)
```

**Example 3: Ask a question**
```
You: What did the article say about machine learning?
Bot: Thinking...
Bot: According to the article you saved, machine learning is...
```

## Project Structure

```
summarizator/
├── bot/
│   ├── handlers/           # Message and command handlers
│   ├── content_processors/ # Content extraction (web, YouTube, PDF, GitHub)
│   ├── rag/               # RAG operations and embedding storage
│   ├── storage/           # Storage abstraction layer
│   ├── prompts/           # Prompt templates for different content types
│   ├── utils/             # Utilities (config, link detection, text formatting)
│   ├── main.py            # Application entry point
│   └── exceptions.py      # Custom exceptions
├── data/
│   ├── config.json        # Configuration file
│   └── {user_id}/         # Per-user data folders (created at runtime)
│       ├── chroma_db/     # User's vector database
│       ├── messages.jsonl # Conversation history
│       └── documents.json # Document metadata
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Architecture

### Modular Design

- **Content Processors**: Each content type (web, YouTube, PDF, GitHub) has its own processor implementing a common interface
- **Storage Abstraction**: File-based storage with abstract interface for easy database migration
- **Prompt Management**: External prompt templates for easy modification
- **Per-User RAG**: Separate vector database for each user (Chroma DB)

### Key Components

1. **Content Processors** (`bot/content_processors/`): Extract and convert content to markdown
2. **RAG Manager** (`bot/rag/rag_manager.py`): Manages document addition and querying
3. **Embedding Store** (`bot/rag/embedding_store.py`): Manages per-user Chroma DB
4. **Storage Layer** (`bot/storage/`): Handles file I/O with abstraction for future DB migration
5. **Message Router** (`bot/handlers/message_handler.py`): Routes messages to appropriate handlers

## Configuration

### config.json Options

- `telegram_token`: Your Telegram bot token
- `openai_api_key`: Your OpenAI API key
- `data_dir`: Directory for user data storage (default: "data")
- `conversation_history_limit`: Number of recent messages to use as context (default: 20)
- `openai_model`: OpenAI model for summaries and answers (default: "gpt-4-turbo-preview")
- `embedding_model`: OpenAI embedding model (default: "text-embedding-3-small")
- `max_document_preview_length`: Maximum length for document previews (default: 200)

### Customizing Prompts

Prompt templates are stored in `bot/prompts/`:
- `summarization/web.txt` - Web page summarization
- `summarization/youtube.txt` - YouTube video summarization
- `summarization/pdf.txt` - PDF document summarization
- `summarization/github.txt` - GitHub repository summarization
- `rag/answer.txt` - RAG answer generation

Edit these files to customize how the bot summarizes content and answers questions.

## Development

### Adding a New Content Type

1. Create a new processor in `bot/content_processors/`:
   ```python
   class MyProcessor(ContentProcessor):
       async def extract_content(self, url: str) -> str:
           # Extract and return markdown content
           pass

       async def get_document_name(self, url: str, content: str) -> str:
           # Return document name
           pass

       def get_prompt_template_name(self) -> str:
           return "my_content_type"
   ```

2. Add URL classification in `bot/utils/link_detector.py`

3. Register processor in `bot/handlers/link_handler.py`

4. Create prompt template in `bot/prompts/summarization/my_content_type.txt`

### Migrating to Database

To migrate from file-based storage to a database:

1. Implement a new storage class (e.g., `PostgresStorage`) extending `BaseStorage`
2. Update `bot/main.py` to use your new storage implementation
3. All handlers and managers use the `BaseStorage` interface, so no other changes needed

## Troubleshooting

### Bot doesn't respond
- Check that `data/config.json` has correct API keys
- Ensure the bot is running (`python -m bot.main`)
- Check logs for errors

### YouTube videos fail
- Ensure the video has closed captions available
- Check that youtube-transcript-api is installed

### PDF extraction fails
- Some PDFs (scanned images) may not extract well
- Try using a different PDF with text content

### Out of memory
- Adjust `max_document_preview_length` in config.json
- Clear old conversations and documents

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [python-telegram-bot](https://python-telegram-bot.org/)
- Uses [OpenAI GPT-4](https://openai.com/) for summarization and Q&A
- Vector storage with [Chroma DB](https://www.trychroma.com/)
- Content extraction libraries: BeautifulSoup, html2text, youtube-transcript-api, pypdf
