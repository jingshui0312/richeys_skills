#!/usr/bin/env python3
"""
YouTube Subtitle Segment Extractor
Extracts video metadata and timestamped subtitle segments for collage generation.
"""

import sys
import json
import argparse
import re
from typing import Dict, Any, Optional, List


def extract_video_id(url_or_id: str) -> Optional[str]:
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def get_video_metadata(video_id: str) -> Dict[str, Any]:
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
                'channel': data.get('channel', data.get('uploader', '')),
                'description': (data.get('description', '') or '')[:400],
                'duration': data.get('duration_string', ''),
                'view_count': data.get('view_count', 0),
                'thumbnail': data.get('thumbnail', ''),
                'upload_date': data.get('upload_date', ''),
            }
    except Exception as e:
        print(f"yt-dlp metadata fetch failed: {e}", file=sys.stderr)
    return {'title': '', 'channel': '', 'description': '', 'duration': '', 'view_count': 0, 'thumbnail': '', 'upload_date': ''}


def get_segments(video_id: str, lang_priority: list = None) -> Dict[str, Any]:
    if lang_priority is None:
        lang_priority = ['zh-Hans', 'zh-Hant', 'zh', 'en']

    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
        except TypeError:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except Exception as e:
            print(f"Cannot list transcripts: {e}", file=sys.stderr)
            return {'segments': [], 'language': 'unknown'}

        transcript = None
        lang_used = 'en'

        for lang in lang_priority:
            try:
                transcript = transcript_list.find_transcript([lang])
                lang_used = lang
                break
            except NoTranscriptFound:
                continue

        if transcript is None:
            try:
                transcript = transcript_list.find_manually_created_transcript()
                lang_used = transcript.language_code
            except Exception:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                    lang_used = 'en (auto)'
                except Exception:
                    for t in transcript_list:
                        transcript = t
                        lang_used = t.language_code
                        break

        if transcript is None:
            return {'segments': [], 'language': 'none'}

        raw_segments = transcript.fetch()

        def seg_text(seg):
            return seg.text if hasattr(seg, 'text') else seg.get('text', '')

        def seg_start(seg):
            return seg.start if hasattr(seg, 'start') else seg.get('start', 0)

        def seg_duration(seg):
            return seg.duration if hasattr(seg, 'duration') else seg.get('duration', 0)

        # Merge short segments into sentence-level chunks
        segments = []
        buffer_text = ''
        buffer_start = 0.0
        MIN_CHARS = 20  # merge segments shorter than this

        for seg in raw_segments:
            text = seg_text(seg).strip()
            text = re.sub(r'\[.*?\]', '', text).strip()  # remove [Music], [Applause] etc.
            if not text:
                continue
            start = seg_start(seg)

            if not buffer_text:
                buffer_start = start
                buffer_text = text
            else:
                # Merge if current buffer doesn't end a sentence
                if not re.search(r'[.!?。！？]$', buffer_text) and len(buffer_text) < MIN_CHARS:
                    buffer_text += ' ' + text
                else:
                    segments.append({
                        'start': buffer_start,
                        'timestamp': format_timestamp(buffer_start),
                        'text': buffer_text,
                    })
                    buffer_start = start
                    buffer_text = text

        if buffer_text:
            segments.append({
                'start': buffer_start,
                'timestamp': format_timestamp(buffer_start),
                'text': buffer_text,
            })

        return {'segments': segments, 'language': lang_used}

    except ImportError:
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'youtube-transcript-api'], check=True)
        return get_segments(video_id, lang_priority)
    except Exception as e:
        print(f"Segment fetch error: {e}", file=sys.stderr)
        return {'segments': [], 'language': 'unknown'}


def main():
    parser = argparse.ArgumentParser(description='Extract YouTube subtitle segments for collage generation')
    parser.add_argument('url', help='YouTube video URL or video ID')
    parser.add_argument('--output', '-o', default='-', help='Output JSON file (default: stdout)')
    parser.add_argument('--max-segments', type=int, default=300, help='Max segments to return')
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"Error: Cannot extract video ID from: {args.url}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting: {video_id}", file=sys.stderr)
    meta = get_video_metadata(video_id)
    segment_data = get_segments(video_id)

    segments = segment_data['segments'][:args.max_segments]

    result = {
        'video_id': video_id,
        'url': f'https://www.youtube.com/watch?v={video_id}',
        'title': meta['title'],
        'channel': meta['channel'],
        'description': meta['description'],
        'duration': meta['duration'],
        'view_count': meta['view_count'],
        'thumbnail': meta['thumbnail'],
        'transcript_language': segment_data['language'],
        'total_segments': len(segment_data['segments']),
        'segments': segments,
    }

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output == '-':
        print(output_json)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"Saved to: {args.output}", file=sys.stderr)
        print(f"Title   : {meta['title']}", file=sys.stderr)
        print(f"Channel : {meta['channel']}", file=sys.stderr)
        print(f"Duration: {meta['duration']}", file=sys.stderr)
        print(f"Segments: {len(segments)} (of {len(segment_data['segments'])} total)", file=sys.stderr)
        print(f"Language: {segment_data['language']}", file=sys.stderr)


if __name__ == '__main__':
    main()
