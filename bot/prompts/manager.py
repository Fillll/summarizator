"""Prompt template manager."""
from pathlib import Path
from typing import Dict


class PromptManager:
    """Loads and manages prompt templates."""

    def __init__(self, prompts_dir: str = "bot/prompts"):
        """Initialize prompt manager.

        Args:
            prompts_dir: Directory containing prompt templates
        """
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}

    def get_summarization_prompt(self, content_type: str) -> str:
        """Get summarization prompt for content type.

        Args:
            content_type: Type of content (web, youtube, pdf, github)

        Returns:
            Prompt template string
        """
        return self._load_prompt(f"summarization/{content_type}.txt")

    def get_rag_prompt(self) -> str:
        """Get RAG answer generation prompt.

        Returns:
            Prompt template string
        """
        return self._load_prompt("rag/answer.txt")

    def _load_prompt(self, path: str) -> str:
        """Load and cache prompt template.

        Args:
            path: Relative path to prompt file

        Returns:
            Prompt template content

        Raises:
            FileNotFoundError: If prompt template not found
        """
        if path not in self._cache:
            full_path = self.prompts_dir / path
            if not full_path.exists():
                raise FileNotFoundError(f"Prompt template not found: {full_path}")

            self._cache[path] = full_path.read_text()

        return self._cache[path]
