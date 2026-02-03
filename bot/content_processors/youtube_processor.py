"""YouTube video content processor using youtube-transcript-api + yt-dlp."""
import re
import time
import asyncio
from typing import Optional
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from bot.content_processors.base import ContentProcessor


class YouTubeProcessor(ContentProcessor):
    """Processor for YouTube videos (extracts captions)."""

    def __init__(self):
        """Initialize YouTube processor."""
        self._last_video_info = None

    def _extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL."""
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
        """Extract closed captions from YouTube video.

        Strategy:
        1. Use yt-dlp to get metadata (title, duration, detected language)
        2. Use youtube-transcript-api to fetch transcript (English first, then original language, then any)
        3. Fall back to yt-dlp subtitle download if transcript-api fails entirely

        Args:
            url: The YouTube video URL

        Returns:
            Markdown-formatted transcript

        Raises:
            Exception: If content extraction fails
        """
        try:
            video_id = self._extract_video_id(url)
            loop = asyncio.get_event_loop()

            # Step 1: Get metadata via yt-dlp (non-blocking)
            info = await loop.run_in_executor(None, lambda: self._get_video_info(url))
            self._last_video_info = info

            # Detect the video's original language
            original_lang = info.get('language', 'en') if info else 'en'

            # Step 2: Try youtube-transcript-api with retry on 429
            rate_limited = False
            subtitle_text, rate_limited = await loop.run_in_executor(
                None,
                lambda: self._fetch_transcript(video_id, original_lang)
            )

            # Step 3: Fall back to yt-dlp subtitle download (skip if rate-limited — same endpoint)
            if not subtitle_text and not rate_limited:
                subtitle_text = await loop.run_in_executor(
                    None,
                    lambda: self._fetch_transcript_ytdlp(url, original_lang, info)
                )

            if not subtitle_text:
                if rate_limited:
                    raise Exception("YouTube is rate-limiting caption requests. Please try again in a few minutes.")
                raise Exception("No subtitles or captions available for this video")

            subtitle_text = re.sub(r'\s+', ' ', subtitle_text).strip()
            return f"# YouTube Video Transcript\n\n{subtitle_text}"

        except Exception as e:
            raise Exception(f"Failed to extract YouTube captions: {str(e)}")

    def _get_video_info(self, url: str) -> Optional[dict]:
        """Get video metadata via yt-dlp."""
        try:
            ydl_opts = {
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception:
            return None

    def _fetch_transcript(self, video_id: str, original_lang: str) -> tuple:
        """Fetch transcript using youtube-transcript-api with retry.

        Language priority: English > original language > any available.

        Args:
            video_id: YouTube video ID
            original_lang: Detected video language from yt-dlp

        Returns:
            Tuple of (transcript text or None, rate_limited bool)
        """
        for attempt in range(3):
            try:
                transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

                # Build language priority list
                priority_langs = ['en']
                if original_lang and original_lang != 'en':
                    priority_langs.append(original_lang)
                    priority_langs.append(f'{original_lang}-orig')

                # Try priority languages first, then fall back to any
                transcript = None
                for lang in priority_langs:
                    try:
                        transcript = transcripts.find_transcript([lang])
                        break
                    except Exception:
                        continue

                # If no priority language found, use the first available
                if not transcript:
                    try:
                        for t in transcripts:
                            transcript = t
                            break
                    except Exception:
                        pass

                if not transcript:
                    return None, False

                segments = transcript.fetch()
                return ' '.join([seg.text for seg in segments]), False

            except Exception as e:
                if '429' in str(e):
                    if attempt < 2:
                        time.sleep(3 + attempt * 4)  # 3s, 7s backoff
                        continue
                    return None, True  # Exhausted retries, definitely rate-limited
                return None, False

        return None, True

    def _fetch_transcript_ytdlp(self, url: str, original_lang: str, info: Optional[dict]) -> Optional[str]:
        """Fallback: fetch transcript via yt-dlp subtitle download.

        Args:
            url: YouTube URL
            original_lang: Detected video language
            info: Previously extracted video info

        Returns:
            Transcript text or None
        """
        try:
            # Build language list to try
            langs_to_try = ['en', original_lang] if original_lang != 'en' else ['en']

            # Get available languages from info
            if info:
                subtitles = info.get('subtitles', {})
                auto = info.get('automatic_captions', {})
                available = list(subtitles.keys()) + list(auto.keys())
            else:
                available = []

            # Add any available languages not already in the list
            for lang in available:
                if lang not in langs_to_try:
                    langs_to_try.append(lang)

            # Try each language
            for lang in langs_to_try:
                result = self._download_subtitle_ytdlp(url, lang)
                if result:
                    return result

            return None
        except Exception:
            return None

    def _download_subtitle_ytdlp(self, url: str, lang: str) -> Optional[str]:
        """Download a single subtitle file via yt-dlp with retry.

        Args:
            url: YouTube URL
            lang: Language code

        Returns:
            Parsed subtitle text or None
        """
        import tempfile
        import os

        for attempt in range(3):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    ydl_opts = {
                        'writesubtitles': True,
                        'writeautomaticsub': True,
                        'subtitleslangs': [lang],
                        'subtitlesformat': 'vtt',
                        'skip_download': True,
                        'outtmpl': os.path.join(tmpdir, '%(id)s'),
                        'quiet': True,
                        'no_warnings': True,
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                    # Find and read the subtitle file
                    for filename in os.listdir(tmpdir):
                        if filename.endswith('.vtt'):
                            with open(os.path.join(tmpdir, filename), 'r', encoding='utf-8') as f:
                                return self._parse_vtt(f.read())

                    return None  # No file created

            except Exception as e:
                if '429' in str(e) and attempt < 2:
                    time.sleep(3 + attempt * 4)
                    continue
                return None

        return None

    def _parse_vtt(self, content: str) -> Optional[str]:
        """Parse VTT (WebVTT) subtitle format."""
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if (line and
                not line.startswith('WEBVTT') and
                '-->' not in line and
                not line.startswith('NOTE') and
                not line.startswith('STYLE') and
                not line.startswith('::cue') and
                not line.isdigit()):
                line = re.sub(r'<[^>]+>', '', line)
                if line:
                    lines.append(line)

        return ' '.join(lines) if lines else None

    async def get_document_name(self, url: str, content: str) -> str:
        """Generate short document name from video title."""
        if self._last_video_info:
            title = self._last_video_info.get('title', '')
            if title:
                return title[:57] + "..." if len(title) > 60 else title

        # Fallback: extract via yt-dlp
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: self._get_video_info(url))
            if info:
                title = info.get('title', '')
                if title:
                    return title[:57] + "..." if len(title) > 60 else title
        except Exception:
            pass

        video_id = self._extract_video_id(url)
        return f"YouTube Video {video_id}"

    def get_video_duration(self) -> str:
        """Get video duration in MM:SS format."""
        if not self._last_video_info:
            return "Unknown"

        duration_seconds = self._last_video_info.get('duration')
        if not duration_seconds:
            return "Unknown"

        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def get_prompt_template_name(self) -> str:
        """Return name of prompt template to use."""
        return "youtube"
