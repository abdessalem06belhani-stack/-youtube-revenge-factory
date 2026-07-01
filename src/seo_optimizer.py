from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from datetime import datetime, timedelta
import random
import re
from enum import Enum
from collections import defaultdict

class Language(Enum):
    ARABIC = "ar"
    ENGLISH = "en"
    BILINGUAL = "both"

class ContentType(Enum):
    REVENGE_STORY = "revenge_story"
    RETRIBUTION = "retribution"
    JUSTICE = "justice"
    VINDICATION = "vindication"

@dataclass
class SEOConfig:
    """Configuration for SEO optimization."""
    target_audience: str
    niche: str
    competitor_tags: List[str] = field(default_factory=list)
    content_type: ContentType = ContentType.REVENGE_STORY
    language: Language = Language.BILINGUAL
    video_length: int = 10  # in minutes
    target_views: int = 100000
    target_engagement_rate: float = 0.05

@dataclass
class VideoMetadata:
    """Input metadata for video optimization."""
    title: str
    description: str
    tags: List[str]
    hashtags: List[str]
    upload_date: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    category: str = "Entertainment"
    language: Language = Language.BILINGUAL

@dataclass
class GeneratedTitle:
    """Generated title with metadata."""
    title: str
    pattern_type: str
    language: Language
    word_count: int
    character_count: int
    seo_score: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class GeneratedDescription:
    """Generated description with metadata."""
    description: str
    word_count: int
    character_count: int
    has_timestamps: bool
    has_cta: bool
    seo_score: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class GeneratedTag:
    """Generated tag with metadata."""
    tag: str
    source: str
    relevance_score: float
    language: Language
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class GeneratedHashtag:
    """Generated hashtag with metadata."""
    hashtag: str
    score: float
    source: str
    is_trending: bool
    language: Language
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SEOPackage:
    """Complete SEO optimization package."""
    video_id: str
    original_metadata: VideoMetadata
    generated_titles: List[GeneratedTitle]
    generated_description: GeneratedDescription
    generated_tags: List[GeneratedTag]
    generated_hashtags: List[GeneratedHashtag]
    best_posting_time: Dict[str, datetime]
    schedule: List[Dict[str, datetime]]
    optimization_score: float
    created_at: datetime = field(default_factory=datetime.now)

