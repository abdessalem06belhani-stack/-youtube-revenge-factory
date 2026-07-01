import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import edge_tts
from pydub import AudioSegment
import io

logger = logging.getLogger(__name__)

# Voice mapping configuration
VOICE_MAPPING = {
    # English voices
    "angry": "en-GB-SoniaNeural",      # British female, suitable for anger
    "sad": "en-US-JennyNeural",        # American female, suitable for sadness
    "happy": "en-US-AriaNeural",       # American female, suitable for happiness
    "calm": "en-US-GuyNeural",         # American male, suitable for calm
    "excited": "en-US-EthanNeural",    # American male, suitable for excitement
    "neutral": "en-US-AvaNeural",      # American female, neutral tone
    "surprised": "en-US-JennyNeural",  # American female, suitable for surprise
    "fearful": "en-GB-SoniaNeural",    # British female, suitable for fear
    "disgusted": "en-US-JennyNeural",  # American female, suitable for disgust
    "shy": "en-US-AriaNeural",         # American female, suitable for shyness
    "confident": "en-US-GuyNeural",    # American male, suitable for confidence
    
    # Arabic voices
    "arabic_angry": "ar-SA-HamzaNeural",      # Arabic male, suitable for anger
    "arabic_sad": "ar-SA-NouraNeural",        # Arabic female, suitable for sadness
    "arabic_happy": "ar-SA-HamzaNeural",      # Arabic male, suitable for happiness
    "arabic_calm": "ar-SA-NouraNeural",       # Arabic female, suitable for calm
    "arabic_excited": "ar-SA-HamzaNeural",    # Arabic male, suitable for excitement
    "arabic_neutral": "ar-SA-NouraNeural",    # Arabic female, neutral tone
    "arabic_surprised": "ar-SA-HamzaNeural",  # Arabic male, suitable for surprise
    "arabic_fearful": "ar-SA-NouraNeural",    # Arabic female, suitable for fear
    "arabic_disgusted": "ar-SA-HamzaNeural",  # Arabic male, suitable for disgust
    "arabic_shy": "ar-SA-NouraNeural",        # Arabic female, suitable for shyness
    "arabic_confident": "ar-SA-HamzaNeural",  # Arabic male, suitable for confidence
}

# Fallback voice mapping for each language
FALLBACK_VOICES = {
    "en-GB-SoniaNeural": "en-US-AvaNeural",  # Fallback to American female
    "en-US-JennyNeural": "en-US-AvaNeural",  # Fallback to American female
    "en-US-AriaNeural": "en-US-AvaNeural",   # Fallback to American female
    "en-US-GuyNeural": "en-US-AvaNeural",    # Fallback to American female
    "en-US-EthanNeural": "en-US-AvaNeural",  # Fallback to American female
    "ar-SA-HamzaNeural": "ar-SA-NouraNeural", # Fallback to Arabic female
    "ar-SA-NouraNeural": "ar-SA-HamzaNeural", # Fallback to Arabic male
}

# Default voice for unknown moods
DEFAULT_VOICE = "en-US-AvaNeural"
DEFAULT_ARABIC_VOICE = "ar-SA-NouraNeural"

# Cache directory
CACHE_DIR = Path("cache/tts")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class AudioSegmentInfo:
    """Information about an audio segment."""
    text: str
    voice: str
    duration: float
    start_time: float = 0.0
    mood: Optional[str] = None
    speed: float = 1.0
    emphasis: bool = False
    pause_before: float = 0.0
    pause_after: float = 0.0
    cache_key: Optional[str] = None

@dataclass
class TTSConfig:
    """Configuration for TTS engine."""
    voice: str = DEFAULT_VOICE
    rate: int = 0  # 0 = normal, -10 = slower, +10 = faster
    volume: int = 100  # 0-100
    pitch: int = 0  # 0 = normal, -10 = lower, +10 = higher
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    fallback_enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30
    enable_ssml: bool = True
    arabic_support: bool = True

class TTEngineError(Exception):
    """Base exception for TTS engine errors."""
    pass

class VoiceNotFoundError(TTEngineError):
    """Raised when a voice is not found."""
    pass

class AudioGenerationError(TTEngineError):
    """Raised when audio generation fails."""
    pass

