"""
Channel Analyzer — تحليل قنوات يوتيوب المنافسة واكتشاف الترندات
يقوم بتحليل القنوات المدخلة من Dashboard، ويجد أفضل فيديوهاتها،
ويستخرج الهاشتاغات وأنماط العناوين للاستخدام في إنتاج فيديوهات جديدة.
"""
from __future__ import annotations
import os, json, time, re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import requests
from urllib.parse import quote

@dataclass
class CompetitorVideo:
    """فيديو منافس محلل"""
    video_id: str
    title: str
    description: str
    view_count: int
    like_count: int
    comment_count: int
    publish_date: str
    duration_sec: int
    tags: List[str]
    thumbnail_url: str
    engagement_rate: float = 0.0
    seo_score: float = 0.0

@dataclass
class ChannelAnalysis:
    """تحليل كامل لقناة"""
    channel_id: str
    channel_name: str
    subscriber_count: int
    total_views: int
    top_videos: List[CompetitorVideo]
    common_tags: List[str]
    title_patterns: List[str]
    description_pattern: str
    avg_views: float
    avg_engagement: float
    posting_frequency: str
    estimated_rpm: float = 2.0

class ChannelAnalyzer:
    """YouTube Channel Analysis Engine"""
    
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    def analyze_channel(self, channel_url: str) -> Optional[ChannelAnalysis]:
        """
        Analyze a YouTube channel: get stats, top videos, patterns.
        
        Args:
            channel_url: Full YouTube channel URL or channel ID
            
        Returns: ChannelAnalysis object with all insights
        """
        channel_id = self._extract_channel_id(channel_url)
        if not channel_id:
            print(f"  ✗ Invalid channel URL: {channel_url}")
            return None
        
        print(f"  Analyzing channel: {channel_id}")
        
        # Get channel info
        channel_info = self._get_channel_info(channel_id)
        if not channel_info:
            return None
        
        # Get top videos
        top_videos = self._get_channel_top_videos(channel_id, max_results=20)
        
        # Extract patterns
        common_tags = self._extract_common_tags(top_videos)
        title_patterns = self._extract_title_patterns(top_videos)
        description_pattern = self._extract_description_pattern(top_videos)
        
        # Calculate metrics
        avg_views = sum(v.view_count for v in top_videos) / max(len(top_videos), 1)
        avg_engagement = sum(v.engagement_rate for v in top_videos) / max(len(top_videos), 1)
        
        analysis = ChannelAnalysis(
            channel_id=channel_id,
            channel_name=channel_info.get("title", "Unknown"),
            subscriber_count=channel_info.get("subscriberCount", 0),
            total_views=channel_info.get("viewCount", 0),
            top_videos=top_videos[:10],  # Keep top 10
            common_tags=common_tags[:30],  # Keep top 30 tags
            title_patterns=title_patterns[:5],
            description_pattern=description_pattern,
            avg_views=avg_views,
            avg_engagement=avg_engagement,
            posting_frequency=self._estimate_posting_frequency(channel_id)
        )
        
        print(f"  ✓ {analysis.channel_name}: {analysis.subscriber_count} subs, {len(top_videos)} videos analyzed")
        return analysis
    
    def find_trending_videos(self, keywords: List[str], min_views: int = 10000, max_results: int = 20) -> List[CompetitorVideo]:
        """
        Find trending videos matching keywords.
        
        Args:
            keywords: Search terms (e.g. ["revenge story", "family drama", "karma"])
            min_views: Minimum view count filter
            max_results: Max videos to return
            
        Returns: List of trending CompetitorVideo objects
        """
        all_videos = []
        
        for keyword in keywords:
            print(f"  Searching trending: '{keyword}'")
            url = f"{self.base_url}/search"
            params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",  # Most viewed first
                "maxResults": min(10, max_results),
                "relevanceLanguage": "en",
                "key": self.api_key,
            }
            
            try:
                resp = requests.get(url, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("items", []):
                    video_id = item["id"]["videoId"]
                    snippet = item["snippet"]
                    
                    # Get detailed stats
                    stats = self._get_video_stats(video_id)
                    
                    video = CompetitorVideo(
                        video_id=video_id,
                        title=snippet["title"],
                        description=snippet.get("description", ""),
                        view_count=stats.get("viewCount", 0),
                        like_count=stats.get("likeCount", 0),
                        comment_count=stats.get("commentCount", 0),
                        publish_date=snippet.get("publishedAt", ""),
                        duration_sec=self._get_video_duration(video_id),
                        tags=snippet.get("tags", []),
                        thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    )
                    
                    # Calculate engagement rate
                    if video.view_count > 0:
                        video.engagement_rate = (video.like_count + video.comment_count) / video.view_count * 100
                    
                    if video.view_count >= min_views:
                        all_videos.append(video)
                
            except Exception as e:
                print(f"  ⚠ Search error for '{keyword}': {e}")
            
            time.sleep(0.5)  # Rate limit
        
        # Sort by views descending
        all_videos.sort(key=lambda v: v.view_count, reverse=True)
        
        print(f"  Found {len(all_videos)} trending videos above {min_views} views")
        return all_videos[:max_results]
    
    def extract_hashtags(self, videos: List[CompetitorVideo]) -> Dict[str, int]:
        """Extract and count hashtags from competitor videos."""
        hashtag_counts = {}
        for video in videos:
            # Extract hashtags from description
            tags = re.findall(r'#(\w+)', video.description)
            for tag in tags:
                tag_lower = tag.lower()
                hashtag_counts[tag_lower] = hashtag_counts.get(tag_lower, 0) + 1
            # Also from video tags
            for tag in video.tags:
                tag_lower = tag.lower().replace(" ", "")
                hashtag_counts[tag_lower] = hashtag_counts.get(tag_lower, 0) + 1
        
        return dict(sorted(hashtag_counts.items(), key=lambda x: -x[1]))
    
    def generate_seo_package(self, video: CompetitorVideo, rewritten_title: str) -> Dict:
        """
        Generate complete SEO package based on competitor analysis.
        
        Returns dict with: title, description, hashtags, publish_time
        """
        # Get trending hashtags from competitor
        competitor_hashtags = self.extract_hashtags([video])
        
        # Build description
        description = f"""{rewritten_title}

{video.description[:200]}...

#hashtags

📌هذا故事纯属虚构。

👇 What would you do? Comment below!
🔔 Subscribe for more revenge stories daily!
"""
        
        return {
            "title": rewritten_title,
            "description": description,
            "hashtags": list(competitor_hashtags.keys())[:20],
            "suggested_publish_time": "14:00 UTC",
        }
    
    def _extract_channel_id(self, url_or_id: str) -> Optional[str]:
        """Extract channel ID from various URL formats."""
        url_or_id = url_or_id.strip()
        
        # Already a channel ID (starts with UC)
        if url_or_id.startswith("UC") and len(url_or_id) == 24:
            return url_or_id
        
        # Handle various URL formats
        patterns = [
            r'(?:youtube\.com/channel/)(UC[\w-]+)',
            r'(?:youtube\.com/@)([\w-]+)',
            r'(?:youtube\.com/c/)([\w-]+)',
            r'(?:youtube\.com/user/)([\w-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                handle = match.group(1)
                # If it's a handle (@name), resolve it
                if not handle.startswith("UC"):
                    return self._resolve_handle(handle)
                return handle
        
        return None
    
    def _resolve_handle(self, handle: str) -> Optional[str]:
        """Resolve a YouTube handle to channel ID."""
        url = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "q": handle,
            "type": "channel",
            "key": self.api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("items"):
                return data["items"][0]["snippet"]["channelId"]
        except Exception:
            pass
        return None
    
    def _get_channel_info(self, channel_id: str) -> Optional[Dict]:
        """Get channel statistics."""
        url = f"{self.base_url}/channels"
        params = {
            "part": "snippet,statistics",
            "id": channel_id,
            "key": self.api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("items"):
                stats = data["items"][0]["statistics"]
                snippet = data["items"][0]["snippet"]
                return {
                    "title": snippet["title"],
                    "description": snippet.get("description", ""),
                    "subscriberCount": int(stats.get("subscriberCount", 0)),
                    "viewCount": int(stats.get("viewCount", 0)),
                    "videoCount": int(stats.get("videoCount", 0)),
                }
        except Exception as e:
            print(f"  ⚠ Channel info error: {e}")
        return None
    
    def _get_channel_top_videos(self, channel_id: str, max_results: int = 20) -> List[CompetitorVideo]:
        """Get a channel's most viewed videos."""
        url = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "order": "viewCount",
            "type": "video",
            "maxResults": min(50, max_results * 2),
            "key": self.api_key,
        }
        
        videos = []
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            for item in data.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                stats = self._get_video_stats(video_id)
                duration = self._get_video_duration(video_id)
                
                video = CompetitorVideo(
                    video_id=video_id,
                    title=snippet["title"],
                    description=snippet.get("description", ""),
                    view_count=int(stats.get("viewCount", 0)),
                    like_count=int(stats.get("likeCount", 0)),
                    comment_count=int(stats.get("commentCount", 0)),
                    publish_date=snippet.get("publishedAt", ""),
                    duration_sec=duration,
                    tags=snippet.get("tags", []),
                    thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                )
                
                if video.view_count > 0:
                    video.engagement_rate = (video.like_count + video.comment_count) / video.view_count * 100
                
                videos.append(video)
                
        except Exception as e:
            print(f"  ⚠ Top videos error: {e}")
        
        videos.sort(key=lambda v: v.view_count, reverse=True)
        return videos[:max_results]
    
    def _get_video_stats(self, video_id: str) -> Dict:
        """Get video statistics."""
        url = f"{self.base_url}/videos"
        params = {
            "part": "statistics",
            "id": video_id,
            "key": self.api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("items"):
                return data["items"][0]["statistics"]
        except Exception:
            pass
        return {}
    
    def _get_video_duration(self, video_id: str) -> int:
        """Get video duration in seconds."""
        url = f"{self.base_url}/videos"
        params = {"part": "contentDetails", "id": video_id, "key": self.api_key}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("items"):
                duration_str = data["items"][0]["contentDetails"]["duration"]
                # Parse ISO 8601 duration
                import isodate
                return int(isodate.parse_duration(duration_str).total_seconds())
        except Exception:
            pass
        return 0
    
    def _extract_common_tags(self, videos: List[CompetitorVideo]) -> List[str]:
        """Extract most common tags across videos."""
        tag_counts = {}
        for video in videos:
            for tag in video.tags:
                tag_counts[tag.lower()] = tag_counts.get(tag.lower(), 0) + 1
        return [tag for tag, _ in sorted(tag_counts.items(), key=lambda x: -x[1])]
    
    def _extract_title_patterns(self, videos: List[CompetitorVideo]) -> List[str]:
        """Extract common title patterns."""
        patterns = []
        for video in videos[:10]:
            title = video.title
            # Check for common patterns
            if " — " in title or " – " in title:
                patterns.append("Story — Twist")
            if "?" in title:
                patterns.append("Question Hook")
            if "!" in title:
                patterns.append("Exclamation Hook")
            if title.startswith("My") or title.startswith("I "):
                patterns.append("First Person Story")
        return list(set(patterns)) if patterns else ["Story — Twist"]
    
    def _extract_description_pattern(self, videos: List[CompetitorVideo]) -> str:
        """Extract common description pattern."""
        descriptions = [v.description for v in videos[:5] if v.description]
        if descriptions:
            # Find most common structure
            return descriptions[0][:500]  # Sample
        return ""
    
    def _estimate_posting_frequency(self, channel_id: str) -> str:
        """Estimate how often a channel posts."""
        url = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "order": "date",
            "maxResults": 10,
            "key": self.api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            items = data.get("items", [])
            if len(items) >= 2:
                dates = [datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z", "+00:00")) for item in items]
                if dates:
                    avg_gap = (dates[0] - dates[-1]).total_seconds() / max(len(dates) - 1, 1)
                    hours = avg_gap / 3600
                    if hours < 12: return "2-3 videos/day"
                    elif hours < 24: return "1 video/day"
                    elif hours < 72: return "1 video/2 days"
                    else: return "Weekly"
        except Exception:
            pass
        return "Unknown"


def main():
    import argparse, json
    
    parser = argparse.ArgumentParser(description="YouTube Channel Analyzer")
    parser.add_argument("--channel", help="YouTube channel URL or ID")
    parser.add_argument("--search", nargs="+", help="Keywords to search for trending videos")
    parser.add_argument("--min-views", type=int, default=10000, help="Minimum views filter")
    parser.add_argument("--output", default="data/analysis", help="Output directory")
    args = parser.parse_args()
    
    import os; os.makedirs(args.output, exist_ok=True)
    analyzer = ChannelAnalyzer()
    
    if args.channel:
        print(f"\n=== Analyzing Channel: {args.channel} ===")
        analysis = analyzer.analyze_channel(args.channel)
        if analysis:
            print(f"\nChannel: {analysis.channel_name}")
            print(f"Subscribers: {analysis.subscriber_count:,}")
            print(f"Avg Views: {analysis.avg_views:,.0f}")
            print(f"Engagement: {analysis.avg_engagement:.2f}%")
            print(f"Common Tags: {', '.join(analysis.common_tags[:10])}")
            print(f"Title Patterns: {', '.join(analysis.title_patterns)}")
            
            outfile = os.path.join(args.output, f"{analysis.channel_id}.json")
            import dataclasses
            with open(outfile, 'w', encoding='utf-8') as f:
                json.dump({
                    "channel_name": analysis.channel_name,
                    "subscriber_count": analysis.subscriber_count,
                    "total_views": analysis.total_views,
                    "avg_views": analysis.avg_views,
                    "avg_engagement": analysis.avg_engagement,
                    "common_tags": analysis.common_tags[:20],
                    "title_patterns": analysis.title_patterns,
                    "top_videos": [asdict(v) for v in analysis.top_videos],
                }, f, indent=2, default=str)
            print(f"  Saved to: {outfile}")
    
    if args.search:
        print(f"\n=== Searching Trending Videos ===")
        videos = analyzer.find_trending_videos(args.search, args.min_views)
        hashtags = analyzer.extract_hashtags(videos)
        print(f"\nTop Hashtags: {', '.join(list(hashtags.keys())[:20])}")
        
        # Save results
        outfile = os.path.join(args.output, "trending_search.json")
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump({
                "keywords": args.search,
                "videos_found": len(videos),
                "top_hashtags": hashtags,
                "videos": [asdict(v) for v in videos],
            }, f, indent=2, default=str)
        print(f"  Saved to: {outfile}")

if __name__ == "__main__":
    main()