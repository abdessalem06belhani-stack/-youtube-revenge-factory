#!/usr/bin/env python3
"""CLI entry point for YouTube Revenge Story Factory."""

import argparse, json, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cmd_scrape(args):
    from src.content_finder import ContentFinder
    from src.channel_analyzer import ChannelAnalyzer
    from src.database import Database
    db = Database()
    results = ContentFinder.find_trending_videos(["UC_sample_channel"])
    with open(args.output, "w") as f:
        json.dump({"videos": results, "source": args.source}, f, indent=2)
    print(f"Scraped {len(results)} videos -> {args.output}")

def cmd_rewrite(args):
    from src.story_rewriter import StoryRewriter
    with open(args.input) as f:
        data = json.load(f)
    story = StoryRewriter.rewrite_story(data, level=args.level)
    with open(args.output, "w") as f:
        json.dump({"story": story, "level": args.level}, f, indent=2)
    print(f"Story rewritten -> {args.output}")

def cmd_tts(args):
    from src.tts_engine import TTSEngine
    with open(args.input) as f:
        data = json.load(f)
    audio_path = TTSEngine.generate_audio(data["story"], voice=args.voice, speed=args.speed)
    print(f"Audio generated -> {audio_path}")

def cmd_backgrounds(args):
    from src.background_matcher import BackgroundMatcher
    with open(args.input) as f:
        data = json.load(f)
    result = BackgroundMatcher.match_backgrounds(data["story"], count=args.count)
    with open(os.path.join(args.output, "backgrounds.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"Backgrounds matched -> {args.output}")

def cmd_thumbnail(args):
    from src.thumbnail_generator import ThumbnailGenerator
    with open(args.input) as f:
        data = json.load(f)
    ThumbnailGenerator.generate(data["story"], output=args.output, style=args.style)
    print(f"Thumbnail generated -> {args.output}")

def cmd_upload(args):
    from src.youtube_uploader import YouTubeUploader
    with open(args.story) as f:
        data = json.load(f)
    uploader = YouTubeUploader()
    result = uploader.upload(args.video, title=args.title, description=args.description)
    print(f"Upload result: {result}")

def cmd_pipeline(args):
    from src.pipeline_orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
    orchestrator.run_full_pipeline(source_video=args.source, level=args.level, count=args.count)
    print("Pipeline completed!")

def main():
    parser = argparse.ArgumentParser(description="YouTube Revenge Story Factory")
    sub = parser.add_subparsers(dest="command")

    p_scrape = sub.add_parser("scrape")
    p_scrape.add_argument("--output", default="outputs/scraped.json")
    p_scrape.add_argument("--source", default="")
    p_scrape.add_argument("--level", default="B1")
    p_scrape.set_defaults(func=cmd_scrape)

    p_rewrite = sub.add_parser("rewrite")
    p_rewrite.add_argument("--input", required=True)
    p_rewrite.add_argument("--output", default="outputs/story.json")
    p_rewrite.add_argument("--level", default="B1")
    p_rewrite.set_defaults(func=cmd_rewrite)

    p_tts = sub.add_parser("tts")
    p_tts.add_argument("--input", required=True)
    p_tts.add_argument("--output", default="outputs/audio")
    p_tts.add_argument("--voice", default="female")
    p_tts.add_argument("--speed", default="1.0")
    p_tts.set_defaults(func=cmd_tts)

    p_bg = sub.add_parser("backgrounds")
    p_bg.add_argument("--input", required=True)
    p_bg.add_argument("--output", default="outputs/backgrounds")
    p_bg.add_argument("--count", type=int, default=3)
    p_bg.add_argument("--style", default="nature")
    p_bg.set_defaults(func=cmd_backgrounds)

    p_thumb = sub.add_parser("thumbnail")
    p_thumb.add_argument("--input", required=True)
    p_thumb.add_argument("--output", default="outputs/thumbnail.png")
    p_thumb.add_argument("--style", default="modern")
    p_thumb.set_defaults(func=cmd_thumbnail)

    p_upload = sub.add_parser("upload")
    p_upload.add_argument("--video", required=True)
    p_upload.add_argument("--story", required=True)
    p_upload.add_argument("--title", default="YouTube Revenge Story")
    p_upload.add_argument("--description", default="")
    p_upload.set_defaults(func=cmd_upload)

    p_pipe = sub.add_parser("pipeline")
    p_pipe.add_argument("--source", default="")
    p_pipe.add_argument("--level", default="B1")
    p_pipe.add_argument("--count", type=int, default=4)
    p_pipe.set_defaults(func=cmd_pipeline)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
