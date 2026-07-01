#!/usr/bin/env python3
"""CLI entry point for YouTube Revenge Story Factory."""

import argparse, asyncio, json, sys, os, time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Sync commands
# ---------------------------------------------------------------------------

def cmd_scrape(args):
    from src.channel_analyzer import ChannelAnalyzer
    analyzer = ChannelAnalyzer()
    keywords = [args.source] if args.source else ["revenge story", "family drama", "karma"]
    results = analyzer.find_trending_videos(keywords, max_results=args.count)
    with open(args.output, "w") as f:
        json.dump({"videos": [vars(v) for v in results], "source": args.source}, f, indent=2, default=str)
    print(f"Scraped {len(results)} videos -> {args.output}")


def cmd_rewrite(args):
    from src.story_rewriter import StoryRewriter
    with open(args.input) as f:
        data = json.load(f)
    rewriter = StoryRewriter()
    story = rewriter.rewrite(data, target_duration_min=int(args.duration))
    if story:
        with open(args.output, "w") as f:
            json.dump(story, f, indent=2, default=str)
        print(f"Story rewritten -> {args.output}")
    else:
        print("Story rewriting failed — check API keys")
        sys.exit(1)


def cmd_thumbnail(args):
    from src.thumbnail_generator import ThumbnailGenerator
    with open(args.input) as f:
        data = json.load(f)
    gen = ThumbnailGenerator()
    path = gen.generate_thumbnail(data, style=args.style, output_path=args.output)
    print(f"Thumbnail generated -> {path}")


def cmd_upload(args):
    from src.youtube_uploader import YouTubeUploader, VideoMetadata, PrivacyStatus
    with open(args.story) as f:
        data = json.load(f)
    metadata = VideoMetadata(
        title=args.title or data.get("title", "YouTube Revenge Story"),
        description=args.description or data.get("hook", ""),
        tags=data.get("hashtags", [])[:20],
        category_id="22",
        privacy_status=PrivacyStatus.PUBLIC,
    )
    uploader = YouTubeUploader()
    uploader.authenticate()
    result = uploader.upload_video(args.video, metadata)
    print(f"Upload result — video ID: {result.get('id')}")


# ---------------------------------------------------------------------------
# Async commands
# ---------------------------------------------------------------------------

async def _cmd_tts(args):
    from src.tts_engine import TTSEngine
    with open(args.input) as f:
        data = json.load(f)
    engine = TTSEngine()
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Extract narration from each scene
    scenes = []
    for act in data.get("acts", []):
        for scene in act.get("scenes", []):
            scenes.append(scene)

    if not scenes:
        print("No scenes found in story data")
        return

    for i, scene in enumerate(scenes):
        narration = scene.get("narration", "")
        mood = scene.get("mood", "neutral")
        if narration:
            audio_bytes, info = await engine.generate_audio(narration, mood=mood)
            out_path = out_dir / f"scene_{i:03d}.mp3"
            with open(out_path, "wb") as f:
                f.write(audio_bytes)
            print(f"  Scene {i}: audio -> {out_path}")

    print(f"TTS audio generated -> {args.output}")


def cmd_tts(args):
    asyncio.run(_cmd_tts(args))


async def _cmd_backgrounds(args):
    from src.background_matcher import BackgroundMatcher
    with open(args.input) as f:
        data = json.load(f)

    # Collect unique moods from scenes
    moods = set()
    for act in data.get("acts", []):
        for scene in act.get("scenes", []):
            m = scene.get("mood", "neutral")
            if m:
                moods.add(m)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    async with BackgroundMatcher() as matcher:
        for mood in moods:
            bg = await matcher.get_background(mood)
            if bg:
                results[mood] = {
                    "url": bg.url,
                    "local_path": bg.local_path,
                    "source": bg.source.value,
                    "width": bg.width,
                    "height": bg.height,
                }
                print(f"  {mood}: {bg.source.value} background -> {bg.local_path}")

    with open(out_dir / "backgrounds.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Backgrounds matched ({len(results)} moods) -> {args.output}")


def cmd_backgrounds(args):
    asyncio.run(_cmd_backgrounds(args))


async def _cmd_pipeline(args):
    from src.pipeline_orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
    video_source = {
        "competitor_channels": [args.source] if args.source else [],
        "target_duration_min": 50,
        "language": "en",
    }
    result = await orchestrator.run_pipeline(video_source)
    print(f"Pipeline completed — status: {result.status.value}")
    print(f"  Stages completed: {len(result.stages_completed)}")
    if result.stages_failed:
        print(f"  Stages failed: {[s.value for s in result.stages_failed]}")


def cmd_pipeline(args):
    asyncio.run(_cmd_pipeline(args))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="YouTube Revenge Story Factory")
    sub = parser.add_subparsers(dest="command")

    p_scrape = sub.add_parser("scrape")
    p_scrape.add_argument("--output", default="outputs/scraped.json")
    p_scrape.add_argument("--source", default="")
    p_scrape.add_argument("--count", type=int, default=10)
    p_scrape.set_defaults(func=cmd_scrape)

    p_rewrite = sub.add_parser("rewrite")
    p_rewrite.add_argument("--input", required=True)
    p_rewrite.add_argument("--output", default="outputs/story.json")
    p_rewrite.add_argument("--duration", default="50")
    p_rewrite.set_defaults(func=cmd_rewrite)

    p_tts = sub.add_parser("tts")
    p_tts.add_argument("--input", required=True)
    p_tts.add_argument("--output", default="outputs/audio")
    p_tts.set_defaults(func=cmd_tts)

    p_bg = sub.add_parser("backgrounds")
    p_bg.add_argument("--input", required=True)
    p_bg.add_argument("--output", default="outputs/backgrounds")
    p_bg.set_defaults(func=cmd_backgrounds)

    p_thumb = sub.add_parser("thumbnail")
    p_thumb.add_argument("--input", required=True)
    p_thumb.add_argument("--output", default="outputs/thumbnail.png")
    p_thumb.add_argument("--style", default="dramatic")
    p_thumb.set_defaults(func=cmd_thumbnail)

    p_upload = sub.add_parser("upload")
    p_upload.add_argument("--video", required=True)
    p_upload.add_argument("--story", required=True)
    p_upload.add_argument("--title", default="")
    p_upload.add_argument("--description", default="")
    p_upload.set_defaults(func=cmd_upload)

    p_pipe = sub.add_parser("pipeline")
    p_pipe.add_argument("--source", default="")
    p_pipe.add_argument("--duration", default="50")
    p_pipe.set_defaults(func=cmd_pipeline)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
