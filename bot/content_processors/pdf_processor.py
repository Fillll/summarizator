"""PDF content processor."""
import os
import tempfile
from pathlib import Path
import aiohttp
import aiofiles
from pypdf import PdfReader
from bot.content_processors.base import ContentProcessor


class PDFProcessor(ContentProcessor):
    """Processor for PDF documents."""

    async def extract_content(self, url: str) -> str:
        """Extract text from PDF and convert to markdown.

        Args:
            url: The PDF URL

        Returns:
            Markdown-formatted content

        Raises:
            Exception: If content extraction fails
        """
        # Download PDF to temporary file
        temp_file = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    response.raise_for_status()
                    content = await response.read()

            # Write to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                temp_file = tmp.name
                tmp.write(content)

            # Extract text using pypdf
            reader = PdfReader(temp_file)
            text_parts = []

            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"## Page {page_num}\n\n{text.strip()}")

            if not text_parts:
                raise Exception("No text could be extracted from PDF")

            return '\n\n'.join(text_parts)

        except Exception as e:
            raise Exception(f"Failed to extract PDF content: {str(e)}")

        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

    async def get_document_name(self, url: str, content: str) -> str:
        """Generate short document name from PDF filename or first heading.

        Args:
            url: The source URL
            content: The extracted content

        Returns:
            Short, readable document name
        """
        # Try to extract filename from URL
        from urllib.parse import urlparse, unquote
        parsed = urlparse(url)
        path = Path(unquote(parsed.path))
        filename = path.stem  # Get filename without extension

        if filename and filename != 'download':
            # Clean up filename
            name = filename.replace('_', ' ').replace('-', ' ').title()
            if len(name) > 60:
                name = name[:57] + "..."
            return name

        # Try to extract first heading from content
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Use first non-empty, non-heading line
                if len(line) > 60:
                    line = line[:57] + "..."
                return line

        return "PDF Document"

    def get_prompt_template_name(self) -> str:
        """Return name of prompt template to use.

        Returns:
            'pdf'
        """
        return "pdf"
