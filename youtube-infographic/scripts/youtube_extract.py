#!/usr/bin/env python3
"""
YouTube Video Content Extractor
Extracts video metadata and transcript for infographic generation.
Token-efficient: transcript truncation + optional brief mode for testing.
"""

import sys
import json
import argparse
import re
import os
from typing import Dict, Any, Optional


def extract_video_id(url_or_id: str) -> Optional[str]:
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def get_video_metadata(video_id: str) -> Dict[str, Any]:
    """Get video metadata using yt-dlp (no API key required)."""
    import subprocess
    try:
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-playlist', '--no-warnings',
             f'https://www.youtube.com/watch?v={video_id}'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'title': data.get('title', ''),
                'description': (data.get('description', '') or '')[:500],
                'channel': data.get('channel', data.get('uploader', '')),
                'upload_date': data.get('upload_date', ''),
                'view_count': data.get('view_count', 0),
                'duration': data.get('duration_string', ''),
                'tags': data.get('tags', [])[:10],
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"yt-dlp metadata fetch failed: {e}", file=sys.stderr)
    return {'title': '', 'description': '', 'channel': '', 'upload_date': '', 'view_count': 0, 'duration': '', 'tags': []}


def get_transcript(video_id: str, max_chars: int = 100000, lang_priority: list = None) -> Dict[str, Any]:
    """
    Get video transcript using youtube-transcript-api.
    Returns transcript text truncated to max_chars for token efficiency.
    """
    if lang_priority is None:
        lang_priority = ['zh-Hans', 'zh-Hant', 'zh', 'en']

    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

        # v1.x uses instance methods; v0.x used class methods
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
        except TypeError:
            # Fallback for older versions
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except (TranscriptsDisabled, Exception) as e:
            print(f"Cannot list transcripts: {e}", file=sys.stderr)
            return {'text': '', 'language': 'unknown', 'is_generated': False, 'truncated': False}

        transcript = None
        lang_used = 'en'

        # Try preferred languages first
        for lang in lang_priority:
            try:
                transcript = transcript_list.find_transcript([lang])
                lang_used = lang
                break
            except NoTranscriptFound:
                continue

        # Fallback: try any available transcript (prefer manual over auto-generated)
        if transcript is None:
            try:
                transcript = transcript_list.find_manually_created_transcript()
                lang_used = transcript.language_code
            except Exception:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                    lang_used = 'en (auto)'
                except Exception:
                    # Try any available
                    for t in transcript_list:
                        transcript = t
                        lang_used = t.language_code
                        break

        if transcript is None:
            return {'text': '', 'language': 'none', 'is_generated': False, 'truncated': False}

        segments = transcript.fetch()
        is_generated = getattr(transcript, 'is_generated', False)

        # Build full text - support both dict (old API) and dataclass (new API) segments
        def seg_text(seg):
            if hasattr(seg, 'text'):
                return seg.text
            return seg.get('text', '')

        full_text = ' '.join(seg_text(seg) for seg in segments)
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        truncated = len(full_text) > max_chars
        text = full_text[:max_chars]
        if truncated:
            # Cut at last sentence boundary
            last_period = max(text.rfind('。'), text.rfind('. '), text.rfind('！'), text.rfind('？'))
            if last_period > max_chars * 0.7:
                text = text[:last_period + 1]

        return {
            'text': text,
            'language': lang_used,
            'is_generated': is_generated,
            'truncated': truncated,
            'total_chars': len(full_text)
        }

    except ImportError:
        print("youtube-transcript-api not installed. Installing...", file=sys.stderr)
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'youtube-transcript-api'], check=True)
        return get_transcript(video_id, max_chars, lang_priority)
    except Exception as e:
        print(f"Transcript fetch error: {e}", file=sys.stderr)
        return {'text': '', 'language': 'unknown', 'is_generated': False, 'truncated': False}


def extract_youtube_data(url_or_id: str, max_transcript_chars: int = 4000, brief: bool = False) -> Dict[str, Any]:
    """
    Main extraction function. Returns structured data for Claude to analyze.

    brief=True: only fetch metadata + first 1000 chars of transcript (for testing, saves tokens)
    """
    video_id = extract_video_id(url_or_id)
    if not video_id:
        print(f"Error: Cannot extract video ID from: {url_or_id}", file=sys.stderr)
        sys.exit(1)

    url = f'https://www.youtube.com/watch?v={video_id}'
    print(f"Extracting video: {video_id}", file=sys.stderr)

    # Get metadata
    print("Fetching video metadata...", file=sys.stderr)
    metadata = get_video_metadata(video_id)

    if brief:
        max_transcript_chars = min(max_transcript_chars, 1500)
        print(f"Brief mode: limiting transcript to {max_transcript_chars} chars", file=sys.stderr)

    # Get transcript
    print("Fetching transcript...", file=sys.stderr)
    transcript_data = get_transcript(video_id, max_chars=max_transcript_chars)

    if transcript_data['text']:
        lang = transcript_data['language']
        chars = len(transcript_data['text'])
        total = transcript_data.get('total_chars', chars)
        truncated_note = f" (truncated from {total} chars)" if transcript_data.get('truncated') else ""
        print(f"Transcript: {chars} chars [{lang}]{truncated_note}", file=sys.stderr)
    else:
        print("Warning: No transcript available for this video", file=sys.stderr)

    result = {
        'video_id': video_id,
        'url': url,
        'title': metadata.get('title', ''),
        'channel': metadata.get('channel', ''),
        'description': metadata.get('description', ''),
        'upload_date': metadata.get('upload_date', ''),
        'view_count': metadata.get('view_count', 0),
        'duration': metadata.get('duration', ''),
        'tags': metadata.get('tags', []),
        'transcript': transcript_data.get('text', ''),
        'transcript_language': transcript_data.get('language', 'unknown'),
        'transcript_truncated': transcript_data.get('truncated', False),
        'transcript_total_chars': transcript_data.get('total_chars', 0),
    }

    return result


def main():
    parser = argparse.ArgumentParser(description='Extract YouTube video content for infographic generation')
    parser.add_argument('url', help='YouTube video URL or video ID')
    parser.add_argument('--output', '-o', default='-', help='Output JSON file path (default: stdout)')
    parser.add_argument('--max-transcript', type=int, default=100000,
                        help='Max transcript characters to extract (default: 100000, covers ~72%% of a 2-hour video)')
    parser.add_argument('--brief', action='store_true',
                        help='Brief mode: limit to 1500 transcript chars for quick testing')
    parser.add_argument('--no-transcript', action='store_true',
                        help='Skip transcript, only fetch metadata (fastest, fewest tokens)')

    args = parser.parse_args()

    data = extract_youtube_data(
        args.url,
        max_transcript_chars=args.max_transcript,
        brief=args.brief
    )

    if args.no_transcript:
        data['transcript'] = ''
        data['transcript_language'] = 'skipped'

    output_json = json.dumps(data, ensure_ascii=False, indent=2)

    if args.output == '-':
        print(output_json)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"Video data saved to: {args.output}", file=sys.stderr)

        # Print summary
        print(f"\n--- Video Summary ---", file=sys.stderr)
        print(f"Title    : {data['title']}", file=sys.stderr)
        print(f"Channel  : {data['channel']}", file=sys.stderr)
        print(f"Duration : {data['duration']}", file=sys.stderr)
        print(f"Views    : {data['view_count']:,}" if data['view_count'] else f"Views    : N/A", file=sys.stderr)
        print(f"Transcript: {len(data['transcript'])} chars [{data['transcript_language']}]", file=sys.stderr)


if __name__ == '__main__':
    main()