class TTSEngine:
    """
    Production-ready TTS engine using Edge-TTS.
    
    Features:
    - Async TTS generation with edge-tts
    - Voice mapping: mood → voice (e.g., angry=en-GB-SoniaNeural, sad=en-US-JennyNeural, happy=en-US-AriaNeural)
    - Generate audio segments per scene with timing
    - Concatenate segments into final narration audio
    - Caching to avoid re-generating same text
    - Arabic language support (ar-SA voices)
    - SSML tags for pauses, emphasis, and speed control
    - Error handling and fallback voices
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """
        Initialize the TTS engine.
        
        Args:
            config: TTS configuration. If None, uses default configuration.
        """
        self.config = config or TTSConfig()
        self._voice_cache: Dict[str, str] = {}  # cache_key -> voice mapping
        self._cache_index: Dict[str, Dict] = {}  # cache_key -> metadata
        
        logger.info(f"TTS Engine initialized with voice: {self.config.voice}")
    
    def _get_cache_key(self, text: str, voice: str, config: TTSConfig) -> str:
        """
        Generate a cache key for the given parameters.
        
        Args:
            text: The text to synthesize
            voice: The voice to use
            config: TTS configuration
            
        Returns:
            Cache key string
        """
        # Create a hash of the text and config
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        config_str = f"{voice}_{config.rate}_{config.volume}_{config.pitch}"
        config_hash = hashlib.md5(config_str.encode('utf-8')).hexdigest()
        
        return f"{text_hash}_{config_hash}"
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """
        Get the cache file path for a given cache key.
        
        Args:
            cache_key: The cache key
            
        Returns:
            Path to the cache file
        """
        return CACHE_DIR / f"{cache_key}.mp3"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if a cache entry is still valid.
        
        Args:
            cache_key: The cache key
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not self.config.cache_enabled:
            return False
        
        cache_file = self._get_cache_file_path(cache_key)
        if not cache_file.exists():
            return False
        
        # Check if cache is expired
        file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age_hours = (datetime.now() - file_mtime).total_seconds() / 3600
        
        return age_hours < self.config.cache_ttl_hours
    
    def _save_to_cache(self, cache_key: str, audio_data: bytes) -> None:
        """
        Save audio data to cache.
        
        Args:
            cache_key: The cache key
            audio_data: The audio data to cache
        """
        if not self.config.cache_enabled:
            return
        
        cache_file = self._get_cache_file_path(cache_key)
        
        try:
            with open(cache_file, 'wb') as f:
                f.write(audio_data)
            
            # Update cache index
            self._cache_index[cache_key] = {
                "timestamp": datetime.now().isoformat(),
                "size": len(audio_data),
                "voice": self.config.voice
            }
            
            # Save cache index
            index_file = CACHE_DIR / "index.json"
            with open(index_file, 'w') as f:
                json.dump(self._cache_index, f, indent=2)
            
            logger.debug(f"Saved audio to cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
    
    def _load_from_cache(self, cache_key: str) -> Optional[bytes]:
        """
        Load audio data from cache.
        
        Args:
            cache_key: The cache key
            
        Returns:
            Audio data if found and valid, None otherwise
        """
        if not self.config.cache_enabled:
            return None
        
        if not self._is_cache_valid(cache_key):
            return None
        
        cache_file = self._get_cache_file_path(cache_key)
        
        try:
            with open(cache_file, 'rb') as f:
                audio_data = f.read()
            
            logger.debug(f"Loaded audio from cache: {cache_key}")
            return audio_data
        except Exception as e:
            logger.warning(f"Failed to load from cache: {e}")
            return None
    
    def _get_voice_for_mood(self, mood: str, language: str = "en") -> str:
        """
        Get the voice for a given mood and language.
        
        Args:
            mood: The mood (e.g., "angry", "happy", "sad")
            language: The language ("en" for English, "ar" for Arabic)
            
        Returns:
            Voice name
            
        Raises:
            VoiceNotFoundError: If no voice is found for the mood
        """
        # Normalize mood
        mood = mood.lower().strip()
        
        # Check cache first
        cache_key = f"{mood}_{language}"
        if cache_key in self._voice_cache:
            return self._voice_cache[cache_key]
        
        # Get voice mapping based on language
        if language == "ar":
            # Arabic voices
            voice_key = f"arabic_{mood}"
            if voice_key in VOICE_MAPPING:
                voice = VOICE_MAPPING[voice_key]
                self._voice_cache[cache_key] = voice
                return voice
        else:
            # English voices
            if mood in VOICE_MAPPING:
                voice = VOICE_MAPPING[mood]
                self._voice_cache[cache_key] = voice
                return voice
        
        # Try to find a voice with similar mood
        for mood_key, voice in VOICE_MAPPING.items():
            if mood in mood_key or mood_key in mood:
                self._voice_cache[cache_key] = voice
                return voice
        
        # Use default voice
        if language == "ar":
            voice = DEFAULT_ARABIC_VOICE
        else:
            voice = DEFAULT_VOICE
        
        self._voice_cache[cache_key] = voice
        logger.warning(f"No voice found for mood '{mood}', using default: {voice}")
        return voice
    
    def _create_ssml(self, text: str, voice: str, config: TTSConfig) -> str:
        """
        Create SSML (Speech Synthesis Markup Language) for the given text.
        
        Args:
            text: The text to synthesize
            voice: The voice to use
            config: TTS configuration
            
        Returns:
            SSML string
        """
        if not config.enable_ssml:
            return text
        
        # Split text into sentences for better prosody
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        ssml_parts = []
        for i, sentence in enumerate(sentences):
            if not sentence:
                continue
            
            # Create SSML for this sentence
            ssml = f"<speak><voice name='{voice}'>"
            
            # Add rate, volume, and pitch
            if config.rate != 0:
                ssml += f"<prosody rate='{config.rate}%'>"
            if config.volume != 100:
                ssml += f"<volume level='{config.volume}%'/>"
            if config.pitch != 0:
                ssml += f"<pitch level='{config.pitch}%'>"
            
            # Add emphasis if needed
            if config.emphasis:
                ssml += f"<emphasis>{sentence}</emphasis>"
            else:
                ssml += sentence
            
            # Close prosody and pitch tags
            if config.pitch != 0:
                ssml += "</pitch>"
            if config.rate != 0:
                ssml += "</prosody>"
            
            ssml += f"</voice></speak>"
            
            # Add pause after sentence (except last)
            if i < len(sentences) - 1:
                ssml += "<break time='500ms'/>"
            
            ssml_parts.append(ssml)
        
        return " ".join(ssml_parts)
    
    async def _generate_audio_with_retry(self, text: str, voice: str, config: TTSConfig) -> bytes:
        """
        Generate audio with retry logic.
        
        Args:
            text: The text to synthesize
            voice: The voice to use
            config: TTS configuration
            
        Returns:
            Audio data as bytes
            
        Raises:
            AudioGenerationError: If audio generation fails after all retries
        """
        last_error = None
        
        for attempt in range(config.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{config.max_retries} to generate audio")
                
                # Create SSML if enabled
                ssml_text = self._create_ssml(text, voice, config)
                
                # Generate audio using edge-tts
                communicate = edge_tts.Communicate(
                    ssml_text if config.enable_ssml else text,
                    voice,
                    rate=f"{config.rate}%",
                    volume=f"{config.volume}%",
                    pitch=f"{config.pitch}%"
                )
                
                # Get audio data using a temp file
                temp_path = f"temp_{attempt}_{int(time.time())}.mp3"
                await communicate.save(
                    temp_path,
                    bitrate="128k",
                    timeout=config.timeout_seconds
                )
                
                # Read the generated file
                with open(temp_path, "rb") as f:
                    audio_bytes = f.read()
                
                # Clean up temp file
                os.remove(temp_path)
                
                logger.debug(f"Successfully generated audio on attempt {attempt + 1}")
                return audio_bytes
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # Clean up temp file if it exists
                temp_path = f"temp_{attempt}_{int(time.time())}.mp3"
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                
                # If this is the last attempt, try fallback voice
                if attempt == config.max_retries - 1 and config.fallback_enabled:
                    logger.info(f"Trying fallback voice for {voice}")
                    fallback_voice = FALLBACK_VOICES.get(voice, DEFAULT_VOICE)
                    
                    try:
                        communicate = edge_tts.Communicate(
                            text,
                            fallback_voice,
                            rate=f"{config.rate}%",
                            volume=f"{config.volume}%",
                            pitch=f"{config.pitch}%"
                        )
                        
                        fallback_path = f"temp_fallback_{attempt}_{int(time.time())}.mp3"
                        await communicate.save(
                            fallback_path,
                            bitrate="128k",
                            timeout=config.timeout_seconds
                        )
                        
                        with open(fallback_path, "rb") as f:
                            audio_bytes = f.read()
                        
                        os.remove(fallback_path)
                        
                        logger.info(f"Successfully generated audio with fallback voice: {fallback_voice}")
                        return audio_bytes
                        
                    except Exception as fallback_error:
                        logger.error(f"Fallback voice also failed: {fallback_error}")
                        last_error = fallback_error
                        
                        if os.path.exists(fallback_path):
                            try:
                                os.remove(fallback_path)
                            except OSError:
                                pass
        
        raise AudioGenerationError(f"Failed to generate audio after {config.max_retries} attempts. Last error: {last_error}")
    
    async def generate_audio(
        self,
        text: str,
        mood: Optional[str] = None,
        language: str = "en",
        config: Optional[TTSConfig] = None
    ) -> Tuple[bytes, AudioSegmentInfo]:
        """
        Generate audio from text.
        
        Args:
            text: The text to synthesize
            mood: The mood (e.g., "angry", "happy", "sad"). If None, uses neutral voice.
            language: The language ("en" for English, "ar" for Arabic)
            config: TTS configuration. If None, uses engine configuration.
            
        Returns:
            Tuple of (audio_data, audio_info)
            
        Raises:
            TTEngineError: If audio generation fails
        """
        if not text.strip():
            raise TTEngineError("Text cannot be empty")
        
        # Use provided config or engine config
        tts_config = config or self.config
        
        # Determine voice based on mood and language
        if mood:
            voice = self._get_voice_for_mood(mood, language)
        else:
            voice = tts_config.voice
        
        # Generate cache key
        cache_key = self._get_cache_key(text, voice, tts_config)
        
        # Try to load from cache
        cached_audio = self._load_from_cache(cache_key)
        if cached_audio is not None:
            logger.debug(f"Loaded audio from cache: {cache_key}")
            audio_info = AudioSegmentInfo(
                text=text,
                voice=voice,
                duration=0.0,  # Unknown from cache
                mood=mood,
                speed=1.0,
                emphasis=False,
                pause_before=0.0,
                pause_after=0.0,
                cache_key=cache_key
            )
            return cached_audio, audio_info
        
        # Generate audio
        try:
            audio_data = await self._generate_audio_with_retry(text, voice, tts_config)
            
            # Save to cache
            self._save_to_cache(cache_key, audio_data)
            
            # Create audio info
            audio_info = AudioSegmentInfo(
                text=text,
                voice=voice,
                duration=0.0,  # Will be calculated later
                mood=mood,
                speed=1.0,
                emphasis=False,
                pause_before=0.0,
                pause_after=0.0,
                cache_key=cache_key
            )
            
            logger.debug(f"Generated audio for text: {text[:50]}...")
            return audio_data, audio_info
            
        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            raise AudioGenerationError(f"Failed to generate audio: {e}")
    
    async def generate_segments(
        self,
        segments: List[AudioSegmentInfo],
        config: Optional[TTSConfig] = None
    ) -> List[Tuple[bytes, AudioSegmentInfo]]:
        """
        Generate audio for multiple segments.
        
        Args:
            segments: List of audio segment info
            config: TTS configuration. If None, uses engine configuration.
            
        Returns:
            List of (audio_data, audio_info) tuples
        """
        tts_config = config or self.config
        results = []
        
        for segment in segments:
            try:
                logger.debug(f"Generating audio for segment: {segment.text[:50]}...")
                audio_data, audio_info = await self.generate_audio(
                    text=segment.text,
                    mood=segment.mood,
                    language="ar" if "arabic" in segment.mood.lower() else "en",
                    config=tts_config
                )
                results.append((audio_data, audio_info))
            except Exception as e:
                logger.error(f"Failed to generate audio for segment: {e}")
                # Create empty audio segment as fallback
                empty_audio = b""
                results.append((empty_audio, segment))
        
        return results
    
    def concatenate_audio(
        self,
        audio_segments: List[AudioSegment],
        pauses: Optional[List[float]] = None
    ) -> AudioSegment:
        """
        Concatenate audio segments with optional pauses.
        
        Args:
            audio_segments: List of AudioSegment objects
            pauses: List of pause durations in milliseconds between segments
            
        Returns:
            Concatenated audio segment
        """
        if not audio_segments:
            return AudioSegment.empty()
        
        # Start with the first segment
        result = audio_segments[0]
        
        # Add pauses and subsequent segments
        pause_index = 0
        for i, segment in enumerate(audio_segments[1:], 1):
            if pauses and pause_index < len(pauses):
                pause = AudioSegment.silent(duration=pauses[pause_index])
                result = result + pause
                pause_index += 1
            
            result = result + segment
        
        return result
    
    async def generate_narration(
        self,
        segments: List[AudioSegmentInfo],
        output_path: Optional[Union[str, Path]] = None,
        config: Optional[TTSConfig] = None
    ) -> Tuple[AudioSegment, List[AudioSegmentInfo]]:
        """
        Generate complete narration audio from segments.
        
        Args:
            segments: List of audio segment info
            output_path: Path to save the final audio. If None, not saved.
            config: TTS configuration. If None, uses engine configuration.
            
        Returns:
            Tuple of (final_audio_segment, list_of_audio_infos)
        """
        tts_config = config or self.config
        
        # Generate audio for all segments
        logger.info(f"Generating audio for {len(segments)} segments")
        audio_results = await self.generate_segments(segments, tts_config)
        
        # Convert bytes to AudioSegment objects
        audio_segments = []
        audio_infos = []
        
        for audio_data, audio_info in audio_results:
            if audio_data:
                # Convert bytes to AudioSegment
                audio_segment = AudioSegment.from_file(
                    io.BytesIO(audio_data),
                    format="mp3"
                )
                audio_segments.append(audio_segment)
                audio_infos.append(audio_info)
            else:
                logger.warning(f"Empty audio data for segment: {audio_info.text[:50]}...")
        
        # Calculate pauses based on segment info
        pauses = []
        for audio_info in audio_infos:
            if audio_info.pause_after > 0:
                pauses.append(audio_info.pause_after * 1000)  # Convert to milliseconds
        
        # Concatenate all segments
        final_audio = self.concatenate_audio(audio_segments, pauses)
        
        # Save to file if output_path is provided
        if output_path:
            output_path = Path(output_path)
            final_audio.export(output_path, format="mp3")
            logger.info(f"Saved narration to: {output_path}")
        
        return final_audio, audio_infos
    
    def clear_cache(self) -> None:
        """Clear all cached audio files."""
        if CACHE_DIR.exists():
            for cache_file in CACHE_DIR.glob("*.mp3"):
                cache_file.unlink()
            
            # Clear cache index
            index_file = CACHE_DIR / "index.json"
            if index_file.exists():
                index_file.unlink()
            
            self._cache_index.clear()
            logger.info("Cleared TTS cache")
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not CACHE_DIR.exists():
            return {"total_files": 0, "total_size": 0, "cache_enabled": self.config.cache_enabled}
        
        total_files = 0
        total_size = 0
        
        for cache_file in CACHE_DIR.glob("*.mp3"):
            total_files += 1
            total_size += cache_file.stat().st_size
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_enabled": self.config.cache_enabled,
            "cache_ttl_hours": self.config.cache_ttl_hours
        }


# Example usage
async def example_usage():
    """Example usage of the TTSEngine."""
    # Create engine with custom configuration
    config = TTSConfig(
        voice="en-US-AriaNeural",
        rate=-10,  # Slower
        volume=100,
        pitch=0,
        cache_enabled=True,
        fallback_enabled=True
    )
    
    engine = TTSEngine(config)
    
    # Generate audio for a single segment
    text = "Hello, this is a test of the TTS engine."
    mood = "happy"
    
    audio_data, audio_info = await engine.generate_audio(text, mood)
    print(f"Generated audio: {len(audio_data)} bytes")
    print(f"Voice used: {audio_info.voice}")
    print(f"Mood: {audio_info.mood}")
    
    # Generate audio for multiple segments
    segments = [
        AudioSegmentInfo(text="First segment of the narration.", mood="calm"),
        AudioSegmentInfo(text="Second segment with emphasis.", mood="excited", emphasis=True),
        AudioSegmentInfo(text="Third segment for the conclusion.", mood="happy"),
    ]
    
    final_audio, audio_infos = await engine.generate_narration(segments)
    print(f"Generated narration: {len(final_audio)} samples")
    
    # Get cache statistics
    stats = engine.get_cache_stats()
    print(f"Cache stats: {stats}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())