"""YouTube video content processor using yt-dlp."""
import re
import asyncio
from typing import Optional
import requests
import yt_dlp
from bot.content_processors.base import ContentProcessor


class YouTubeProcessor(ContentProcessor):
    """Processor for YouTube videos (extracts closed captions using yt-dlp)."""

    def __init__(self):
        """Initialize YouTube processor."""
        self._last_video_info = None

    def _extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL.

        Args:
            url: YouTube URL

        Returns:
            Video ID

        Raises:
            ValueError: If video ID cannot be extracted
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\?/]+)',
            r'youtube\.com/embed/([^&\?/]+)',
            r'youtube\.com/v/([^&\?/]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise ValueError(f"Could not extract video ID from URL: {url}")

    async def extract_content(self, url: str) -> str:
        """Extract closed captions from YouTube video using yt-dlp.

        Args:
            url: The YouTube video URL

        Returns:
            Markdown-formatted transcript

        Raises:
            Exception: If content extraction fails
        """
        try:
            # Configure yt-dlp options
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }

            # Extract info in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: self._extract_with_ytdlp(url, ydl_opts)
            )

            if not info:
                raise Exception("Could not extract video information")

            # Store video info for metadata extraction
            self._last_video_info = info

            # Get subtitles
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})

            # Try to get English subtitles (prefer manual over automatic)
            subtitle_text = None
            for lang in ['en', 'en-US', 'en-GB']:
                if lang in subtitles:
                    subtitle_text = await self._download_and_parse_subtitle(subtitles[lang])
                    if subtitle_text:
                        break

            # Fall back to automatic captions if no manual subtitles
            if not subtitle_text:
                for lang in ['en', 'en-US', 'en-GB']:
                    if lang in automatic_captions:
                        subtitle_text = await self._download_and_parse_subtitle(automatic_captions[lang])
                        if subtitle_text:
                            break

            if not subtitle_text:
                raise Exception("No English subtitles or captions available for this video")

            # Clean up the text
            subtitle_text = re.sub(r'\s+', ' ', subtitle_text).strip()

            return f"# YouTube Video Transcript\n\n{subtitle_text}"

        except Exception as e:
            raise Exception(f"Failed to extract YouTube captions: {str(e)}")

    def _extract_with_ytdlp(self, url: str, opts: dict) -> Optional[dict]:
        """Extract video info using yt-dlp (blocking call).

        Args:
            url: YouTube URL
            opts: yt-dlp options

        Returns:
            Video info dictionary or None
        """
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception:
            return None

    async def _download_and_parse_subtitle(self, subtitle_formats: list) -> Optional[str]:
        """Download and parse subtitle from available formats.

        Args:
            subtitle_formats: List of subtitle format dictionaries

        Returns:
            Extracted subtitle text or None
        """
        # Try different formats in order of preference
        for fmt in subtitle_formats:
            url = fmt.get('url')
            if not url:
                continue

            try:
                # Download subtitle content
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(url, timeout=30)
                )

                if response.status_code != 200:
                    continue

                content = response.text

                # Parse based on format
                ext = fmt.get('ext', '')
                if ext in ['vtt', 'srv3']:
                    return self._parse_vtt(content)
                elif ext == 'json3':
                    return self._parse_json3(content)
                else:
                    # Try to parse as VTT anyway
                    parsed = self._parse_vtt(content)
                    if parsed:
                        return parsed

            except Exception:
                continue

        return None

    def _parse_vtt(self, content: str) -> Optional[str]:
        """Parse VTT (WebVTT) subtitle format.

        Args:
            content: VTT file content

        Returns:
            Extracted text or None
        """
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            # Skip VTT headers, timestamps, cue identifiers, and empty lines
            if (line and
                not line.startswith('WEBVTT') and
                not '-->' in line and
                not line.startswith('NOTE') and
                not line.startswith('STYLE') and
                not line.startswith('::cue') and
                not line.isdigit()):
                # Remove VTT formatting tags
                line = re.sub(r'<[^>]+>', '', line)
                if line:
                    lines.append(line)

        return ' '.join(lines) if lines else None

    def _parse_json3(self, content: str) -> Optional[str]:
        """Parse JSON3 subtitle format (YouTube's format).

        Args:
            content: JSON3 file content

        Returns:
            Extracted text or None
        """
        try:
            import json
            data = json.loads(content)
            events = data.get('events', [])

            lines = []
            for event in events:
                segs = event.get('segs', [])
                for seg in segs:
                    text = seg.get('utf8', '').strip()
                    if text:
                        lines.append(text)

            return ' '.join(lines) if lines else None
        except:
            return None

    async def get_document_name(self, url: str, content: str) -> str:
        """Generate short document name from video title.

        Args:
            url: The source URL
            content: The extracted content

        Returns:
            Short, readable document name
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }

            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: self._extract_with_ytdlp(url, ydl_opts)
            )

            if info:
                title = info.get('title', '')
                if title:
                    # Truncate if too long
                    if len(title) > 60:
                        title = title[:57] + "..."
                    return title
        except:
            pass

        # Fallback
        video_id = self._extract_video_id(url)
        return f"YouTube Video {video_id}"

    def get_video_duration(self) -> str:
        """Get video duration in MM:SS format.

        Returns:
            Duration string (e.g., "12:34") or "Unknown" if not available
        """
        if not self._last_video_info:
            return "Unknown"

        duration_seconds = self._last_video_info.get('duration')
        if not duration_seconds:
            return "Unknown"

        # Convert seconds to MM:SS format
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def get_prompt_template_name(self) -> str:
        """Return name of prompt template to use.

        Returns:
            'youtube'
        """
        return "youtube"
