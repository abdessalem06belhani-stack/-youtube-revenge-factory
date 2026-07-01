import asyncio
import aiohttp
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import time
import hashlib
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import logging
from functools import wraps
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundSource(Enum):
    PEXELS = "pexels"
    PIXABAY = "pixabay"
    UNSPLASH = "unsplash"
    GRADIENT = "gradient"

@dataclass
class BackgroundResult:
    url: str
    local_path: str
    source: BackgroundSource
    width: int
    height: int
    mood: str
    downloaded_at: float = field(default_factory=time.time)
    cache_key: str = ""

@dataclass
class MoodConfig:
    mood: str
    keywords: List[str]
    color_grading: Dict[str, Tuple[int, int, int]]  # RGB values for color grading
    preferred_aspect_ratio: Tuple[int, int] = (16, 9)
    target_resolution: Tuple[int, int] = (3840, 2160)

class BackgroundMatcher:
    """
    4K Background Matcher module that fetches high-quality backgrounds based on scene mood.
    
    Sources: Pexels → Pixabay → Unsplash → Gradient fallback
    Changes every 5 seconds for retention.
    """
    
    def __init__(self, cache_dir: str = "cache/backgrounds"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # API configuration
        self.pexels_api_key = os.getenv("PEXELS_API_KEY")
        self.pixabay_api_key = os.getenv("PIXABAY_API_KEY")
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        
        # Mood to keywords mapping
        self.mood_configs = self._initialize_mood_configs()
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, BackgroundResult] = {}
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 0.5  # seconds between requests
        
        # Background sources in priority order
        self.sources = [
            BackgroundSource.PEXELS,
            BackgroundSource.PIXABAY,
            BackgroundSource.UNSPLASH,
            BackgroundSource.GRADIENT
        ]
        
        # Statistics
        self.stats = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "cache_hits": 0
        }
    
    def _initialize_mood_configs(self) -> Dict[str, MoodConfig]:
        """Initialize mood configurations with keywords and color grading."""
        return {
            "angry": MoodConfig(
                mood="angry",
                keywords=["fight", "argument", "confrontation", "rage", "violence"],
                color_grading={"red": (255, 50, 50), "orange": (255, 100, 0), "yellow": (255, 200, 0)}
            ),
            "sad": MoodConfig(
                mood="sad",
                keywords=["lonely", "rain", "night", "dark", "melancholy"],
                color_grading={"blue": (50, 50, 255), "gray": (128, 128, 128), "purple": (100, 50, 150)}
            ),
            "happy": MoodConfig(
                mood="happy",
                keywords=["joy", "celebration", "sunshine", "bright", "colorful"],
                color_grading={"yellow": (255, 255, 100), "green": (100, 255, 100), "blue": (100, 100, 255)}
            ),
            "neutral": MoodConfig(
                mood="neutral",
                keywords=["calm", "peaceful", "nature", "neutral", "balanced"],
                color_grading={"green": (100, 150, 100), "blue": (100, 150, 200), "gray": (150, 150, 150)}
            ),
            "fear": MoodConfig(
                mood="fear",
                keywords=["dark", "shadow", "nightmare", "danger", "mystery"],
                color_grading={"black": (20, 20, 30), "purple": (80, 40, 120), "red": (150, 50, 50)}
            ),
            "surprise": MoodConfig(
                mood="surprise",
                keywords=["magic", "sparkle", "colorful", "unexpected", "wonder"],
                color_grading={"purple": (150, 50, 200), "blue": (50, 150, 200), "gold": (255, 215, 0)}
            ),
            "disgust": MoodConfig(
                mood="disgust",
                keywords=["decay", "rot", "dirty", "gross", "unpleasant"],
                color_grading={"brown": (101, 67, 33), "green": (50, 100, 50), "gray": (100, 100, 100)}
            ),
            "trust": MoodConfig(
                mood="trust",
                keywords=["honest", "reliable", "stable", "solid", "clear"],
                color_grading={"blue": (70, 130, 180), "green": (60, 179, 113), "gray": (128, 128, 128)}
            ),
            "anticipation": MoodConfig(
                mood="anticipation",
                keywords=["build", "expectation", "future", "hope", "possibility"],
                color_grading={"gold": (255, 215, 0), "blue": (30, 144, 255), "green": (46, 139, 87)}
            ),
            "joy": MoodConfig(
                mood="joy",
                keywords=["celebration", "party", "fun", "excitement", "happiness"],
                color_grading={"yellow": (255, 223, 0), "red": (255, 69, 58), "green": (52, 211, 153)}
            )
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _rate_limit(self, source: BackgroundSource):
        """Implement rate limiting for API requests."""
        current_time = time.time()
        last_time = self.last_request_time.get(source.value, 0)
        
        if current_time - last_time < self.min_request_interval:
            sleep_time = self.min_request_interval - (current_time - last_time)
            time.sleep(sleep_time)
        
        self.last_request_time[source.value] = time.time()
    
    def _generate_cache_key(self, mood: str, source: BackgroundSource, keyword: str) -> str:
        """Generate a unique cache key for a background request."""
        key_data = f"{mood}_{source.value}_{keyword}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[BackgroundResult]:
        """Get background from cache if available and not expired."""
        if cache_key in self.cache:
            result = self.cache[cache_key]
            # Cache for 1 hour
            if time.time() - result.downloaded_at < 3600:
                self.stats["cache_hits"] += 1
                return result
            else:
                del self.cache[cache_key]
        return None
    
    def _save_to_cache(self, result: BackgroundResult):
        """Save background result to cache."""
        self.cache[result.cache_key] = result
    
    def _retry_request(self, func, *args, max_attempts: int = 3, **kwargs):
        """Retry a function call with exponential backoff."""
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                logger.warning(f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}")
    
    async def _fetch_from_pexels(self, keyword: str) -> Optional[BackgroundResult]:
        """Fetch background from Pexels API."""
        if not self.pexels_api_key:
            logger.warning("Pexels API key not configured")
            return None
        
        self._rate_limit(BackgroundSource.PEXELS)
        
        url = "https://api.pexels.com/v1/search"
        params = {
            "query": keyword,
            "per_page": 1,
            "orientation": "landscape",
            "size": "large"
        }
        headers = {"Authorization": self.pexels_api_key}
        
        def make_request():
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        
        try:
            data = self._retry_request(make_request)
            if data and data.get("photos"):
                photo = data["photos"][0]
                img_url = photo["src"]["original"]
                width = photo["width"]
                height = photo["height"]
                
                # Download and process image
                local_path = self._download_image(img_url, f"pexels_{keyword}")
                if local_path:
                    result = BackgroundResult(
                        url=img_url,
                        local_path=local_path,
                        source=BackgroundSource.PEXELS,
                        width=width,
                        height=height,
                        mood=keyword,
                        cache_key=self._generate_cache_key(keyword, BackgroundSource.PEXELS, keyword)
                    )
                    self._save_to_cache(result)
                    self.stats["successful"] += 1
                    return result
        except Exception as e:
            logger.error(f"Pexels API error: {e}")
            self.stats["failed"] += 1
        
        return None
    
    async def _fetch_from_pixabay(self, keyword: str) -> Optional[BackgroundResult]:
        """Fetch background from Pixabay API."""
        if not self.pixabay_api_key:
            logger.warning("Pixabay API key not configured")
            return None
        
        self._rate_limit(BackgroundSource.PIXABAY)
        
        url = "https://pixabay.com/api/"
        params = {
            "key": self.pixabay_api_key,
            "q": keyword,
            "image_type": "photo",
            "orientation": "horizontal",
            "per_page": 1,
            "min_width": 3840,
            "min_height": 2160
        }
        
        def make_request():
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        try:
            data = self._retry_request(make_request)
            if data and data.get("hits"):
                hit = data["hits"][0]
                img_url = hit["largeImageURL"]
                width = hit["imageWidth"]
                height = hit["imageHeight"]
                
                # Download and process image
                local_path = self._download_image(img_url, f"pixabay_{keyword}")
                if local_path:
                    result = BackgroundResult(
                        url=img_url,
                        local_path=local_path,
                        source=BackgroundSource.PIXABAY,
                        width=width,
                        height=height,
                        mood=keyword,
                        cache_key=self._generate_cache_key(keyword, BackgroundSource.PIXABAY, keyword)
                    )
                    self._save_to_cache(result)
                    self.stats["successful"] += 1
                    return result
        except Exception as e:
            logger.error(f"Pixabay API error: {e}")
            self.stats["failed"] += 1
        
        return None
    
    async def _fetch_from_unsplash(self, keyword: str) -> Optional[BackgroundResult]:
        """Fetch background from Unsplash API."""
        if not self.unsplash_access_key:
            logger.warning("Unsplash API key not configured")
            return None
        
        self._rate_limit(BackgroundSource.UNSPLASH)
        
        url = "https://api.unsplash.com/photos/random"
        params = {
            "query": keyword,
            "orientation": "landscape",
            "w": 3840,
            "h": 2160
        }
        headers = {"Authorization": f"Client-ID {self.unsplash_access_key}"}
        
        def make_request():
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        
        try:
            data = self._retry_request(make_request)
            if data:
                img_url = data["urls"]["raw"]
                width = data["width"]
                height = data["height"]
                
                # Download and process image
                local_path = self._download_image(img_url, f"unsplash_{keyword}")
                if local_path:
                    result = BackgroundResult(
                        url=img_url,
                        local_path=local_path,
                        source=BackgroundSource.UNSPLASH,
                        width=width,
                        height=height,
                        mood=keyword,
                        cache_key=self._generate_cache_key(keyword, BackgroundSource.UNSPLASH, keyword)
                    )
                    self._save_to_cache(result)
                    self.stats["successful"] += 1
                    return result
        except Exception as e:
            logger.error(f"Unsplash API error: {e}")
            self.stats["failed"] += 1
        
        return None
    
    def _generate_gradient_image(self, mood: str, width: int = 3840, height: int = 2160) -> str:
        """Generate a gradient image as final fallback."""
        from PIL import ImageDraw
        
        # Get color based on mood
        mood_colors = {
            "angry": [(255, 50, 50), (255, 100, 0), (255, 200, 0)],
            "sad": [(50, 50, 255), (128, 128, 128), (100, 50, 150)],
            "happy": [(255, 255, 100), (100, 255, 100), (100, 100, 255)],
            "neutral": [(100, 150, 100), (100, 150, 200), (150, 150, 150)],
            "fear": [(20, 20, 30), (80, 40, 120), (150, 50, 50)],
            "surprise": [(150, 50, 200), (50, 150, 200), (255, 215, 0)],
            "disgust": [(101, 67, 33), (50, 100, 50), (100, 100, 100)],
            "trust": [(70, 130, 180), (60, 179, 113), (128, 128, 128)],
            "anticipation": [(255, 215, 0), (30, 144, 255), (46, 139, 87)],
            "joy": [(255, 223, 0), (255, 69, 58), (52, 211, 153)]
        }
        
        colors = mood_colors.get(mood, mood_colors["neutral"])
        
        # Create gradient image
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Create a smooth gradient
        for y in range(height):
            ratio = y / height
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add some texture based on mood
        if mood == "angry":
            # Add some noise/texture
            for _ in range(width * height // 100):
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)
                image.putpixel((x, y), (random.randint(200, 255), random.randint(0, 50), random.randint(0, 50)))
        
        # Save the image
        filename = f"gradient_{mood}_{int(time.time())}.jpg"
        local_path = self.cache_dir / filename
        image.save(local_path, "JPEG", quality=95)
        
        return str(local_path)
    
    def _download_image(self, url: str, filename: str) -> Optional[str]:
        """Download an image from URL with retry logic."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to cache directory
            local_path = self.cache_dir / filename
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return str(local_path)
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            return None
    
    def _process_image(self, image_path: str, mood: str) -> str:
        """Process image: crop to 16:9, apply color grading."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get target dimensions
                target_width, target_height = 3840, 2160
                
                # Crop to 16:9 aspect ratio
                img_width, img_height = img.size
                target_ratio = target_width / target_height
                img_ratio = img_width / img_height
                
                if img_ratio > target_ratio:
                    # Image is wider than target, crop sides
                    new_width = int(img_height * target_ratio)
                    left = (img_width - new_width) // 2
                    right = left + new_width
                    top = 0
                    bottom = img_height
                else:
                    # Image is taller than target, crop top/bottom
                    new_height = int(img_width / target_ratio)
                    left = 0
                    right = img_width
                    top = (img_height - new_height) // 2
                    bottom = top + new_height
                
                img = img.crop((left, top, right, bottom))
                
                # Resize to target resolution
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Apply color grading based on mood
                mood_config = self.mood_configs.get(mood, self.mood_configs["neutral"])
                color_grading = mood_config.color_grading
                
                # Apply color grading (simple approach: adjust brightness/contrast)
                if mood == "angry":
                    # Increase red channel
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(1.2)
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.3)
                elif mood == "sad":
                    # Decrease brightness, add blue tint
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(0.7)
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(0.9)
                elif mood == "happy":
                    # Increase brightness, add warm tones
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(1.3)
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.2)
                elif mood == "fear":
                    # Darken, add blue tones
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(0.6)
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.1)
                
                # Save processed image
                processed_filename = f"processed_{Path(image_path).name}"
                processed_path = self.cache_dir / processed_filename
                img.save(processed_path, "JPEG", quality=95)
                
                return str(processed_path)
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return image_path  # Return original if processing fails
    
    async def get_background(self, mood: str, force_refresh: bool = False) -> Optional[BackgroundResult]:
        """
        Get a background image for the specified mood.
        
        Args:
            mood: The mood to get a background for
            force_refresh: Whether to force a refresh from APIs
            
        Returns:
            BackgroundResult or None if no background could be found
        """
        if mood not in self.mood_configs:
            logger.warning(f"Unknown mood '{mood}', using 'neutral' instead")
            mood = "neutral"
        
        mood_config = self.mood_configs[mood]
        keywords = mood_config.keywords
        
        # Try each keyword and source until we find a background
        for keyword in keywords:
            for source in self.sources:
                cache_key = self._generate_cache_key(mood, source, keyword)
                
                # Check cache first
                if not force_refresh:
                    cached_result = self._get_from_cache(cache_key)
                    if cached_result:
                        return cached_result
                
                # Try to fetch from API
                if source == BackgroundSource.PEXELS:
                    result = await self._fetch_from_pexels(keyword)
                elif source == BackgroundSource.PIXABAY:
                    result = await self._fetch_from_pixabay(keyword)
                elif source == BackgroundSource.UNSPLASH:
                    result = await self._fetch_from_unsplash(keyword)
                elif source == BackgroundSource.GRADIENT:
                    # Generate gradient image
                    local_path = self._generate_gradient_image(mood)
                    result = BackgroundResult(
                        url=f"gradient://{mood}",
                        local_path=local_path,
                        source=BackgroundSource.GRADIENT,
                        width=3840,
                        height=2160,
                        mood=mood,
                        cache_key=cache_key
                    )
                    self._save_to_cache(result)
                    self.stats["successful"] += 1
                
                if result:
                    # Process the image
                    processed_path = self._process_image(result.local_path, mood)
                    if processed_path != result.local_path:
                        result.local_path = processed_path
                    return result
        
        logger.error(f"Failed to find background for mood '{mood}'")
        self.stats["failed"] += 1
        return None
    
    async def get_batch_backgrounds(self, moods: List[str], interval: float = 5.0) -> List[BackgroundResult]:
        """
        Get backgrounds for multiple scenes with timing.
        
        Args:
            moods: List of moods to get backgrounds for
            interval: Time interval between downloads in seconds
            
        Returns:
            List of BackgroundResult objects
        """
        results = []
        
        for i, mood in enumerate(moods):
            logger.info(f"Getting background for mood '{mood}' ({i + 1}/{len(moods)})")
            
            result = await self.get_background(mood)
            if result:
                results.append(result)
                logger.info(f"Got background from {result.source.value} for mood '{mood}'")
            else:
                logger.error(f"Failed to get background for mood '{mood}'")
            
            # Wait between requests except for the last one
            if i < len(moods) - 1:
                await asyncio.sleep(interval)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about background matching."""
        return self.stats.copy()
    
    def clear_cache(self):
        """Clear the background cache."""
        self.cache.clear()
        logger.info("Background cache cleared")
    
    async def cleanup_old_cache(self, max_age_hours: float = 24.0):
        """Clean up old cache entries."""
        current_time = time.time()
        keys_to_delete = []
        
        for cache_key, result in self.cache.items():
            if current_time - result.downloaded_at > max_age_hours * 3600:
                keys_to_delete.append(cache_key)
        
        for key in keys_to_delete:
            del self.cache[key]
        
        if keys_to_delete:
            logger.info(f"Cleaned up {len(keys_to_delete)} old cache entries")


# Example usage and testing
async def main():
    """Example usage of BackgroundMatcher."""
    async with BackgroundMatcher() as matcher:
        # Get a single background
        result = await matcher.get_background("angry")
        if result:
            print(f"Got background from {result.source.value}: {result.local_path}")
        
        # Get batch of backgrounds
        moods = ["happy", "sad", "angry", "neutral"]
        results = await matcher.get_batch_backgrounds(moods, interval=2.0)
        
        print(f"Got {len(results)} backgrounds")
        for result in results:
            print(f"  - {result.mood}: {result.source.value} ({result.width}x{result.height})")
        
        # Print statistics
        stats = matcher.get_stats()
        print(f"\nStatistics: {stats}")

if __name__ == "__main__":
    asyncio.run(main())