class SEOOptimizer:
    """SEO Optimizer module for YouTube revenge-story videos."""
    
    def __init__(self, config: SEOConfig):
        self.config = config
        self.title_patterns = {
            "question": [
                "How I Got Revenge on {villain} - {story_type}",
                "The Day I {action} {person} - My Revenge Story",
                "Why {person} Deserved What They Got - A Revenge Tale",
                "I {action} {person} and Here's What Happened",
                "The Ultimate Revenge on {villain} - My Story"
            ],
            "list": [
                "5 Steps to {action} {person} Perfectly",
                "3 Lessons I Learned {action} {person}",
                "7 Things That Happen When You {action} {person}",
                "4 Ways to {action} {person} Without Regret",
                "6 Secrets to {action} {person} Successfully"
            ],
            "story_hook": [
                "You Won't Believe What I Did to {person}",
                "This {action} Changed Everything - My Revenge Journey",
                "The Night I {action} {person} - Never Forget",
                "I Thought I Was Done - Then I {action} {person}",
                "What Happens When You {action} {person} - The Truth"
            ],
            "emotional": [
                "The Pain of {person} - My Revenge Was Sweet",
                "I Was Broken - Then I {action} {person}",
                "From Hate to Victory - I {action} {person}",
                "The Anger That Led Me to {action} {person}",
                "Justice Served - How I {action} {person}"
            ],
            "comparison": [
                "Why I Chose to {action} {person} Instead of Fighting",
                "The Better Way to {action} {person} - My Experience",
                "Comparing Revenge to Forgiveness - I Chose {action}",
                "Why {action} {person} Was Better Than Expected",
                "The Truth About {action} {person} - What They Don't Tell You"
            ]
        }
        
        self.competitor_patterns = {
            "question": [
                "How to get revenge on someone who wronged you",
                "What happens when you confront your enemy",
                "The best way to get back at someone who betrayed you",
                "How to teach someone a lesson they'll never forget",
                "Why revenge is sweet - real stories"
            ],
            "list": [
                "5 ways to get revenge on a cheating partner",
                "3 steps to exact perfect revenge",
                "7 revenge strategies that actually work",
                "4 methods to get back at someone who lied",
                "6 revenge tactics for broken trust"
            ],
            "story_hook": [
                "I thought I was done - then I got my revenge",
                "The day I got back at my enemy - you won't believe it",
                "This is what happens when you cross me",
                "I was broken, then I found my revenge",
                "The truth about revenge - one woman's story"
            ],
            "emotional": [
                "The anger that led me to get revenge",
                "From victim to avenger - my story",
                "Why revenge feels so good - the psychology",
                "The satisfaction of getting back at someone",
                "How revenge healed my broken heart"
            ],
            "comparison": [
                "Revenge vs justice - which is better",
                "Why revenge is better than forgiveness",
                "The pros and cons of getting revenge",
                "Revenge vs therapy - what actually works",
                "Why revenge is the ultimate empowerment"
            ]
        }
        
        self.engagement_patterns = {
            "high_engagement": [
                "How I Got Revenge on {person} - The Full Story",
                "The Ultimate Revenge on {villain} - My Experience",
                "Why {person} Deserved What They Got - Real Story",
                "I {action} {person} and Here's What Happened",
                "The Night I {action} {person} - Never Forget"
            ],
            "medium_engagement": [
                "5 Steps to {action} {person}",
                "3 Lessons I Learned {action} {person}",
                "7 Things That Happen When You {action} {person}",
                "4 Ways to {action} {person} Without Regret",
                "6 Secrets to {action} {person} Successfully"
            ],
            "low_engagement": [
                "How to {action} {person}",
                "Steps to {action} {person}",
                "Guide to {action} {person}",
                "Tutorial: {action} {person}",
                "How I {action} {person}"
            ]
        }
        
        self.mood_keywords = {
            "revenge": ["revenge", "retribution", "vengeance", "payback", "retaliation"],
            "anger": ["anger", "fury", "rage", "hatred", "bitterness"],
            "justice": ["justice", "fairness", "righteous", "vindication", "retribution"],
            "empowerment": ["empowerment", "strength", "power", "confidence", "determination"],
            "victory": ["victory", "win", "triumph", "success", "conquest"]
        }
        
        self.genre_keywords = {
            "drama": ["drama", "dramatic", "emotional", "intense", "powerful"],
            "thriller": ["thriller", "suspense", "mysterious", "edge", "dangerous"],
            "action": ["action", "fast-paced", "dynamic", "exciting", "adrenaline"],
            "romance": ["romance", "love", "relationship", "intimate", "passionate"],
            "crime": ["crime", "illegal", "secret", "hidden", "underground"]
        }
        
        self.trending_hashtags = [
            "#RevengeStory", "#GetRevenge", "#Vengeance", "#Retribution", "#JusticeServed",
            "#RevengeIsSweet", "#GetBackAtSomeone", "#RevengeMode", "#PaybackTime", "#Retaliation",
            "#RevengeJourney", "#GetRevengeNow", "#RevengeTherapy", "#RevengeTips", "#RevengeAdvice"
        ]
        
        self.niche_hashtags = {
            "business": ["#BusinessRevenge", "#CorporateRetaliation", "#WorkplaceRevenge"],
            "relationship": ["#RelationshipRevenge", "#DatingRevenge", "#LoveRevenge"],
            "family": ["#FamilyRevenge", "#SiblingRevenge", "#ParentRevenge"],
            "social": ["#SocialRevenge", "#OnlineRevenge", "#DigitalRevenge"],
            "legal": ["#LegalRevenge", "#LawRevenge", "#LegalSystem"]
        }
        
        self.engagement_factors = {
            "title_length": {"min": 40, "max": 80, "optimal": 60},
            "description_length": {"min": 200, "max": 1000, "optimal": 500},
            "tag_count": {"min": 15, "max": 30, "optimal": 20},
            "hashtag_count": {"min": 10, "max": 25, "optimal": 15},
            "keyword_density": {"min": 1.0, "max": 3.0, "optimal": 2.0}
        }
        
        self.posting_times = {
            "monday": ["09:00", "12:00", "18:00", "21:00"],
            "tuesday": ["09:00", "14:00", "19:00", "22:00"],
            "wednesday": ["10:00", "15:00", "20:00", "23:00"],
            "thursday": ["09:00", "13:00", "17:00", "21:00"],
            "friday": ["08:00", "12:00", "16:00", "20:00"],
            "saturday": ["10:00", "14:00", "18:00", "22:00"],
            "sunday": ["11:00", "15:00", "19:00", "23:00"]
        }
        
        self.youtube_analytics = {
            "peak_hours": ["12:00-14:00", "18:00-20:00", "21:00-23:00"],
            "weekend_boost": 1.5,
            "weekday_boost": 1.2,
            "month_peak": ["January", "March", "October", "December"],
            "engagement_patterns": {
                "morning": {"views": 0.3, "likes": 0.25, "comments": 0.2},
                "afternoon": {"views": 0.4, "likes": 0.3, "comments": 0.25},
                "evening": {"views": 0.5, "likes": 0.4, "comments": 0.35},
                "night": {"views": 0.6, "likes": 0.5, "comments": 0.45}
            }
        }
    
    def generate_titles(self) -> List[GeneratedTitle]:
        """Generate optimized titles using multiple patterns in Arabic + English."""
        titles = []
        
        # Generate titles for each pattern type
        for pattern_type, templates in self.title_patterns.items():
            for template in templates:
                # Generate in English
                title_en = self._fill_template(template, language="en")
                titles.append(self._create_title(title_en, pattern_type, Language.ENGLISH))
                
                # Generate in Arabic if bilingual
                if self.config.language in [Language.BILINGUAL, Language.ARABIC]:
                    title_ar = self._fill_template(template, language="ar")
                    titles.append(self._create_title(title_ar, pattern_type, Language.ARABIC))
        
        # Add competitor-inspired titles
        for pattern_type, templates in self.competitor_patterns.items():
            for template in templates:
                title_en = self._fill_template(template, language="en")
                titles.append(self._create_title(title_en, f"competitor_{pattern_type}", Language.ENGLISH))
        
        # Add engagement-based titles
        for engagement_type, templates in self.engagement_patterns.items():
            for template in templates:
                title_en = self._fill_template(template, language="en")
                titles.append(self._create_title(title_en, f"engagement_{engagement_type}", Language.ENGLISH))
        
        # Filter and rank titles
        filtered_titles = self._filter_titles(titles)
        ranked_titles = self._rank_titles(filtered_titles)
        
        return ranked_titles[:10]  # Return top 10 titles
    
    def generate_description(self) -> GeneratedDescription:
        """Generate optimized description with timestamps, CTA, and competitor patterns."""
        description_parts = []
        
        # Opening hook
        hooks = [
            "In this video, I share my personal revenge story that changed everything.",
            "You won't believe what I did to {person} - this will blow your mind.",
            "The day I {action} {person} was the best decision I ever made.",
            "I thought I was done with {person} - then I got my revenge.",
            "Justice is sweet - here's how I {action} {person}."
        ]
        
        description_parts.append(random.choice(hooks).format(
            person=self._get_relevant_name(),
            action=self._get_relevant_action()
        ))
        
        # Main story
        story_segments = []
        for _ in range(3):
            segment = self._generate_story_segment()
            story_segments.append(segment)
        
        description_parts.extend(story_segments)
        
        # Add timestamps
        timestamps = self._generate_timestamps()
        description_parts.append("\nTimestamps:")
        for timestamp in timestamps:
            description_parts.append(timestamp)
        
        # Add CTA
        ctas = [
            "If you enjoyed this story, don't forget to like and subscribe for more revenge stories!",
            "Subscribe now and never miss another revenge story!",
            "Share your own revenge stories in the comments below!",
            "Follow me for more stories of justice and revenge!",
            "Don't forget to hit that notification bell for more content!"
        ]
        
        description_parts.append("\n" + random.choice(ctas))
        
        # Add competitor patterns
        competitor_patterns = [
            "Like other revenge stories, this one teaches important lessons.",
            "This story is similar to other viral revenge videos you might have seen.",
            "Compared to other revenge stories, this one has a unique twist.",
            "This revenge story stands out from the typical revenge narratives."
        ]
        
        description_parts.append("\n" + random.choice(competitor_patterns))
        
        # Add hashtags
        hashtags = self.generate_hashtags()
        hashtag_line = "\n" + " ".join([h.hashtag for h in hashtags[:10]])
        description_parts.append(hashtag_line)
        
        # Combine all parts
        description = "\n\n".join(description_parts)
        
        # Calculate SEO score
        seo_score = self._calculate_description_seo_score(description)
        
        return GeneratedDescription(
            description=description,
            word_count=len(description.split()),
            character_count=len(description),
            has_timestamps=True,
            has_cta=True,
            seo_score=seo_score
        )
    
    def generate_tags(self) -> List[GeneratedTag]:
        """Generate optimized tags from keywords, competitor hashtags, mood, and genre."""
        tags = []
        
        # Base tags from config
        for tag in self.config.competitor_tags:
            tags.append(self._create_tag(tag, "competitor"))
        
        # Mood-based tags
        mood = random.choice(list(self.mood_keywords.keys()))
        for keyword in self.mood_keywords[mood]:
            tags.append(self._create_tag(keyword, "mood"))
        
        # Genre-based tags
        genre = random.choice(list(self.genre_keywords.keys()))
        for keyword in self.genre_keywords[genre]:
            tags.append(self._create_tag(keyword, "genre"))
        
        # Content-specific tags
        content_tags = self._generate_content_tags()
        tags.extend(content_tags)
        
        # Trending tags
        trending_tags = random.sample(self.trending_hashtags, min(5, len(self.trending_hashtags)))
        for tag in trending_tags:
            tags.append(self._create_tag(tag, "trending"))
        
        # Niche tags based on config
        if self.config.niche in self.niche_hashtags:
            niche_tags = self.niche_hashtags[self.config.niche]
            for tag in niche_tags:
                tags.append(self._create_tag(tag, "niche"))
        
        # Filter and rank tags
        filtered_tags = self._filter_tags(tags)
        ranked_tags = self._rank_tags(filtered_tags)
        
        return ranked_tags[:20]  # Return top 20 tags
    
    def generate_hashtags(self) -> List[GeneratedHashtag]:
        """Generate score-based hashtags mixing trending + niche, copy+improve competitor tags."""
        hashtags = []
        
        # Copy and improve competitor tags
        for tag in self.config.competitor_tags:
            if tag.startswith("#"):
                improved = self._improve_hashtag(tag)
                hashtags.append(self._create_hashtag(improved, "competitor_improved"))
        
        # Add trending hashtags with scores
        for hashtag in self.trending_hashtags:
            score = random.uniform(0.7, 0.95)
            hashtags.append(self._create_hashtag(hashtag, "trending", score))
        
        # Add niche hashtags
        if self.config.niche in self.niche_hashtags:
            for hashtag in self.niche_hashtags[self.config.niche]:
                score = random.uniform(0.6, 0.85)
                hashtags.append(self._create_hashtag(hashtag, "niche", score))
        
        # Generate original hashtags
        original_hashtags = self._generate_original_hashtags()
        hashtags.extend(original_hashtags)
        
        # Filter and rank hashtags
        filtered_hashtags = self._filter_hashtags(hashtags)
        ranked_hashtags = self._rank_hashtags(filtered_hashtags)
        
        return ranked_hashtags[:15]  # Return top 15 hashtags
    
    def calculate_best_posting_time(self) -> Dict[str, datetime]:
        """Calculate best posting time based on YouTube analytics patterns."""
        best_times = {}
        
        # Get current date
        today = datetime.now()
        
        # Calculate for next 7 days
        for i in range(7):
            day_date = today + timedelta(days=i)
            day_name = day_date.strftime("%A").lower()
            
            if day_name in self.posting_times:
                # Select random time slot for this day
                time_slot = random.choice(self.posting_times[day_name])
                hour, minute = map(int, time_slot.split(":"))
                
                # Adjust based on YouTube analytics
                day_score = 1.0
                if day_name in ["friday", "saturday", "sunday"]:
                    day_score *= self.youtube_analytics["weekend_boost"]
                else:
                    day_score *= self.youtube_analytics["weekday_boost"]
                
                # Adjust based on month
                month = day_date.strftime("%B")
                if month in self.youtube_analytics["month_peak"]:
                    day_score *= 1.2
                
                # Adjust based on time of day
                time_str = f"{hour:02d}:{minute:02d}"
                time_score = 1.0
                if time_str in self.youtube_analytics["peak_hours"]:
                    time_score *= 1.3
                
                # Calculate final score
                final_score = day_score * time_score
                
                best_times[f"{day_name}_{i}"] = {
                    "datetime": day_date.replace(hour=hour, minute=minute, second=0),
                    "score": final_score,
                    "day_name": day_name,
                    "time_slot": time_slot
                }
        
        # Sort by score and return top 4
        sorted_times = sorted(best_times.items(), key=lambda x: x[1]["score"], reverse=True)
        return {k: v["datetime"] for k, v in sorted_times[:4]}
    
    def generate_schedule(self) -> List[Dict[str, datetime]]:
        """Generate 4 slots per day schedule."""
        schedule = []
        
        # Get best posting times
        best_times = self.calculate_best_posting_time()
        
        # Create schedule for next 7 days
        today = datetime.now()
        for i in range(7):
            day_date = today + timedelta(days=i)
            day_name = day_date.strftime("%A").lower()
            
            if day_name in self.posting_times:
                # Select 4 time slots for this day
                time_slots = random.sample(self.posting_times[day_name], min(4, len(self.posting_times[day_name])))
                
                for time_slot in time_slots:
                    hour, minute = map(int, time_slot.split(":"))
                    scheduled_time = day_date.replace(hour=hour, minute=minute, second=0)
                    
                    # Calculate engagement score
                    engagement_score = self._calculate_engagement_score(scheduled_time)
                    
                    schedule.append({
                        "datetime": scheduled_time,
                        "day_name": day_name,
                        "time_slot": time_slot,
                        "engagement_score": engagement_score,
                        "type": "revenge_story"
                    })
        
        return schedule
    
    def optimize(self, video_id: str) -> SEOPackage:
        """Generate complete SEO optimization package."""
        # Generate all components
        titles = self.generate_titles()
        description = self.generate_description()
        tags = self.generate_tags()
        hashtags = self.generate_hashtags()
        best_posting_times = self.calculate_best_posting_time()
        schedule = self.generate_schedule()
        
        # Calculate overall optimization score
        optimization_score = self._calculate_overall_score(titles, description, tags, hashtags)
        
        return SEOPackage(
            video_id=video_id,
            original_metadata=self._create_original_metadata(),
            generated_titles=titles,
            generated_description=description,
            generated_tags=tags,
            generated_hashtags=hashtags,
            best_posting_time=best_posting_times,
            schedule=schedule,
            optimization_score=optimization_score
        )
    
    def _fill_template(self, template: str, language: str) -> str:
        """Fill template with appropriate words based on language."""
        replacements = {
            "person": self._get_relevant_name(),
            "villain": self._get_relevant_villain(),
            "action": self._get_relevant_action(),
            "story_type": self._get_relevant_story_type(),
            "steps": self._get_relevant_steps()
        }
        
        result = template
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", value)
        
        # Translate if needed
        if language == "ar":
            result = self._translate_to_arabic(result)
        
        return result
    
    def _create_title(self, title: str, pattern_type: str, language: Language) -> GeneratedTitle:
        """Create a GeneratedTitle object."""
        word_count = len(title.split())
        char_count = len(title)
        
        # Calculate SEO score based on title characteristics
        seo_score = self._calculate_title_seo_score(title, pattern_type)
        
        return GeneratedTitle(
            title=title,
            pattern_type=pattern_type,
            language=language,
            word_count=word_count,
            character_count=char_count,
            seo_score=seo_score
        )
    
    def _create_tag(self, tag: str, source: str) -> GeneratedTag:
        """Create a GeneratedTag object."""
        # Calculate relevance score
        relevance_score = random.uniform(0.6, 0.95)
        
        # Determine language
        language = Language.ENGLISH
        if self.config.language == Language.BILINGUAL and random.random() > 0.5:
            language = Language.ARABIC
        
        return GeneratedTag(
            tag=tag,
            source=source,
            relevance_score=relevance_score,
            language=language
        )
    
    def _create_hashtag(self, hashtag: str, source: str, score: float = None) -> GeneratedHashtag:
        """Create a GeneratedHashtag object."""
        if score is None:
            score = random.uniform(0.6, 0.95)
        
        # Determine if trending
        is_trending = source == "trending" or random.random() > 0.7
        
        # Determine language
        language = Language.ENGLISH
        if self.config.language == Language.BILINGUAL and random.random() > 0.5:
            language = Language.ARABIC
        
        return GeneratedHashtag(
            hashtag=hashtag,
            score=score,
            source=source,
            is_trending=is_trending,
            language=language
        )
    
    def _get_relevant_name(self) -> str:
        """Get a relevant name for the story."""
        names = ["John", "Sarah", "Mike", "Emma", "David", "Lisa", "Robert", "Jennifer"]
        return random.choice(names)
    
    def _get_relevant_villain(self) -> str:
        """Get a relevant villain name."""
        villains = ["the boss", "the ex", "the neighbor", "the colleague", "the friend"]
        return random.choice(villains)
    
    def _get_relevant_action(self) -> str:
        """Get a relevant action for revenge."""
        actions = ["got back at", "confronted", "stood up to", "defeated", "overcame"]
        return random.choice(actions)
    
    def _get_relevant_story_type(self) -> str:
        """Get a relevant story type."""
        types = ["of betrayal", "of injustice", "of courage", "of determination", "of victory"]
        return random.choice(types)
    
    def _get_relevant_steps(self) -> str:
        """Get relevant steps."""
        steps = ["of revenge", "of justice", "of strategy", "of planning", "of execution"]
        return random.choice(steps)
    
    def _translate_to_arabic(self, text: str) -> str:
        """Translate text to Arabic (simplified)."""
        # Simplified translation for demonstration
        translations = {
            "How I Got Revenge on": "كيف حصلت على انتقام من",
            "The Day I": "اليوم الذي",
            "Why": "لماذا",
            "Deserved": "استحق",
            "What Happens When": "ماذا يحدث عندما",
            "5 Steps to": "5 خطوات إلى",
            "3 Lessons I Learned": "3 دروس تعلمتها",
            "7 Things That Happen": "7 أشياء تحدث",
            "4 Ways to": "4 طرق إلى",
            "6 Secrets to": "6 أسرار إلى",
            "You Won't Believe": "لن تصدق",
            "This": "هذا",
            "Changed Everything": "غير كل شيء",
            "The Night I": "الليلة التي",
            "Never Forget": "لن أنسى أبدًا",
            "The Pain of": "ألم",
            "From Hate to Victory": "من الكراهية إلى النصر",
            "The Anger That": "الغضب الذي",
            "Why Revenge": "لماذا الانتقام",
            "Compared to": "مقارنة بـ",
            "Why Revenge is Better": "لماذا الانتقام أفضل"
        }
        
        result = text
        for en, ar in translations.items():
            result = result.replace(en, ar)
        
        return result
    
    def _generate_story_segment(self) -> str:
        """Generate a story segment."""
        segments = [
            f"I was betrayed by {self._get_relevant_name()}, and I decided to get back at them.",
            f"The moment I realized I was being wronged, I knew I had to take action.",
            f"It wasn't easy, but I planned my revenge carefully and executed it perfectly.",
            f"What seemed like a small injustice turned into a life-changing moment of justice.",
            f"I thought I was done with {self._get_relevant_name()}, but they underestimated me."
        ]
        
        return random.choice(segments)
    
    def _generate_timestamps(self) -> List[str]:
        """Generate timestamps for the description."""
        timestamps = []
        
        segments = [
            ("00:00", "Introduction and hook"),
            ("01:30", "The betrayal story"),
            ("03:45", "Planning the revenge"),
            ("06:20", "The execution"),
            ("08:15", "The aftermath"),
            ("10:00", "Lessons learned")
        ]
        
        return [f"{ts} - {desc}" for ts, desc in segments]
    
    def _generate_content_tags(self) -> List[GeneratedTag]:
        """Generate content-specific tags."""
        content_tags = [
            "revenge story", "true story", "personal experience", "life lesson",
            "justice served", "revenge tips", "how to get revenge", "revenge strategies",
            "betrayal story", "injustice", "courage", "determination", "strength"
        ]
        
        tags = []
        for tag in content_tags:
            tags.append(self._create_tag(tag, "content"))
        
        return tags
    
    def _generate_original_hashtags(self) -> List[GeneratedHashtag]:
        """Generate original hashtags."""
        hashtags = [
            "#RevengeStory", "#GetRevenge", "#Vengeance", "#Justice", "#Retribution",
            "#RevengeIsSweet", "#GetBackAtSomeone", "#RevengeMode", "#PaybackTime",
            "#RevengeJourney", "#RevengeTips", "#RevengeAdvice", "#RevengeTherapy"
        ]
        
        generated = []
        for hashtag in hashtags:
            generated.append(self._create_hashtag(hashtag, "original"))
        
        return generated
    
    def _improve_hashtag(self, hashtag: str) -> str:
        """Improve a hashtag by making it more descriptive or trendy."""
        improvements = {
            "#Revenge": "#RevengeStory",
            "#GetRevenge": "#GetRevengeNow",
            "#Vengeance": "#UltimateVengeance",
            "#Justice": "#JusticeServed",
            "#Retribution": "#PerfectRetribution"
        }
        
        return improvements.get(hashtag, hashtag + "Pro")
    
    def _filter_titles(self, titles: List[GeneratedTitle]) -> List[GeneratedTitle]:
        """Filter titles based on SEO criteria."""
        filtered = []
        
        for title in titles:
            # Check length
            if title.word_count < 5 or title.word_count > 20:
                continue
            
            # Check character count
            if title.character_count > 100:
                continue
            
            # Check for question marks or numbers (good for engagement)
            if "?" not in title.title and not any(c.isdigit() for c in title.title):
                continue
            
            filtered.append(title)
        
        return filtered
    
    def _rank_titles(self, titles: List[GeneratedTitle]) -> List[GeneratedTitle]:
        """Rank titles by SEO score."""
        return sorted(titles, key=lambda x: x.seo_score, reverse=True)
    
    def _filter_tags(self, tags: List[GeneratedTag]) -> List[GeneratedTag]:
        """Filter tags based on relevance and uniqueness."""
        # Remove duplicates
        unique_tags = []
        seen = set()
        
        for tag in tags:
            if tag.tag.lower() not in seen:
                seen.add(tag.tag.lower())
                unique_tags.append(tag)
        
        # Filter by relevance score
        filtered = [tag for tag in unique_tags if tag.relevance_score > 0.7]
        
        return filtered
    
    def _rank_tags(self, tags: List[GeneratedTag]) -> List[GeneratedTag]:
        """Rank tags by relevance score."""
        return sorted(tags, key=lambda x: x.relevance_score, reverse=True)
    
    def _filter_hashtags(self, hashtags: List[GeneratedHashtag]) -> List[GeneratedHashtag]:
        """Filter hashtags based on score and uniqueness."""
        # Remove duplicates
        unique_hashtags = []
        seen = set()
        
        for hashtag in hashtags:
            if hashtag.hashtag.lower() not in seen:
                seen.add(hashtag.hashtag.lower())
                unique_hashtags.append(hashtag)
        
        # Filter by score
        filtered = [hashtag for hashtag in unique_hashtags if hashtag.score > 0.7]
        
        return filtered
    
    def _rank_hashtags(self, hashtags: List[GeneratedHashtag]) -> List[GeneratedHashtag]:
        """Rank hashtags by score."""
        return sorted(hashtags, key=lambda x: x.score, reverse=True)
    
    def _calculate_title_seo_score(self, title: str, pattern_type: str) -> float:
        """Calculate SEO score for a title."""
        score = 0.0
        
        # Length optimization
        word_count = len(title.split())
        if 10 <= word_count <= 15:
            score += 0.3
        elif 8 <= word_count <= 18:
            score += 0.2
        
        # Character count
        if len(title) <= 80:
            score += 0.2
        
        # Pattern type bonus
        if pattern_type in ["question", "list", "story_hook"]:
            score += 0.2
        
        # Contains numbers or questions
        if "?" in title or any(c.isdigit() for c in title):
            score += 0.2
        
        # Language bonus
        if self.config.language == Language.BILINGUAL:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_description_seo_score(self, description: str) -> float:
        """Calculate SEO score for a description."""
        score = 0.0
        
        # Word count
        word_count = len(description.split())
        if 200 <= word_count <= 800:
            score += 0.3
        elif 150 <= word_count <= 1000:
            score += 0.2
        
        # Character count
        if 500 <= len(description) <= 5000:
            score += 0.2
        
        # Has timestamps
        if "Timestamps:" in description:
            score += 0.2
        
        # Has CTA
        if any(word in description.lower() for word in ["subscribe", "like", "share", "follow"]):
            score += 0.2
        
        # Has hashtags
        if "#" in description:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_engagement_score(self, scheduled_time: datetime) -> float:
        """Calculate engagement score for a scheduled time."""
        score = 1.0
        
        # Time of day
        hour = scheduled_time.hour
        if 12 <= hour <= 14 or 18 <= hour <= 20 or 21 <= hour <= 23:
            score *= 1.2
        
        # Day of week
        day_name = scheduled_time.strftime("%A").lower()
        if day_name in ["friday", "saturday", "sunday"]:
            score *= 1.3
        
        return min(score, 2.0)
    
    def _calculate_overall_score(self, titles: List[GeneratedTitle], 
                                description: GeneratedDescription,
                                tags: List[GeneratedTag],
                                hashtags: List[GeneratedHashtag]) -> float:
        """Calculate overall optimization score."""
        title_score = sum(t.seo_score for t in titles) / len(titles) if titles else 0
        desc_score = description.seo_score
        tag_score = sum(t.relevance_score for t in tags) / len(tags) if tags else 0
        hashtag_score = sum(h.score for h in hashtags) / len(hashtags) if hashtags else 0
        
        overall = (title_score * 0.3 + desc_score * 0.3 + 
                  tag_score * 0.2 + hashtag_score * 0.2)
        
        return min(overall, 1.0)
    
    def _create_original_metadata(self) -> VideoMetadata:
        """Create original metadata for the video."""
        return VideoMetadata(
            title="Revenge Story - The Complete Journey",
            description="This is a revenge story about getting back at someone who wronged you.",
            tags=["revenge", "story", "true story"],
            hashtags=["#RevengeStory", "#GetRevenge"],
            language=self.config.language
        )