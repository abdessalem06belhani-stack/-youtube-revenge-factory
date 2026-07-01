"""
Pytest tests for ChannelAnalyzer class.
Tests use unittest.mock to mock external APIs.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.channel_analyzer import ChannelAnalyzer, ChannelAnalysis, CompetitorVideo


class TestChannelAnalyzer:
    """Test suite for ChannelAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.analyzer = ChannelAnalyzer()
    
    def test_analyze_channel_valid_url(self):
        """Test analyze_channel() with valid URL - mock response."""
        # Mock the channel URL extraction
        with patch.object(self.analyzer, '_extract_channel_id') as mock_extract:
            mock_extract.return_value = "UC123456789"
            
            # Mock channel info response
            with patch.object(self.analyzer, '_get_channel_info') as mock_channel_info:
                mock_channel_info.return_value = {
                    "title": "Test Channel",
                    "subscriberCount": 10000,
                    "viewCount": 500000,
                    "videoCount": 100
                }
                
                # Mock top videos response
                with patch.object(self.analyzer, '_get_channel_top_videos') as mock_top_videos:
                    mock_top_videos.return_value = [
                        CompetitorVideo(
                            video_id="video1",
                            title="Test Video 1",
                            description="Test description 1",
                            view_count=1000,
                            like_count=100,
                            comment_count=10,
                            publish_date="2023-01-01",
                            duration_sec=300,
                            tags=["test", "video"],
                            thumbnail_url="http://example.com/thumb1.jpg",
                            engagement_rate=10.0
                        ),
                        CompetitorVideo(
                            video_id="video2",
                            title="Test Video 2",
                            description="Test description 2",
                            view_count=2000,
                            like_count=200,
                            comment_count=20,
                            publish_date="2023-01-02",
                            duration_sec=360,
                            tags=["test", "video"],
                            thumbnail_url="http://example.com/thumb2.jpg",
                            engagement_rate=15.0
                        )
                    ]
                    
                    # Mock pattern extraction methods
                    with patch.object(self.analyzer, '_extract_common_tags') as mock_tags:
                        mock_tags.return_value = ["test", "video", "channel"]
                        
                        with patch.object(self.analyzer, '_extract_title_patterns') as mock_patterns:
                            mock_patterns.return_value = ["Story — Twist", "Question Hook"]
                            
                            with patch.object(self.analyzer, '_extract_description_pattern') as mock_desc_pattern:
                                mock_desc_pattern.return_value = "Sample description pattern"
                                
                                with patch.object(self.analyzer, '_estimate_posting_frequency') as mock_freq:
                                    mock_freq.return_value = "1 video/day"
                                    
                                    # Call the method
                                    result = self.analyzer.analyze_channel("https://youtube.com/channel/UC123456789")
                                    
                                    # Assertions
                                    assert result is not None
                                    assert isinstance(result, ChannelAnalysis)
                                    assert result.channel_id == "UC123456789"
                                    assert result.channel_name == "Test Channel"
                                    assert result.subscriber_count == 10000
                                    assert len(result.top_videos) == 2
                                    assert len(result.common_tags) == 3
                                    assert len(result.title_patterns) == 2
                                    assert result.description_pattern == "Sample description pattern"
                                    assert result.posting_frequency == "1 video/day"
    
    def test_analyze_channel_invalid_url(self):
        """Test analyze_channel() with invalid URL."""
        with patch.object(self.analyzer, '_extract_channel_id') as mock_extract:
            mock_extract.return_value = None
            
            result = self.analyzer.analyze_channel("invalid_url")
            assert result is None
    
    def test_analyze_channel_no_channel_info(self):
        """Test analyze_channel() when channel info is not available."""
        with patch.object(self.analyzer, '_extract_channel_id') as mock_extract:
            mock_extract.return_value = "UC123456789"
            
            with patch.object(self.analyzer, '_get_channel_info') as mock_channel_info:
                mock_channel_info.return_value = None
                
                result = self.analyzer.analyze_channel("https://youtube.com/channel/UC123456789")
                assert result is None
    
    def test_find_trending_videos(self):
        """Test find_trending_videos() - mock YouTube API response."""
        # Mock requests.get for search API
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": {"videoId": "video1"},
                    "snippet": {
                        "title": "Trending Video 1",
                        "description": "Description 1",
                        "publishedAt": "2023-01-01",
                        "thumbnails": {"high": {"url": "http://example.com/thumb1.jpg"}},
                        "tags": ["trending", "video"]
                    }
                },
                {
                    "id": {"videoId": "video2"},
                    "snippet": {
                        "title": "Trending Video 2",
                        "description": "Description 2",
                        "publishedAt": "2023-01-02",
                        "thumbnails": {"high": {"url": "http://example.com/thumb2.jpg"}},
                        "tags": ["trending", "video"]
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        # Mock _get_video_stats
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.analyzer, '_get_video_stats') as mock_stats:
                mock_stats.side_effect = [
                    {"viewCount": 15000, "likeCount": 500, "commentCount": 50},
                    {"viewCount": 12000, "likeCount": 400, "commentCount": 40}
                ]
                
                with patch.object(self.analyzer, '_get_video_duration') as mock_duration:
                    mock_duration.side_effect = [300, 360]
                    
                    # Call the method
                    result = self.analyzer.find_trending_videos(["revenge story", "family drama"], min_views=10000)
                    
                    # Assertions
                    assert len(result) == 2
                    assert all(isinstance(v, CompetitorVideo) for v in result)
                    assert result[0].view_count >= 10000
                    assert result[0].title == "Trending Video 1"
                    assert result[0].engagement_rate > 0
    
    def test_find_trending_videos_no_results(self):
        """Test find_trending_videos() with no matching videos."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            result = self.analyzer.find_trending_videos(["nonexistent"], min_views=10000)
            assert result == []
    
    def test_extract_hashtags(self):
        """Test extract_hashtags() - verify parsing from video description."""
        videos = [
            CompetitorVideo(
                video_id="video1",
                title="Test Video",
                description="#trending #viral #youtube #test #video",
                view_count=1000,
                like_count=100,
                comment_count=10,
                publish_date="2023-01-01",
                duration_sec=300,
                tags=["trending", "viral", "youtube"],
                thumbnail_url="http://example.com/thumb.jpg",
                engagement_rate=10.0
            ),
            CompetitorVideo(
                video_id="video2",
                title="Test Video 2",
                description="#test #video #trending #new",
                view_count=2000,
                like_count=200,
                comment_count=20,
                publish_date="2023-01-02",
                duration_sec=360,
                tags=["test", "video"],
                thumbnail_url="http://example.com/thumb2.jpg",
                engagement_rate=15.0
            )
        ]
        
        result = self.analyzer.extract_hashtags(videos)
        
        # Assertions
        assert isinstance(result, dict)
        assert "trending" in result
        assert "viral" in result
        assert "youtube" in result
        assert "test" in result
        assert "video" in result
        assert "new" in result
        
        # Check counts (actual implementation logic)
        # trending: video1 desc(1) + video1 tags(1) + video2 desc(1) = 3
        # viral: video1 desc(1) + video1 tags(1) = 2
        # youtube: video1 desc(1) + video1 tags(1) = 2
        # test: video1 desc(1) + video2 desc(1) + video2 tags(1) = 3
        # video: video1 desc(1) + video2 desc(1) + video2 tags(1) = 3
        # new: video2 desc(1) = 1
        assert result["trending"] == 3
        assert result["viral"] == 2
        assert result["youtube"] == 2
        assert result["test"] == 3
        assert result["video"] == 3
        assert result["new"] == 1
        
        # Check sorting (highest count first)
        sorted_keys = list(result.keys())
        assert sorted_keys == sorted(sorted_keys, key=lambda x: -result[x])
    
    def test_extract_hashtags_empty_videos(self):
        """Test extract_hashtags() with empty video list."""
        result = self.analyzer.extract_hashtags([])
        assert result == {}
    
    def test_extract_hashtags_no_hashtags(self):
        """Test extract_hashtags() with videos containing no hashtags."""
        videos = [
            CompetitorVideo(
                video_id="video1",
                title="Test Video",
                description="No hashtags here",
                view_count=1000,
                like_count=100,
                comment_count=10,
                publish_date="2023-01-01",
                duration_sec=300,
                tags=["test", "video"],
                thumbnail_url="http://example.com/thumb.jpg",
                engagement_rate=10.0
            )
        ]
        
        result = self.analyzer.extract_hashtags(videos)
        assert result == {"test": 1, "video": 1}
    
    def test_empty_invalid_input_handling(self):
        """Test empty/invalid input handling."""
        # Test with empty string
        with patch.object(self.analyzer, '_extract_channel_id') as mock_extract:
            mock_extract.return_value = None
            result = self.analyzer.analyze_channel("")
            assert result is None
        
        # Test with None (should raise exception)
        with pytest.raises(Exception):
            self.analyzer.analyze_channel(None)
    
    def test_arabic_content_support(self):
        """Test Arabic content support."""
        # Create video with Arabic content in description
        video = CompetitorVideo(
            video_id="video1",
            title="فيديو اختبار",
            description="#اختبار #فيديو #يوتيوب #عربي #تحديات",
            view_count=1000,
            like_count=100,
            comment_count=10,
            publish_date="2023-01-01",
            duration_sec=300,
            tags=["اختبار", "فيديو", "عربي"],
            thumbnail_url="http://example.com/thumb.jpg",
            engagement_rate=10.0
        )
        
        result = self.analyzer.extract_hashtags([video])
        
        # Assertions for Arabic hashtags
        assert "اختبار" in result
        assert "فيديو" in result
        assert "يوتيوب" in result
        assert "عربي" in result
        assert "تحديات" in result
        
        # Check counts (hashtags appear in both description and tags)
        # Each Arabic hashtag appears in description (1) + tags (1) = 2
        assert result["اختبار"] == 2
        assert result["فيديو"] == 2
        assert result["يوتيوب"] == 1
        assert result["عربي"] == 2
        assert result["تحديات"] == 1
    
    def test_generate_seo_package(self):
        """Test generate_seo_package() method."""
        video = CompetitorVideo(
            video_id="video1",
            title="Original Title",
            description="Original description with #hashtags",
            view_count=1000,
            like_count=100,
            comment_count=10,
            publish_date="2023-01-01",
            duration_sec=300,
            tags=["hashtag1", "hashtag2"],
            thumbnail_url="http://example.com/thumb.jpg",
            engagement_rate=10.0
        )
        
        rewritten_title = "Rewritten Title"
        result = self.analyzer.generate_seo_package(video, rewritten_title)
        
        # Assertions
        assert isinstance(result, dict)
        assert result["title"] == rewritten_title
        assert "hashtag1" in result["hashtags"]
        assert "hashtag2" in result["hashtags"]
        assert "hashtags" in result
        assert result["suggested_publish_time"] == "14:00 UTC"
    
    def test_channel_analyzer_initialization(self):
        """Test ChannelAnalyzer initialization."""
        analyzer = ChannelAnalyzer()
        assert analyzer.api_key == ""  # Default empty key
        assert analyzer.base_url == "https://www.googleapis.com/youtube/v3"
    
    def test_channel_analyzer_with_api_key(self):
        """Test ChannelAnalyzer with API key from environment."""
        with patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key_123'}):
            analyzer = ChannelAnalyzer()
            assert analyzer.api_key == "test_key_123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])