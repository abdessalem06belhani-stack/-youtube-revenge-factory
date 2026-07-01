# YouTube Revenge Story Factory

![YouTube Revenge Factory](https://img.shields.io/badge/YouTube%20Revenge%20Factory-FFA500?style=flat-square&logo=youtube)

## نظرة عامة / Overview

**YouTube Revenge Story Factory** هو نظام متكامل لتحويل مقاطع الفيديو إلى قصص انتقامية باستخدام الذكاء الاصطناعي، حيث يقوم بإنشاء مقاطع فيديو احترافية باستخدام تقنية التوليد النصي إلى الفيديو (text-to-video) من NVIDIA NIM وGemini وPexels وPixabay وUnsplash. يقوم النظام بتحليل محتوى الفيديو الأصلي، وإنشاء سيناريوهات قصص انتقامية، وتوليد مقاطع فيديو عالية الجودة باستخدام أحدث تقنيات الذكاء الاصطناعي.

**YouTube Revenge Story Factory** is an integrated system for transforming videos into revenge stories using AI, where it creates professional videos using text-to-video generation technology from NVIDIA NIM, Gemini, Pexels, Pixabay, and Unsplash. The system analyzes the original video content, generates revenge story scenarios, and produces high-quality videos using the latest AI technologies.

## العرض التوضيحي / Demo

[![عرض توضيحي للفيديو](https://img.youtube.com/vi/sample/maxresdefault.jpg)](https://www.youtube.com/watch?v=sample)

- **عرض توضيحي مباشر**: [مشاهدة على يوتيوب](https://www.youtube.com/watch?v=sample)
- **لقطة الشاشة**: ![لقطة الشاشة](screenshots/demo.png)

## الميزات / Features

- **تحليل المحتوى**: تحليل تلقائي لمحتوى الفيديو الأصلي باستخدام الذكاء الاصطناعي
- **توليد السيناريو**: إنشاء سيناريوهات قصص انتقامية جذابة
- **توليد الفيديو**: إنتاج مقاطع فيديو عالية الجودة باستخدام تقنيات text-to-video
- **التكامل مع المنصات**: النشر التلقائي على يوتيوب ووسائل التواصل الاجتماعي
- **التحكم عبر لوحة التحكم**: واجهة مستخدم سهلة الاستخدام لإدارة العمليات
- **التشغيل الآلي**: التشغيل عبر GitHub Actions والـ Colab
- **جودة 4K**: دعم إنتاج الفيديو بدقة 4K
- **مصادر متعددة**: التكامل مع NVIDIA NIM وGemini وPexels وPixabay وUnsplash

## مخطط البنية / Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   لوحة التحكم  │    │   GitHub Actions│    │     Colab       │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   API       │ │    │ │   Workflow  │ │    │ │   Jupyter   │ │
│ │   Server    │ │    │ │   Trigger   │ │    │ │   Notebook  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │   Supabase  │    │   YouTube   │    │   NVIDIA    │
    │   Database  │    │   API       │    │   NIM       │
    │             │    │   OAuth2    │    │   (T2V)     │
    └─────────────┘    └─────────────┘    └─────────────┘
          │                      │                      │
          │                      │                      │
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │   Gemini    │    │   Pexels    │    │   Pixabay   │
    │   (Analysis)│    │   (Media)   │    │   (Media)   │
    └─────────────┘    └─────────────┘    └─────────────┘
          │                      │                      │
          │                      │                      │
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │   Unsplash   │    │   Storage   │    │   CDN       │
    │   (Media)   │    │   (S3)      │    │   (Cloud)   │
    └─────────────┘    └─────────────┘    └─────────────┘
```

## المتطلبات الأساسية / Prerequisites

### الحسابات المطلوبة / Accounts Needed

1. **يوتيوب API**: حساب مطور يوتيوب مع تفعيل واجهة برمجة التطبيقات
2. **Supabase**: مشروع Supabase مع قاعدة البيانات
3. **NVIDIA NIM**: حساب NVIDIA مع الوصول إلى خدمة text-to-video
4. **Gemini**: حساب Google AI مع مفتاح API
5. **Pexels**: حساب Pexels مع مفتاح API
6. **Pixabay**: حساب Pixabay مع مفتاح API
7. **Unsplash**: حساب Unsplash مع مفتاح API

## الإعداد لمرة واحدة / One-Time Setup

### 1. إعداد مشروع Supabase

```bash
# استيراد مخطط قاعدة البيانات
sqlite3 supabase.db < schema.sql

# أو عبر واجهة مستخدم Supabase
# الانتقال إلى Project → SQL Editor
# استيراد ملف schema.sql
```

### 2. إعداد OAuth2 ليوتيوب API

```bash
# إنشاء ملف client_secrets.json
gcloud auth login
# ثم:
# الانتقال إلى Google Cloud Console → APIs & Services → Credentials
# إنشاء بيانات اعتماد OAuth 2.0 عميل ويب
# تنزيل JSON وتسميته client_secrets.json
```

### 3. مفاتيح API في GitHub Secrets

```bash
# إضافة المتغيرات السرية عبر واجهة مستخدم GitHub
GH_SECRET_YOUTUBE_CLIENT_ID=your_youtube_client_id
GH_SECRET_YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
GH_SECRET_SUPABASE_URL=your_supabase_url
GH_SECRET_SUPABASE_ANON_KEY=your_supabase_anon_key
GH_SECRET_NVIDIA_API_KEY=your_nvidia_api_key
GH_SECRET_GEMINI_API_KEY=your_gemini_api_key
GH_SECRET_PEXELS_API_KEY=your_pexels_api_key
GH_SECRET_PIXABAY_API_KEY=your_pixabay_api_key
GH_SECRET_UNSPLASH_ACCESS_KEY=your_unsplash_access_key
```

### 4. نشر لوحة التحكم (GitHub Pages)

```bash
# عبر واجهة مستخدم GitHub Actions
# الانتقال إلى Actions → youtube-revenge-factory → workflows
# تشغيل workflow "Deploy to GitHub Pages"
```

## دليل التكوين / Configuration Guide

### إعدادات لوحة التحكم / Dashboard Settings

- **عنوان القناة**: عنوان القناة على يوتيوب
- **وصف القناة**: وصف القناة
- **الفئة**: فئة الفيديو
- **العلامات**: علامات الفيديو مفصولة بفواصل
- **اللغة**: لغة الفيديو (العربية/الإنجليزية)

### خيارات config.yaml

```yaml
# config.yaml
youtube:
  channel_id: UC_your_channel_id
  client_id: ${GH_SECRET_YOUTUBE_CLIENT_ID}
  client_secret: ${GH_SECRET_YOUTUBE_CLIENT_SECRET}

supabase:
  url: ${GH_SECRET_SUPABASE_URL}
  anon_key: ${GH_SECRET_SUPABASE_ANON_KEY}

ai_services:
  nvidia:
    api_key: ${GH_SECRET_NVIDIA_API_KEY}
    model: "nvidia/llama-3.1-nemotron-70b-instruct"
  gemini:
    api_key: ${GH_SECRET_GEMINI_API_KEY}
    model: "gemini-1.5-pro"

media_sources:
  pexels:
    api_key: ${GH_SECRET_PEXELS_API_KEY}
  pixabay:
    api_key: ${GH_SECRET_PIXABAY_API_KEY}
  unsplash:
    access_key: ${GH_SECRET_UNSPLASH_ACCESS_KEY}
```

## الاستخدام / Usage

### عبر لوحة التحكم (موصى به) / Via Dashboard (Recommended)

1. الانتقال إلى لوحة التحكم: [اضغط هنا](https://yourusername.github.io/youtube-revenge-factory)
2. تسجيل الدخول باستخدام حساب GitHub
3. اختيار الفيديو المصدر من مكتبة Supabase
4. تكوين إعدادات الفيديو
5. النقر على "إنشاء القصة"
6. تتبع التقدم في لوحة النشاط

### عبر GitHub Actions (تشغيل يدوي) / Via GitHub Actions (Manual Trigger)

```bash
# تشغيل workflow عبر واجهة مستخدم GitHub Actions
# الانتقال إلى Actions → youtube-revenge-factory
# النقر على "Run workflow" واختيار الفيديو المصدر
```

### عبر Colab (عرض 4K) / Via Colab (4K Rendering)

```python
# تشغيل ملف Colab: colab_4k_rendering.ipynb
# يتطلب GPU runtime مع ذاكرة >= 24GB
# قم بتعيين GPU:
from google.colab import drive
drive.mount('/content/drive')
!pip install -r requirements.txt
```

## تدفق الأنابيب (خطوة بخطوة) / Pipeline Flow (Step by Step)

1. **التحميل**: تحميل الفيديو المصدر إلى Supabase Storage
2. **التحليل**: تحليل محتوى الفيديو باستخدام Gemini AI
3. **توليد السيناريو**: إنشاء سيناريو القصة الانتقامية
4. **جمع الوسائط**: البحث عن الصور ومقاطع الفيديو المناسبة من Pexels/Pixabay/Unsplash
5. **توليد الفيديو**: إنتاج الفيديو النهائي باستخدام NVIDIA NIM T2V
6. **المعالجة**: إضافة التأثيرات والانتقالات والطبقة الصوتية
7. **التحسين**: تحسين الفيديو للجودة والدقة
8. **الرفع**: نشر الفيديو النهائي على يوتيوب ووسائل التواصل الاجتماعي
9. **التوثيق**: حفظ السجل في قاعدة بيانات Supabase

## هيكل الملفات / File Structure

```
/youtube-revenge-factory/
├── .github/
│   ├── workflows/
│   │   ├── deploy.yml          # نشر GitHub Pages
│   │   ├── pipeline.yml        # pipeline التشغيل الآلي
│   │   └── colab.yml           # تشغيل Colab
├── src/
│   ├── api/                    # كود الخادم
│   │   ├── auth.py              # مصادقة يوتيوب
│   │   ├── pipeline.py          # منطق الأنابيب
│   │   └── services/            # خدمات الذكاء الاصطناعي
│   ├── utils/                  # الأدوات المساعدة
│   │   ├── media_downloader.py   # تنزيل الوسائط
│   │   ├── video_generator.py   # مولد الفيديو
│   │   └── content_analyzer.py # محلل المحتوى
│   └── models/                 # نماذج البيانات
│       ├── video.py             # نموذج الفيديو
│       ├── story.py             # نموذج القصة
│       └── user.py              # نموذج المستخدم
├── dashboard/                  # كود لوحة التحكم
│   ├── index.html              # الصفحة الرئيسية
│   ├── styles.css              # التنسيقات
│   ├── app.js                  # منطق العميل
│   └── assets/                 # الأصول
├── docs/                       # الوثائق
│   ├── api.md                  # مرجع API
│   ├── setup.md                # دليل الإعداد
│   └── architecture.md         # مخطط البنية
├── config.yaml                  # ملف التكوين
├── requirements.txt             # اعتمادات Python
├── schema.sql                  # مخطط قاعدة البيانات Supabase
├── README.md                   # هذه الوثيقة
└── screenshots/                 # لقطات الشاشة
    └── demo.png
```

## متغيرات البيئة / Environment Variables

### .env.example

```bash
# YouTube API
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_API_KEY=your_api_key

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# AI Services
NVIDIA_API_KEY=your_nvidia_api_key
GEMINI_API_KEY=your_gemini_api_key

# Media Sources
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
UNSPLASH_SECRET_KEY=your_unsplash_secret_key

# Storage
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_BUCKET_NAME=your_bucket_name

# Application
APP_ENV=development
LOG_LEVEL=info
MAX_VIDEO_DURATION=300
```

## الأسئلة الشائعة / FAQ

### س: ما هي متطلبات الأجهزة؟ / Q: What are the hardware requirements?

**ج**: وحدة معالجة رسومات واحدة من نوع NVIDIA RTX 4090 أو ما يعادلها مع ذاكرة لا تقل عن 24 جيجابايت. يُنصح باستخدام 32 جيجابايت أو أكثر لمعالجة الفيديو بدقة 4K.

**A**: One NVIDIA RTX 4090 or equivalent GPU with minimum 24GB VRAM. 32GB or more is recommended for 4K video processing.

### س: هل يمكنني استخدام هذا للمحتوى التجاري؟ / Q: Can I use this for commercial content?

**ج**: نعم، ولكنك تحتاج إلى الحصول على جميع التراخيص اللازمة لمصادر الوسائط وتأكيد حقوق استخدام الذكاء الاصطناعي للمحتوى الذي تنشئه.

**A**: Yes, but you need to obtain all necessary licenses for media sources and confirm AI usage rights for content you create.

### س: كيف يمكنني زيادة معدل المعالجة؟ / Q: How can I increase processing speed?

**ج**: استخدم GPU instances، وقم بتحسين حجم النماذج، وفكر في معالجة الدفعات، وقم بتخزين الوسائط مؤقتًا.

**A**: Use GPU instances, optimize model sizes, consider batch processing, and cache media assets.

### س: ماذا يحدث إذا فشل الذكاء الاصطناعي في توليد الفيديو؟ / Q: What happens if AI video generation fails?

**ج**: يقوم النظام بإعادة المحاولة تلقائيًا (بحد أقصى 3 محاولات)، ثم يسجل الخطأ، ويقترح بدائل من مصادر الوسائط الأخرى.

**A**: The system automatically retries (max 3 attempts), logs the error, and suggests alternatives from other media sources.

## الترخيص / License

هذا المشروع مفتوح المصدر تحت ترخيص MIT. انظر ملف LICENSE للتفاصيل.

This project is open source under the MIT License. See the LICENSE file for details.

---

*آخر تحديث: 1 يوليو 2026 / Last Updated: July 1, 2026*
*الإصدار: 1.0.0*

© 2026 YouTube Revenge Story Factory. جميع الحقوق محفوظة.