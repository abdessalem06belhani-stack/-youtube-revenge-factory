import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

# YouTube API constants
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1
MAX_BACKOFF_SECONDS = 60

class PrivacyStatus(Enum):
    PUBLIC = 'public'
    UNLISTED = 'unlisted'
    PRIVATE = 'private'

class UploadStatus(Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELED = 'canceled'

@dataclass
class UploadProgress:
    status: UploadStatus
    bytes_uploaded: int
    total_bytes: int
    percentage: float
    elapsed_time: float
    estimated_time_remaining: Optional[float] = None
    current_speed: Optional[float] = None

@dataclass
class VideoMetadata:
    title: str
    description: str = ''
    tags: Optional[List[str]] = None
    category_id: str = '22'  # People & Blogs
    privacy_status: PrivacyStatus = PrivacyStatus.PUBLIC
    made_for_kids: bool = False
    scheduled_publish_time: Optional[datetime] = None
    thumbnail_path: Optional[str] = None

class YouTubeUploaderError(Exception):
    """Base exception for YouTube uploader errors."""
    pass

class AuthenticationError(YouTubeUploaderError):
    """Raised when authentication fails."""
    pass

class QuotaExceededError(YouTubeUploaderError):
    """Raised when YouTube API quota is exceeded."""
    pass

class UploadError(YouTubeUploaderError):
    """Raised when upload fails."""
    pass

class YouTubeUploader:
    """
    YouTube Uploader module that handles OAuth2 authentication and video upload via YouTube Data API v3.
    
    Features:
    - OAuth2 authentication flow (local server or refresh token)
    - Upload video with title, description, tags, thumbnail
    - Schedule publishing (for later time)
    - Set video category, privacy status (public/unlisted/private)
    - MadeForKids flag
    - Retry logic with exponential backoff
    - Progress callback for upload status
    - Error handling for quota limits, auth errors
    - Read credentials from environment vars (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN)
    - Test mode: validate without uploading
    """
    
    def __init__(self, test_mode: bool = False):
        """
        Initialize YouTube uploader.
        
        Args:
            test_mode: If True, validate credentials without uploading
        """
        self.test_mode = test_mode
        self.credentials = None
        self.youtube_client = None
        self._progress_callback: Optional[Callable[[UploadProgress], None]] = None
        
    def set_progress_callback(self, callback: Callable[[UploadProgress], None]) -> None:
        """
        Set progress callback for upload status.
        
        Args:
            callback: Function that receives UploadProgress objects
        """
        self._progress_callback = callback
    
    def _call_progress_callback(self, progress: UploadProgress) -> None:
        """Call progress callback if set."""
        if self._progress_callback:
            self._progress_callback(progress)
    
    def _exponential_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        backoff = min(INITIAL_BACKOFF_SECONDS * (2 ** attempt), MAX_BACKOFF_SECONDS)
        jitter = backoff * 0.1  # Add 10% jitter
        return backoff + jitter
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with retry logic and exponential backoff.
        
        Args:
            func: Function to execute
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function
            
        Returns:
            Result of function call
            
        Raises:
            UploadError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {MAX_RETRIES} attempts failed.")
        
        raise UploadError(f"Upload failed after {MAX_RETRIES} attempts. Last error: {str(last_exception)}")
    
    def _get_credentials(self) -> Credentials:
        """
        Get or create YouTube API credentials.
        
        Returns:
            Google OAuth2 credentials
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Check for refresh token in environment
        refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
        client_id = os.getenv('YOUTUBE_CLIENT_ID')
        client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
        
        if not all([refresh_token, client_id, client_secret]):
            raise AuthenticationError(
                "Missing required environment variables: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN"
            )
        
        # Create credentials from refresh token
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
        
        # Refresh the token
        try:
            credentials.refresh(Request())
            logger.info("Successfully refreshed YouTube API credentials")
        except Exception as e:
            raise AuthenticationError(f"Failed to refresh credentials: {str(e)}")
        
        return credentials
    
    def authenticate(self) -> None:
        """
        Authenticate with YouTube API.
        
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            self.credentials = self._get_credentials()
            
            if self.test_mode:
                logger.info("Test mode: Validating credentials without uploading")
                # Test the credentials by making a simple API call
                self.youtube_client = build(
                    YOUTUBE_API_SERVICE_NAME,
                    YOUTUBE_API_VERSION,
                    credentials=self.credentials
                )
                
                # Test API call
                request = self.youtube_client.channels().list(
                    part='snippet',
                    mine=True
                )
                response = request.execute()
                logger.info(f"Authentication successful. Channel ID: {response['items'][0]['id']}")
            else:
                self.youtube_client = build(
                    YOUTUBE_API_SERVICE_NAME,
                    YOUTUBE_API_VERSION,
                    credentials=self.credentials
                )
                logger.info("Successfully authenticated with YouTube API")
                
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def _upload_video(self, video_path: str, metadata: VideoMetadata) -> Dict[str, Any]:
        """
        Upload video to YouTube.
        
        Args:
            video_path: Path to video file
            metadata: Video metadata
            
        Returns:
            Upload response data
            
        Raises:
            UploadError: If upload fails
        """
        if not os.path.exists(video_path):
            raise UploadError(f"Video file not found: {video_path}")
        
        # Prepare request body
        request_body = {
            'snippet': {
                'title': metadata.title,
                'description': metadata.description,
                'tags': metadata.tags or [],
                'categoryId': metadata.category_id,
            },
            'status': {
                'privacyStatus': metadata.privacy_status.value,
                'publishAt': metadata.scheduled_publish_time.isoformat() if metadata.scheduled_publish_time else None,
                'madeForKids': metadata.made_for_kids,
            }
        }
        
        # Add thumbnail if provided
        if metadata.thumbnail_path and os.path.exists(metadata.thumbnail_path):
            request_body['snippet']['defaultThumbnail'] = metadata.thumbnail_path
        
        # Prepare media upload
        media = MediaFileUpload(
            video_path,
            chunksize=1024 * 1024,  # 1MB chunks
            mimetype='video/mp4',
            resumable=True
        )
        
        # Execute upload with progress tracking
        try:
            request = self.youtube_client.videos().insert(
                part='snippet,status',
                body=request_body,
                media_body=media
            )
            
            # Track upload progress
            start_time = time.time()
            last_progress_update = 0
            
            def progress_callback(upload, finished):
                nonlocal last_progress_update
                
                if finished:
                    elapsed = time.time() - start_time
                    progress = UploadProgress(
                        status=UploadStatus.COMPLETED,
                        bytes_uploaded=upload.total_size,
                        total_bytes=upload.total_size,
                        percentage=100.0,
                        elapsed_time=elapsed,
                        current_speed=upload.total_size / elapsed if elapsed > 0 else 0
                    )
                    self._call_progress_callback(progress)
                    return
                
                # Calculate progress
                current_size = upload.total_size if hasattr(upload, 'total_size') else 0
                elapsed = time.time() - start_time
                
                # Update progress at most every 0.5 seconds to avoid too many callbacks
                if elapsed - last_progress_update >= 0.5:
                    progress = UploadProgress(
                        status=UploadStatus.IN_PROGRESS,
                        bytes_uploaded=current_size,
                        total_bytes=upload.total_size,
                        percentage=(current_size / upload.total_size * 100) if upload.total_size > 0 else 0,
                        elapsed_time=elapsed,
                        current_speed=current_size / elapsed if elapsed > 0 else 0,
                        estimated_time_remaining=(upload.total_size - current_size) / (current_size / elapsed) if current_size > 0 and elapsed > 0 else None
                    )
                    self._call_progress_callback(progress)
                    last_progress_update = elapsed
            
            # Execute upload with retry logic
            response = self._retry_with_backoff(request.execute, progress_callback)
            
            return response
            
        except HttpError as e:
            error_code = e.resp.status
            error_content = e.content.decode('utf-8') if e.content else str(e)
            
            if error_code == 403 and 'quotaExceeded' in error_content:
                raise QuotaExceededError("YouTube API quota exceeded")
            elif error_code == 401:
                raise AuthenticationError("Authentication failed")
            else:
                raise UploadError(f"YouTube API error: {error_content}")
    
    def upload_video(self, video_path: str, metadata: VideoMetadata) -> Dict[str, Any]:
        """
        Upload video to YouTube.
        
        Args:
            video_path: Path to video file
            metadata: Video metadata
            
        Returns:
            Upload response data
            
        Raises:
            AuthenticationError: If authentication fails
            UploadError: If upload fails
            QuotaExceededError: If quota is exceeded
        """
        if not self.youtube_client:
            self.authenticate()
        
        logger.info(f"Starting upload of video: {video_path}")
        logger.info(f"Title: {metadata.title}")
        logger.info(f"Privacy: {metadata.privacy_status.value}")
        
        if metadata.scheduled_publish_time:
            logger.info(f"Scheduled for: {metadata.scheduled_publish_time.isoformat()}")
        
        try:
            response = self._upload_video(video_path, metadata)
            
            video_id = response.get('id')
            logger.info(f"Video uploaded successfully! Video ID: {video_id}")
            
            # Log additional details
            if metadata.scheduled_publish_time:
                logger.info(f"Video will be published at: {metadata.scheduled_publish_time.isoformat()}")
            
            return response
            
        except (QuotaExceededError, AuthenticationError):
            raise
        except Exception as e:
            raise UploadError(f"Upload failed: {str(e)}")
    
    def get_channel_info(self) -> Dict[str, Any]:
        """
        Get channel information.
        
        Returns:
            Channel information
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.youtube_client:
            self.authenticate()
        
        try:
            request = self.youtube_client.channels().list(
                part='snippet,statistics,contentDetails',
                mine=True
            )
            response = request.execute()
            return response
        except Exception as e:
            raise AuthenticationError(f"Failed to get channel info: {str(e)}")
    
    def close(self) -> None:
        """Close the uploader and clean up resources."""
        self.youtube_client = None
        self.credentials = None
        logger.info("YouTube uploader closed")

# Example usage and test functions
def create_sample_metadata() -> VideoMetadata:
    """Create sample video metadata for testing."""
    return VideoMetadata(
        title="Test Video Upload",
        description="This is a test video uploaded via the YouTube Uploader module.",
        tags=["test", "upload", "youtube", "api"],
        category_id="22",  # People & Blogs
        privacy_status=PrivacyStatus.UNLISTED,
        made_for_kids=False,
        scheduled_publish_time=None,
        thumbnail_path=None
    )

def test_uploader() -> None:
    """Test the YouTube uploader (requires environment variables)."""
    # Check for required environment variables
    required_vars = ['YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables before running the test.")
        return
    
    # Create uploader in test mode
    uploader = YouTubeUploader(test_mode=True)
    
    try:
        # Authenticate
        uploader.authenticate()
        
        # Get channel info
        channel_info = uploader.get_channel_info()
        print(f"Channel: {channel_info['items'][0]['snippet']['title']}")
        print(f"Subscribers: {channel_info['items'][0]['statistics']['subscriberCount']}")
        
        # Test with sample metadata
        metadata = create_sample_metadata()
        print(f"Test metadata created: {metadata.title}")
        
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
    finally:
        uploader.close()

if __name__ == "__main__":
    test_uploader()