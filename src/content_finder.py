"""
Content Finder — يقوم بتحميل فيديوهات يوتيوب واستخراج النص (transcription)
ثم تجهيز القصة الخام لإعادة الصياغة.
"""
from __future__ import annotations
import os, json, re, subprocess, tempfile
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import requests

class ContentFinder:
    """
    Finds trending YouTube videos via ChannelAnalyzer, downloads them,
    transcribes the audio, and prepares raw story text for rewriting.
    """
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.yt_dlp_path = "yt-dlp"  # Assume installed
    
    def download_video(self, video_url: str, output_template: str = None) -> Optional[str]:
        """
        Download a YouTube video's audio for transcription.
        
        Args:
            video_url: Full YouTube URL or video ID
            output_template: Output file template (default: data/raw/%(id)s.%(ext)s)
            
        Returns: Path to downloaded audio file, or None
        """
        if not output_template:
            output_template = str(self.output_dir / "%(id)s.%(ext)s")
        
        # Extract video ID from URL
        video_id = self._extract_video_id(video_url)
        if not video_id:
            print(f"  ✗ Invalid video URL: {video_url}")
            return None
        
        print(f"  Downloading audio: {video_id}")
        
        # Download audio only (smaller, faster)
        cmd = [
            self.yt_dlp_path,
            f"https://youtube.com/watch?v={video_id}",
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "128K",  # Good enough for transcription
            "-o", output_template,
            "--no-playlist",
            "--quiet",
            "--no-warnings",
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                print(f"  ⚠ yt-dlp warning: {result.stderr[:200]}")
            
            # Find the downloaded file
            audio_path = self.output_dir / f"{video_id}.mp3"
            if audio_path.exists():
                print(f"  ✓ Audio saved: {audio_path}")
                return str(audio_path)
            else:
                # yt-dlp might have used a different extension
                for ext in [".mp3", ".m4a", ".opus", ".webm"]:
                    p = self.output_dir / f"{video_id}{ext}"
                    if p.exists():
                        print(f"  ✓ Audio saved: {p}")
                        return str(p)
                print(f"  ✗ Audio file not found after download")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"  ✗ Download timeout for {video_id}")
            return None
        except FileNotFoundError:
            print(f"  ✗ yt-dlp not found. Install: pip install yt-dlp")
            return None
        except Exception as e:
            print(f"  ✗ Download error: {e}")
            return None
    
    def transcribe_audio(self, audio_path: str, language: str = "en") -> Optional[str]:
        """
        Transcribe audio to text using whisper.
        
        Tries OpenAI Whisper first, then falls back to a simpler approach.
        
        Args:
            audio_path: Path to audio file
            language: Language code
            
        Returns: Transcribed text, or None
        """
        print(f"  Transcribing: {audio_path}")
        
        # Try whisper
        try:
            import whisper
            model = whisper.load_model("base")  # Small, fast, reasonably accurate
            result = model.transcribe(audio_path, language=language)
            text = result["text"]
            
            # Save transcript
            transcript_path = Path(audio_path).with_suffix(".txt")
            transcript_path.write_text(text, encoding='utf-8')
            
            print(f"  ✓ Transcribed: {len(text)} chars")
            return text
            
        except ImportError:
            print(f"  ⚠ whisper not installed, trying whisper.cpp...")
        except Exception as e:
            print(f"  ⚠ whisper error: {e}")
        
        # Try whisper.cpp as fallback
        try:
            # Convert to WAV first
            wav_path = Path(audio_path).with_suffix(".wav")
            subprocess.run([
                "ffmpeg", "-y", "-i", audio_path,
                "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                str(wav_path)
            ], capture_output=True, timeout=120)
            
            result = subprocess.run([
                "./whisper.cpp/main", "-f", str(wav_path),
                "-m", "./whisper.cpp/models/ggml-base.en.bin",
                "-otxt"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return result.stdout
            
        except Exception as e:
            print(f"  ⚠ whisper.cpp error: {e}")
        
        # Last resort: return empty and let AI handle it
        print(f"  ✗ Transcription failed")
        return None
    
    def extract_story_from_video(self, video_info: Dict) -> Optional[Dict]:
        """
        Full pipeline: download → transcribe → prepare for rewriting.
        
        Args:
            video_info: Dict with video_id, title, description from ChannelAnalyzer
            
        Returns: Dict with raw story data for the AI rewriter
        """
        video_id = video_info["video_id"]
        print(f"\n=== Processing Video: {video_info.get('title', video_id)} ===")
        
        # Step 1: Download audio
        audio_path = self.download_video(video_id)
        if not audio_path:
            # If download fails, use description as story source
            print("  Using video description as story source")
            return self._prepare_from_description(video_info)
        
        # Step 2: Transcribe
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            print("  Using video description as fallback")
            return self._prepare_from_description(video_info)
        
        # Step 3: Prepare story data
        story_data = {
            "source": "youtube",
            "video_id": video_id,
            "original_title": video_info.get("title", ""),
            "original_description": video_info.get("description", ""),
            "transcript": transcript,
            "hashtags": video_info.get("tags", []),
            "view_count": video_info.get("view_count", 0),
            "extracted_at": datetime.now().isoformat(),
        }
        
        # Save raw story
        story_path = self.output_dir / f"{video_id}_raw.json"
        story_path.write_text(json.dumps(story_data, indent=2, default=str), encoding='utf-8')
        print(f"  ✓ Story data saved: {story_path}")
        
        return story_data
    
    def _prepare_from_description(self, video_info: Dict) -> Dict:
        """Fallback: use video description as story source."""
        desc = video_info.get("description", "")
        # Extract the narrative part (before hashtags)
        story_text = re.split(r'#\w+', desc)[0] if '#' in desc else desc
        
        story_data = {
            "source": "youtube_description",
            "video_id": video_info.get("video_id", ""),
            "original_title": video_info.get("title", ""),
            "original_description": desc,
            "transcript": story_text,
            "hashtags": video_info.get("tags", []),
            "view_count": video_info.get("view_count", 0),
            "extracted_at": datetime.now().isoformat(),
        }
        
        story_path = self.output_dir / f"{video_info.get('video_id', 'unknown')}_raw.json"
        story_path.write_text(json.dumps(story_data, indent=2, default=str), encoding='utf-8')
        
        return story_data
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL or return as-is if already ID."""
        url = url.strip()
        patterns = [
            r'(?:youtube\.com/watch\?v=)(\w-{11})',
            r'(?:youtu\.be/)(\w-{11})',
            r'(?:youtube\.com/embed/)(\w-{11})',
            r'(?:youtube\.com/shorts/)(\w-{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        # If it's already a video ID (11 chars)
        if re.match(r'^\w-{11}$', url):
            return url
        return None
    
    def fetch_video_info(self, video_id: str) -> Optional[Dict]:
        """Fetch video metadata via YouTube oEmbed API (no key needed)."""
        url = f"https://www.youtube.com/oembed?url=https://youtube.com/watch?v={video_id}&format=json"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {
                "video_id": video_id,
                "title": data.get("title", ""),
                "author_name": data.get("author_name", ""),
                "author_url": data.get("author_url", ""),
                "thumbnail_url": data.get("thumbnail_url", ""),
            }
        except Exception as e:
            print(f"  ⚠ oEmbed error: {e}")
            return None
    
    def get_video_description(self, video_id: str) -> Optional[str]:
        """Get video description via invidious (free, no key)."""
        # Try public invidious instances
        instances = [
            f"https://invidious.snopyta.org/api/v1/videos/{video_id}",
            f"https://yewtu.be/api/v1/videos/{video_id}",
            f"https://invidious.private.coffee/api/v1/videos/{video_id}",
        ]
        for instance in instances:
            try:
                resp = requests.get(instance, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("description", "")
            except Exception:
                continue
        return None


def main():
    import argparse, json
    
    parser = argparse.ArgumentParser(description="YouTube Content Finder")
    parser.add_argument("--video", help="YouTube video URL or ID to process")
    parser.add_argument("--urls-file", help="File containing video URLs (one per line)")
    parser.add_argument("--output", default="data/raw", help="Output directory")
    args = parser.parse_args()
    
    finder = ContentFinder(output_dir=args.output)
    
    video_urls = []
    if args.video:
        video_urls.append(args.video)
    if args.urls_file:
        with open(args.urls_file, 'r') as f:
            video_urls.extend([line.strip() for line in f if line.strip()])
    
    for url in video_urls:
        video_id = finder._extract_video_id(url)
        if video_id:
            info = finder.fetch_video_info(video_id)
            if info:
                # Try to get description
                desc = finder.get_video_description(video_id)
                if desc:
                    info["description"] = desc
                story = finder.extract_story_from_video(info)
                if story:
                    print(f"  ✓ Ready for rewriting: {story['original_title']}")

if __name__ == "__main__":
    main()