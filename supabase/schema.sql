-- youtube-revenge-factory Database Schema (مبسطة)
-- 4 جداول فقط

-- 1. SETTINGS: إعدادات المستخدم من Dashboard
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT UNIQUE NOT NULL,        -- e.g. 'target_channels', 'ai_model', 'video_resolution'
    value JSONB NOT NULL,            -- القيمة بأي تنسيق
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. CHANNELS: قنوات المنافسين المحللة
CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id TEXT UNIQUE NOT NULL,  -- YouTube channel ID
    channel_name TEXT NOT NULL,
    subscriber_count BIGINT DEFAULT 0,
    total_views BIGINT DEFAULT 0,
    niche TEXT,                       -- 'revenge', 'family_drama', etc.
    analysis_data JSONB,             -- تحليل كامل للقناة (top videos, hashtags, patterns)
    last_analyzed TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. VIDEOS: الفيديوهات المنتجة
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_video_id TEXT,             -- YouTube video ID المصدر (المنافس)
    source_channel_id TEXT,           -- القناة المصدر
    original_title TEXT,              -- عنوان الفيديو الأصلي
    rewritten_title TEXT,             -- العنوان المعاد صياغته
    hook TEXT,                        -- الجملة الأولى القوية
    story_json JSONB,                 -- القصة الكاملة (3 acts + scenes + cliffhangers)
    audio_path TEXT,                  -- مسار الصوت المنتج
    bg_paths JSONB,                   -- مسارات الخلفيات
    thumbnail_path TEXT,              -- مسار الصورة المصغرة
    video_path TEXT,                  -- مسار الفيديو النهائي
    youtube_video_id TEXT,            -- YouTube ID بعد الرفع
    duration_sec INT,
    resolution TEXT DEFAULT '3840x2160',
    hashtags JSONB,                   -- الهاشتاغات المستخدمة
    description TEXT,                 -- الوصف الكامل
    status TEXT DEFAULT 'queued',     -- queued → processing → rendered → uploaded → published
    publish_time TIMESTAMPTZ,
    views_estimate INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

-- 4. ANALYTICS: إحصائيات مبسطة
CREATE TABLE IF NOT EXISTS analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID REFERENCES videos(id),
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    views INT DEFAULT 0,
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    revenue_estimate DECIMAL(10,2) DEFAULT 0,
    UNIQUE(video_id, date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_created ON videos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date);