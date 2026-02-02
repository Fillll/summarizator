"""Configuration loader and manager."""
import json
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration loader and manager."""

    def __init__(self, config_path: str = "data/config.json"):
        """Initialize config loader.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                "Please create data/config.json with your API keys."
            )

        with open(self.config_path) as f:
            config = json.load(f)

        # Allow environment variables to override config file
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            config["telegram_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
        if os.getenv("OPENAI_API_KEY"):
            config["openai_api_key"] = os.getenv("OPENAI_API_KEY")

        return config

    @property
    def telegram_token(self) -> str:
        """Get Telegram bot token."""
        return self._config["telegram_token"]

    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key."""
        return self._config["openai_api_key"]

    @property
    def data_dir(self) -> str:
        """Get data directory path."""
        return self._config.get("data_dir", "data")

    @property
    def conversation_history_limit(self) -> int:
        """Get conversation history limit."""
        return self._config.get("conversation_history_limit", 20)

    @property
    def openai_model(self) -> str:
        """Get OpenAI model name."""
        return self._config.get("openai_model", "gpt-4-turbo-preview")

    @property
    def embedding_model(self) -> str:
        """Get embedding model name."""
        return self._config.get("embedding_model", "text-embedding-3-small")

    @property
    def max_document_preview_length(self) -> int:
        """Get maximum document preview length."""
        return self._config.get("max_document_preview_length", 200)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
