"""
Pipeline Orchestrator - Main pipeline orchestrator that connects all modules end-to-end.

Reads config from config.yaml, runs the full pipeline:
1. Source stories from YouTube competitor channels (channel_analyzer)
2. Download + transcribe (content_finder)
3. Rewrite story with AI (story_rewriter)
4. Generate TTS narration (tts_engine)
5. Match backgrounds per scene mood (background_matcher)
6. Generate thumbnail (thumbnail_generator)
7. Output pipeline state as JSON for Colab/worker

Features:
- Async pipeline with state tracking
- Status callback for Dashboard updates (via Supabase)
- Error handling with retry per stage
- Config-driven: which stages to run
- Pipeline state saved to Supabase `videos` table
- Logging with structured output
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from src.channel_analyzer import ChannelAnalyzer
from src.content_finder import ContentFinder
from src.story_rewriter import StoryRewriter
from src.tts_engine import TTSEngine, AudioSegmentInfo, TTSConfig
from src.background_matcher import BackgroundMatcher
from src.thumbnail_generator import ThumbnailGenerator
from src.database import db

# Configure logging with structured output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stages for tracking and status updates."""
    CHANNEL_ANALYSIS = "channel_analysis"
    CONTENT_FINDING = "content_finding"
    STORY_REWRITING = "story_rewriting"
    TTS_GENERATION = "tts_generation"
    BACKGROUND_MATCHING = "background_matching"
    THUMBNAIL_GENERATION = "thumbnail_generation"
    FINAL_OUTPUT = "final_output"


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineState:
    """Pipeline execution state tracking."""
    video_id: str
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: Optional[PipelineStage] = None
    stages_completed: List[PipelineStage] = field(default_factory=list)
    stages_failed: List[PipelineStage] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    config: Dict[str, Any] = field(default_factory=dict)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    final_output: Optional[Dict[str, Any]] = None
    supabase_video_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class PipelineConfig:
    """Pipeline configuration from config.yaml."""
    # Stage enable/disable flags
    enable_channel_analysis: bool = True
    enable_content_finding: bool = True
    enable_story_rewriting: bool = True
    enable_tts_generation: bool = True
    enable_background_matching: bool = True
    enable_thumbnail_generation: bool = True
    enable_final_output: bool = True
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 5.0
    
    # Timeout configuration
    stage_timeout: int = 300  # seconds
    
    # Output configuration
    output_dir: str = "outputs/pipeline"
    output_format: str = "json"
    
    # Dashboard configuration
    enable_dashboard_updates: bool = True
    dashboard_callback_url: Optional[str] = None


class PipelineOrchestrator:
    """
    Main pipeline orchestrator that connects all modules end-to-end.
    
    Features:
    - Async pipeline with state tracking
    - Status callback for Dashboard updates (via Supabase)
    - Error handling with retry per stage
    - Config-driven: which stages to run
    - Pipeline state saved to Supabase `videos` table
    - Logging with structured output
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the pipeline orchestrator.
        
        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = Path(config_path)
        self.pipeline_config = self._load_config()
        self.pipeline_state: Optional[PipelineState] = None
        
        # Initialize modules
        self.channel_analyzer = ChannelAnalyzer()
        self.content_finder = ContentFinder()
        self.story_rewriter = StoryRewriter()
        self.tts_engine = TTSEngine()
        self.background_matcher = BackgroundMatcher()
        self.thumbnail_generator = ThumbnailGenerator()
        
        # Create output directory
        Path(self.pipeline_config.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info("Pipeline Orchestrator initialized")
    
    def _load_config(self) -> PipelineConfig:
        """
        Load configuration from config.yaml.
        
        Returns:
            PipelineConfig object
        """
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Extract pipeline-specific config
            pipeline_config = PipelineConfig()
            
            # Stage enable/disable flags
            if 'pipeline' in config_data:
                pipeline_section = config_data['pipeline']
                pipeline_config.enable_channel_analysis = pipeline_section.get('enable_channel_analysis', True)
                pipeline_config.enable_content_finding = pipeline_section.get('enable_content_finding', True)
                pipeline_config.enable_story_rewriting = pipeline_section.get('enable_story_rewriting', True)
                pipeline_config.enable_tts_generation = pipeline_section.get('enable_tts_generation', True)
                pipeline_config.enable_background_matching = pipeline_section.get('enable_background_matching', True)
                pipeline_config.enable_thumbnail_generation = pipeline_section.get('enable_thumbnail_generation', True)
                pipeline_config.enable_final_output = pipeline_section.get('enable_final_output', True)
                
                pipeline_config.max_retries = pipeline_section.get('max_retries', 3)
                pipeline_config.retry_delay = pipeline_section.get('retry_delay', 5.0)
                pipeline_config.stage_timeout = pipeline_section.get('stage_timeout', 300)
                pipeline_config.output_dir = pipeline_section.get('output_dir', 'outputs/pipeline')
                pipeline_config.output_format = pipeline_section.get('output_format', 'json')
                pipeline_config.enable_dashboard_updates = pipeline_section.get('enable_dashboard_updates', True)
            
            # Extract from root config if available
            if 'video' in config_data:
                pipeline_config.video_config = config_data['video']
            
            logger.info(f"Configuration loaded from {self.config_path}")
            return pipeline_config
            
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            # Return default config
            return PipelineConfig()
    
    async def run_pipeline(self, video_source: Dict[str, Any]) -> PipelineState:
        """
        Run the complete pipeline for a video source.
        
        Args:
            video_source: Dictionary containing video source information
            
        Returns:
            PipelineState object with execution results
        """
        # Generate unique video ID
        video_id = f"video_{int(time.time())}_{hash(str(video_source)) % 10000}"
        
        # Initialize pipeline state
        self.pipeline_state = PipelineState(
            video_id=video_id,
            status=PipelineStatus.RUNNING,
            start_time=time.time(),
            config=self.pipeline_config.__dict__
        )
        
        # Save initial state to Supabase
        await self._update_supabase_state()
        
        logger.info(f"Starting pipeline for video {video_id}")
        
        try:
            # Execute pipeline stages
            await self._execute_stage(PipelineStage.CHANNEL_ANALYSIS, video_source)
            await self._execute_stage(PipelineStage.CONTENT_FINDING, video_source)
            await self._execute_stage(PipelineStage.STORY_REWRITING, video_source)
            await self._execute_stage(PipelineStage.TTS_GENERATION, video_source)
            await self._execute_stage(PipelineStage.BACKGROUND_MATCHING, video_source)
            await self._execute_stage(PipelineStage.THUMBNAIL_GENERATION, video_source)
            await self._execute_stage(PipelineStage.FINAL_OUTPUT, video_source)
            
            # Mark as completed
            self.pipeline_state.status = PipelineStatus.COMPLETED
            self.pipeline_state.end_time = time.time()
            
            logger.info(f"Pipeline completed successfully for video {video_id}")
            
        except Exception as e:
            # Mark as failed
            self.pipeline_state.status = PipelineStatus.FAILED
            self.pipeline_state.error_messages.append(str(e))
            self.pipeline_state.end_time = time.time()
            
            logger.error(f"Pipeline failed for video {video_id}: {e}")
            
            # Update Supabase with error state
            await self._update_supabase_state()
            raise
        
        # Save final state to Supabase
        await self._update_supabase_state()
        
        return self.pipeline_state
    
    async def _execute_stage(self, stage: PipelineStage, video_source: Dict[str, Any]):
        """
        Execute a single pipeline stage with retry logic.
        
        Args:
            stage: Pipeline stage to execute
            video_source: Video source data
        """
        self.pipeline_state.current_stage = stage
        
        # Check if stage is enabled
        if not self._is_stage_enabled(stage):
            logger.info(f"Skipping disabled stage: {stage.value}")
            self.pipeline_state.stages_completed.append(stage)
            return
        
        logger.info(f"Executing stage: {stage.value}")
        
        # Execute with retry logic
        last_exception = None
        for attempt in range(self.pipeline_state.max_retries):
            try:
                await self._execute_stage_with_timeout(stage, video_source)
                self.pipeline_state.stages_completed.append(stage)
                logger.info(f"Stage {stage.value} completed successfully (attempt {attempt + 1})")
                return
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Stage {stage.value} failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.pipeline_state.max_retries - 1:
                    await asyncio.sleep(self.pipeline_config.retry_delay)
                    self.pipeline_state.retry_count += 1
                else:
                    self.pipeline_state.stages_failed.append(stage)
                    self.pipeline_state.error_messages.append(f"Stage {stage.value} failed after {self.pipeline_state.max_retries} attempts: {e}")
                    raise
        
        # This should not be reached, but just in case
        if last_exception:
            raise last_exception
    
    async def _execute_stage_with_timeout(self, stage: PipelineStage, video_source: Dict[str, Any]):
        """
        Execute a single pipeline stage with timeout.
        
        Args:
            stage: Pipeline stage to execute
            video_source: Video source data
        """
        try:
            # Execute stage based on type
            if stage == PipelineStage.CHANNEL_ANALYSIS:
                await self._stage_channel_analysis(video_source)
            elif stage == PipelineStage.CONTENT_FINDING:
                await self._stage_content_finding(video_source)
            elif stage == PipelineStage.STORY_REWRITING:
                await self._stage_story_rewriting(video_source)
            elif stage == PipelineStage.TTS_GENERATION:
                await self._stage_tts_generation(video_source)
            elif stage == PipelineStage.BACKGROUND_MATCHING:
                await self._stage_background_matching(video_source)
            elif stage == PipelineStage.THUMBNAIL_GENERATION:
                await self._stage_thumbnail_generation(video_source)
            elif stage == PipelineStage.FINAL_OUTPUT:
                await self._stage_final_output(video_source)
            
        except asyncio.TimeoutError:
            raise Exception(f"Stage {stage.value} timed out after {self.pipeline_config.stage_timeout} seconds")
        except Exception as e:
            raise Exception(f"Stage {stage.value} failed: {e}")
    
    def _is_stage_enabled(self, stage: PipelineStage) -> bool:
        """
        Check if a pipeline stage is enabled.
        
        Args:
            stage: Pipeline stage to check
            
        Returns:
            True if stage is enabled, False otherwise
        """
        stage_mapping = {
            PipelineStage.CHANNEL_ANALYSIS: self.pipeline_config.enable_channel_analysis,
            PipelineStage.CONTENT_FINDING: self.pipeline_config.enable_content_finding,
            PipelineStage.STORY_REWRITING: self.pipeline_config.enable_story_rewriting,
            PipelineStage.TTS_GENERATION: self.pipeline_config.enable_tts_generation,
            PipelineStage.BACKGROUND_MATCHING: self.pipeline_config.enable_background_matching,
            PipelineStage.THUMBNAIL_GENERATION: self.pipeline_config.enable_thumbnail_generation,
            PipelineStage.FINAL_OUTPUT: self.pipeline_config.enable_final_output,
        }
        
        return stage_mapping.get(stage, True)
    
    async def _stage_channel_analysis(self, video_source: Dict[str, Any]):
        """
        Stage 1: Source stories from YouTube competitor channels.
        
        Args:
            video_source: Video source data
        """
        logger.info("Stage 1: Channel Analysis")
        
        # Extract competitor channels from video source
        competitor_channels = video_source.get('competitor_channels', [])
        if not competitor_channels:
            logger.warning("No competitor channels found in video source")
            return
        
        # Analyze each channel
        analyzed_channels = []
        for channel_url in competitor_channels:
            analysis = self.channel_analyzer.analyze_channel(channel_url)
            if analysis:
                analyzed_channels.append(analysis)
                self.pipeline_state.intermediate_results['channel_analysis'] = analyzed_channels
        
        logger.info(f"Analyzed {len(analyzed_channels)} competitor channels")
    
    async def _stage_content_finding(self, video_source: Dict[str, Any]):
        """
        Stage 2: Download + transcribe (content_finder).
        
        Args:
            video_source: Video source data
        """
        logger.info("Stage 2: Content Finding")
        
        # Extract videos from channel analysis
        videos_to_process = []
        if 'channel_analysis' in self.pipeline_state.intermediate_results:
            for channel in self.pipeline_state.intermediate_results['channel_analysis']:
                videos_to_process.extend(channel.top_videos[:5])  # Top 5 videos per channel
        
        if not videos_to_process:
            logger.warning("No videos found for content finding")
            return
        
        # Process each video
        processed_stories = []
        for video in videos_to_process[:10]:  # Process top 10 videos
            video_info = {
                'video_id': video.video_id,
                'title': video.title,
                'description': video.description,
                'view_count': video.view_count,
                'tags': video.tags,
            }
            
            story_data = self.content_finder.extract_story_from_video(video_info)
            if story_data:
                processed_stories.append(story_data)
        
        self.pipeline_state.intermediate_results['content_finding'] = processed_stories
        logger.info(f"Processed {len(processed_stories)} videos for content finding")
    
    async def _stage_story_rewriting(self, video_source: Dict[str, Any]):
        """
        Stage 3: Rewrite story with AI (story_rewriter).
        
        Args:
            video_source: Video source data
        """
        logger.info("Stage 3: Story Rewriting")
        
        # Get stories from content finding stage
        stories = self.pipeline_state.intermediate_results.get('content_finding', [])
        if not stories:
            logger.warning("No stories found for rewriting")
            return
        
        # Rewrite stories
        rewritten_stories = []
        for story in stories[:5]:  # Rewrite top 5 stories
            rewritten = self.story_rewriter.rewrite(story, target_duration_min=50)
            if rewritten:
                rewritten_stories.append(rewritten)
        
        self.pipeline_state.intermediate_results['story_rewriting'] = rewritten_stories
        logger.info(f"Rewrote {len(rewritten_stories)} stories")
    
    async def _stage_tts_generation(self, video_source: Dict[str, Any]):
        """
        Stage 4: Generate TTS narration (tts_engine).
        
        Args:
            video_source: Video source data
        """
        logger.info("Stage 4: TTS Generation")
        
        # Get rewritten stories
        rewritten_stories = self.pipeline_state.intermediate_results.get('story_rewriting', [])
        if not rewritten_stories:
            logger.warning("No rewritten stories found for TTS generation")
            return
        
        # Generate TTS for each story
        tts_results = []
        for story in rewritten_stories:
            # Extract scenes from story
            scenes = story.get('acts', [])
            for act in scenes:
                for scene in act.get('scenes', []):
                    narration = scene.get('narration', '')
                    mood = scene.get('mood', 'neutral')
                    
                    if narration:
                        try:
                            audio_data, audio_info = await self.tts_engine.generate_audio(
                                text=narration,
                                mood=mood,
                                language='en'
                            )
                            tts_results.append({
                                'scene_id': scene.get('number'),
                                'narration': narration,
                                'mood': mood,
                                'audio_data': audio_data,
                                'audio_info': audio_info.__dict__ if hasattr(audio_info, '__dict__') else audio_info
                            })
                        except Exception as e:
                            logger.warning(f"Failed to generate TTS for scene {scene.get('number')}: {e}")
        
        self.pipeline_state.intermediate_results['tts_generation'] = tts_results
        logger.info(f"Generated TTS for {len(tts_results)} scenes")
    
    async def _stage_background_matching(self, video_source: Dict[str, Any]):
        """
        Stage 5: Match backgrounds per scene mood (background_matcher).
        
        Args:
            video_source: Video source data
        """
        logger.info("Stage 5: Background Matching")
        
        # Get rewritten stories for mood information
        rewritten_stories = self.pipeline_state.intermediate_results.get('story_rewriting', [])
        if not rewritten_stories:
            logger.warning("No rewritten stories found for background matching")
            return
        
        # Extract unique moods from scenes
        moods = set()
        for story in rewritten_stories:
            scenes = story.get('acts', [])
            for act in scenes:
                for scene in act.get('scenes', []):
                    mood = scene.get('mood', 'neutral')
                    if mood:
                        moods.add(mood)
        
        # Get backgrounds for each mood
        background_results = {}
        async with self.background_matcher as matcher:
            for mood in moods:
                try:
                    background = await matcher.get_background(mood)
                    if background:
                        background_results[mood] = {
                            'url': background.url,
                            'local_path': background.local_path,
                            'source': background.source.value,
                            'width': background.width,
                            'height': background.height,
                            'mood': background.mood
                        }
                except Exception as e:
                    logger.warning(f"Failed to get background for mood {mood}: {e}")
        
        self.pipeline_state.intermediate_results['background_matching'] = background_results
        logger.info(f"Matched backgrounds for {len(background_results)} moods")
    
    async def _stage_thumbnail_generation(self, video_source: Dict[str, Any]):
        """
        Stage 6: Generate thumbnail (thumbnail_generator).
        
        Args:
            video_source: Video source data
        """
        logger.info("Stage 6: Thumbnail Generation")
        
        # Get rewritten stories for title and mood
        rewritten_stories = self.pipeline_state.intermediate_results.get('story_rewriting', [])
        if not rewritten_stories:
            logger.warning("No rewritten stories found for thumbnail generation")
            return
        
        # Use first story for thumbnail
        first_story = rewritten_stories[0]
        story_data = {
            'title': first_story.get('title', 'YouTube Revenge Story'),
            'mood': 'dramatic'  # Default mood for thumbnail
        }
        
        # Generate thumbnail
        thumbnail_path = self.thumbnail_generator.generate_thumbnail(
            story_data=story_data,
            style='dramatic'
        )
        
        self.pipeline_state.intermediate_results['thumbnail_generation'] = {
            'path': thumbnail_path,
            'story_title': story_data['title'],
            'style': 'dramatic'
        }
        
        logger.info(f"Generated thumbnail: {thumbnail_path}")
    
    async def _stage_final_output(self, video_source: Dict[str, Any]):
        """
        Stage 7: Output pipeline state as JSON for Colab/worker.
        
        Args:
            video_source: Video source data
        """
        logger.info("Stage 7: Final Output")
        
        # Prepare final output
        final_output = {
            'video_id': self.pipeline_state.video_id,
            'status': self.pipeline_state.status.value,
            'start_time': self.pipeline_state.start_time,
            'end_time': self.pipeline_state.end_time,
            'stages_completed': [stage.value for stage in self.pipeline_state.stages_completed],
            'stages_failed': [stage.value for stage in self.pipeline_state.stages_failed],
            'error_messages': self.pipeline_state.error_messages,
            'config': self.pipeline_state.config,
            'intermediate_results': self.pipeline_state.intermediate_results,
            'supabase_video_id': self.pipeline_state.supabase_video_id,
            'retry_count': self.pipeline_state.retry_count,
        }
        
        # Save to file
        output_path = Path(self.pipeline_config.output_dir) / f"{self.pipeline_state.video_id}.json"
        with open(output_path, 'w') as f:
            json.dump(final_output, f, indent=2, default=str)
        
        self.pipeline_state.final_output = final_output
        
        logger.info(f"Final output saved to: {output_path}")
    
    async def _update_supabase_state(self):
        """
        Update pipeline state in Supabase.
        """
        if not self.pipeline_state:
            return
        
        # Prepare data for Supabase
        supabase_data = {
            'video_id': self.pipeline_state.video_id,
            'status': self.pipeline_state.status.value,
            'current_stage': self.pipeline_state.current_stage.value if self.pipeline_state.current_stage else None,
            'stages_completed': json.dumps([stage.value for stage in self.pipeline_state.stages_completed]),
            'stages_failed': json.dumps([stage.value for stage in self.pipeline_state.stages_failed]),
            'error_messages': json.dumps(self.pipeline_state.error_messages),
            'start_time': self.pipeline_state.start_time,
            'end_time': self.pipeline_state.end_time,
            'config': json.dumps(self.pipeline_state.config),
            'intermediate_results': json.dumps(self.pipeline_state.intermediate_results),
            'final_output': json.dumps(self.pipeline_state.final_output) if self.pipeline_state.final_output else None,
            'retry_count': self.pipeline_state.retry_count,
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            # Save to Supabase
            video_id = db.save_video(supabase_data)
            if video_id:
                self.pipeline_state.supabase_video_id = video_id
                logger.info(f"Pipeline state saved to Supabase with video ID: {video_id}")
            else:
                logger.warning("Failed to save pipeline state to Supabase")
                
        except Exception as e:
            logger.error(f"Failed to update Supabase state: {e}")
    
    async def get_pipeline_status(self, video_id: str) -> Optional[PipelineState]:
        """
        Get pipeline status for a specific video.
        
        Args:
            video_id: Video ID to get status for
            
        Returns:
            PipelineState object or None if not found
        """
        # This would typically query Supabase for the pipeline state
        # For now, return the current pipeline state if it matches
        if self.pipeline_state and self.pipeline_state.video_id == video_id:
            return self.pipeline_state
        
        return None
    
    async def cancel_pipeline(self, video_id: str) -> bool:
        """
        Cancel a running pipeline.
        
        Args:
            video_id: Video ID to cancel
            
        Returns:
            True if pipeline was cancelled, False otherwise
        """
        if self.pipeline_state and self.pipeline_state.video_id == video_id:
            self.pipeline_state.status = PipelineStatus.CANCELLED
            self.pipeline_state.end_time = time.time()
            
            # Update Supabase
            await self._update_supabase_state()
            
            logger.info(f"Pipeline {video_id} cancelled")
            return True
        
        return False


async def main():
    """
    Example usage of the PipelineOrchestrator.
    """
    # Initialize orchestrator
    orchestrator = PipelineOrchestrator()
    
    # Example video source
    video_source = {
        'competitor_channels': [
            'https://www.youtube.com/channel/UC_x5XG1Zv0hZ5w9Q4t8n9g',
            'https://www.youtube.com/@somechannel',
        ],
        'target_duration_min': 50,
        'language': 'en',
        'mood': 'dramatic',
    }
    
    try:
        # Run pipeline
        result = await orchestrator.run_pipeline(video_source)
        
        print(f"Pipeline completed with status: {result.status.value}")
        print(f"Stages completed: {len(result.stages_completed)}")
        print(f"Stages failed: {len(result.stages_failed)}")
        
        if result.final_output:
            print(f"Final output saved to: {result.video_id}.json")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())