/* =============================================================
   YouTube Revenge Factory — Advanced Dashboard (app.js)
   Settings persistence via Supabase · GitHub API · AR/EN i18n
   ============================================================= */

const supabaseUrl = import.meta.env?.VITE_SUPABASE_URL || window?.CONFIG?.SUPABASE_URL || '';
const supabaseKey = import.meta.env?.VITE_SUPABASE_KEY || window?.CONFIG?.SUPABASE_KEY || '';

let currentLanguage = localStorage.getItem('language') || 'en';
let hasUnsavedChanges = false;
let settingsCache = {};

/* ---- Default Settings ---- */
const DEFAULTS = {
  // Video basic
  'video-resolution': '3840x2160',
  'video-width': 1920,
  'video-height': 1080,
  'video-fps': 30,
  'video-duration': 120,
  // Video advanced
  'video-crf': 18,
  'video-preset': 'slow',
  'video-pixfmt': 'yuv420p',
  'video-scene-duration': 5,
  // Backgrounds
  'source-priority': ['pexels', 'pixabay', 'unsplash', 'gradient'],
  'background-kenburns': 1.03,
  'background-cache-dir': 'data/backgrounds/cache',
  // Audio
  'audio-tts-engine': 'edge_tts',
  'audio-voice': 'random',
  'audio-speed': 0.95,
  // AI
  'ai-primary': 'nvidia_nim',
  'ai-primary-model': 'meta/llama-3.1-70b-instruct',
  'ai-backup': 'gemini',
  'ai-backup-model': '',
  'ai-temperature': 0.7,
  // Publishing
  'publishing-platform': 'youtube',
  'publishing-category': 'Entertainment',
  'publishing-privacy': 'unlisted',
  'publishing-language': 'en',
  'publishing-auto-upload': false,
  // Pipeline
  'pipeline-channel-analysis': true,
  'pipeline-content-finding': true,
  'pipeline-story-rewriting': true,
  'pipeline-tts': true,
  'pipeline-backgrounds': true,
  'pipeline-thumbnail': true,
  'pipeline-final-output': true,
  'pipeline-max-retries': 3,
  'pipeline-retry-delay': 5.0,
  'pipeline-stage-timeout': 300,
  // API keys
  'api-nvidia': '',
  'api-gemini': '',
  'api-pexels': '',
  'api-pixabay': '',
  'api-unsplash': '',
  // SEO
  'seo-title': '',
  'seo-description': '',
  'seo-tags': '',
};

/* =============================================================
   Translations (EN / AR)
   ============================================================= */
const translations = {
  en: {
    'app.title': 'YouTube Revenge Factory — Advanced Dashboard',
    'app.shortTitle': 'Revenge Factory',
    'nav.settings': 'Settings',
    'nav.pipeline': 'Pipeline',
    'nav.analytics': 'Analytics',
    'nav.logs': 'Logs',
    'settings.title': 'Advanced Settings',
    'settings.video': 'Video Settings',
    'settings.videoAdvanced': 'Video — Advanced',
    'settings.backgrounds': 'Backgrounds',
    'settings.audio': 'Audio',
    'settings.ai': 'AI Configuration',
    'settings.publishing': 'Publishing',
    'settings.pipeline': 'Pipeline Stages',
    'settings.apiKeys': 'API Keys',
    'settings.seo': 'SEO',
    'video.resolution': 'Resolution',
    'video.width': 'Width',
    'video.height': 'Height',
    'video.fps': 'FPS',
    'video.duration': 'Duration (seconds)',
    'video.crf': 'CRF (Quality)',
    'video.preset': 'Encoder Preset',
    'video.pixelFormat': 'Pixel Format',
    'video.sceneDuration': 'Scene Duration (seconds)',
    'backgrounds.sourcePriority': 'Source Priority',
    'backgrounds.kenburns': 'Ken Burns Zoom',
    'backgrounds.cacheDir': 'Cache Directory',
    'audio.ttsEngine': 'TTS Engine',
    'audio.voice': 'Voice',
    'audio.speed': 'Speed',
    'ai.primaryProvider': 'Primary Provider',
    'ai.primaryModel': 'Primary Model',
    'ai.backupProvider': 'Backup Provider',
    'ai.backupModel': 'Backup Model',
    'ai.temperature': 'Temperature',
    'publishing.platform': 'Platform',
    'publishing.category': 'Category',
    'publishing.privacy': 'Privacy',
    'publishing.language': 'Language',
    'publishing.autoUpload': 'Auto Upload',
    'pipeline.channelAnalysis': 'Channel Analysis',
    'pipeline.contentFinding': 'Content Finding',
    'pipeline.storyRewriting': 'Story Rewriting',
    'pipeline.tts': 'TTS Generation',
    'pipeline.backgrounds': 'Background Matching',
    'pipeline.thumbnail': 'Thumbnail Generation',
    'pipeline.finalOutput': 'Final Output',
    'pipeline.maxRetries': 'Max Retries',
    'pipeline.retryDelay': 'Retry Delay (s)',
    'pipeline.stageTimeout': 'Stage Timeout (s)',
    'api.nvidia': 'NVIDIA API Key',
    'api.gemini': 'Gemini API Key',
    'api.pexels': 'Pexels API Key',
    'api.pixabay': 'Pixabay API Key',
    'api.unsplash': 'Unsplash Access Key',
    'seo.title': 'Video Title Template',
    'seo.description': 'Description Template',
    'seo.tags': 'Tags (comma separated)',
    'save': 'Save Settings',
    'save.clean': 'All changes saved',
    'save.dirty': 'Unsaved changes',
    'save.success': 'Settings saved successfully',
    'save.error': 'Error saving settings',
    'reset': 'Reset to Defaults',
    'reset.confirm': 'Reset all settings to defaults?',
    'reset.done': 'Settings reset to defaults',
    'run.pipeline': 'Run Pipeline Now',
    'pipeline.status': 'Pipeline Status',
    'pipeline.date': 'Date',
    'pipeline.trigger': 'Trigger',
    'pipeline.duration': 'Duration',
    'pipeline.actions': 'Actions',
    'pipeline.noRuns': 'No pipeline runs yet',
    'pipeline.logs': 'Pipeline Logs',
    'pipeline.running': 'Running...',
    'pipeline.started': 'Pipeline started successfully',
    'pipeline.failed': 'Failed to run pipeline',
    'pipeline.norepo': 'Repository not configured in settings',
    'analytics.title': 'Analytics',
    'analytics.videos': 'Videos Published',
    'analytics.views': 'Total Views',
    'analytics.engagement': 'Engagement Rate',
    'status.idle': 'Idle',
    'status.running': 'Running',
    'status.completed': 'Completed',
    'status.error': 'Error',
    'status.pending': 'Pending',
    'connection.connected': 'Connected',
    'connection.disconnected': 'Disconnected',
    'theme.toggle': 'Toggle Theme',
    'language.toggle': 'العربية',
    'logs.empty': 'No logs available',
    'logs.view': 'View Logs',
  },
  ar: {
    'app.title': 'مصنع الانتقام على يوتيوب — لوحة التحكم المتقدمة',
    'app.shortTitle': 'مصنع الانتقام',
    'nav.settings': 'الإعدادات',
    'nav.pipeline': 'خط الإنتاج',
    'nav.analytics': 'التحليلات',
    'nav.logs': 'السجلات',
    'settings.title': 'الإعدادات المتقدمة',
    'settings.video': 'إعدادات الفيديو',
    'settings.videoAdvanced': 'الفيديو — متقدم',
    'settings.backgrounds': 'الخلفيات',
    'settings.audio': 'الصوت',
    'settings.ai': 'تكوين الذكاء الاصطناعي',
    'settings.publishing': 'النشر',
    'settings.pipeline': 'مراحل خط الإنتاج',
    'settings.apiKeys': 'مفاتيح API',
    'settings.seo': 'تحسين محركات البحث',
    'video.resolution': 'الدقة',
    'video.width': 'العرض',
    'video.height': 'الارتفاع',
    'video.fps': 'الإطارات في الثانية',
    'video.duration': 'المدة (بالثواني)',
    'video.crf': 'CRF (الجودة)',
    'video.preset': 'إعدادات الترميز',
    'video.pixelFormat': 'تنسيق البكسل',
    'video.sceneDuration': 'مدة المشهد (ثواني)',
    'backgrounds.sourcePriority': 'ترتيب المصادر',
    'backgrounds.kenburns': 'تكبير Ken Burns',
    'backgrounds.cacheDir': 'مجلد التخزين المؤقت',
    'audio.ttsEngine': 'محرك TTS',
    'audio.voice': 'الصوت',
    'audio.speed': 'السرعة',
    'ai.primaryProvider': 'المزود الأساسي',
    'ai.primaryModel': 'النموذج الأساسي',
    'ai.backupProvider': 'المزود الاحتياطي',
    'ai.backupModel': 'النموذج الاحتياطي',
    'ai.temperature': 'درجة الحرارة',
    'publishing.platform': 'المنصة',
    'publishing.category': 'التصنيف',
    'publishing.privacy': 'الخصوصية',
    'publishing.language': 'اللغة',
    'publishing.autoUpload': 'الرفع التلقائي',
    'pipeline.channelAnalysis': 'تحليل القناة',
    'pipeline.contentFinding': 'البحث عن المحتوى',
    'pipeline.storyRewriting': 'إعادة كتابة القصة',
    'pipeline.tts': 'توليد الصوت',
    'pipeline.backgrounds': 'مطابقة الخلفيات',
    'pipeline.thumbnail': 'توليد الصورة المصغرة',
    'pipeline.finalOutput': 'الإخراج النهائي',
    'pipeline.maxRetries': 'عدد المحاولات',
    'pipeline.retryDelay': 'تأخير إعادة المحاولة (ث)',
    'pipeline.stageTimeout': 'مهلة المرحلة (ث)',
    'api.nvidia': 'مفتاح NVIDIA API',
    'api.gemini': 'مفتاح Gemini API',
    'api.pexels': 'مفتاح Pexels API',
    'api.pixabay': 'مفتاح Pixabay API',
    'api.unsplash': 'مفتاح Unsplash',
    'seo.title': 'قالب عنوان الفيديو',
    'seo.description': 'قالب الوصف',
    'seo.tags': 'الوسوم (مفصولة بفواصل)',
    'save': 'حفظ الإعدادات',
    'save.clean': 'جميع التغييرات محفوظة',
    'save.dirty': 'هناك تغييرات غير محفوظة',
    'save.success': 'تم حفظ الإعدادات بنجاح',
    'save.error': 'خطأ في حفظ الإعدادات',
    'reset': 'إعادة ضبط الإعدادات',
    'reset.confirm': 'هل تريد إعادة ضبط جميع الإعدادات؟',
    'reset.done': 'تمت إعادة الضبط للإعدادات الافتراضية',
    'run.pipeline': 'تشغيل خط الإنتاج الآن',
    'pipeline.status': 'حالة خط الإنتاج',
    'pipeline.date': 'التاريخ',
    'pipeline.trigger': 'المشغل',
    'pipeline.duration': 'المدة',
    'pipeline.actions': 'الإجراءات',
    'pipeline.noRuns': 'لا توجد عمليات سابقة',
    'pipeline.logs': 'سجلات خط الإنتاج',
    'pipeline.running': 'جارٍ التشغيل...',
    'pipeline.started': 'تم تشغيل خط الإنتاج بنجاح',
    'pipeline.failed': 'فشل تشغيل خط الإنتاج',
    'pipeline.norepo': 'لم يتم تكوين المستودع في الإعدادات',
    'analytics.title': 'التحليلات',
    'analytics.videos': 'الفيديوهات المنشورة',
    'analytics.views': 'إجمالي المشاهدات',
    'analytics.engagement': 'معدل التفاعل',
    'status.idle': 'غير نشط',
    'status.running': 'يعمل',
    'status.completed': 'مكتمل',
    'status.error': 'خطأ',
    'status.pending': 'قيد الانتظار',
    'connection.connected': 'متصل',
    'connection.disconnected': 'غير متصل',
    'theme.toggle': 'تبديل المظهر',
    'language.toggle': 'English',
    'logs.empty': 'لا توجد سجلات',
    'logs.view': 'عرض السجلات',
  },
};

/* =============================================================
   i18n
   ============================================================= */
function setLanguage(lang) {
  currentLanguage = lang;
  localStorage.setItem('language', lang);
  const t = translations[lang];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) el.textContent = t[key];
  });
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  document.documentElement.lang = lang;
  document.getElementById('language-toggle').textContent = translations[lang === 'en' ? 'ar' : 'en']['language.toggle'];
}

function t(key) {
  return translations[currentLanguage]?.[key] || key;
}

/* =============================================================
   Supabase Client
   ============================================================= */
class SupabaseClient {
  constructor(url, key) {
    this.url = url;
    this.key = key;
    this.headers = {
      apikey: key,
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
      Prefer: 'return=representation',
    };
  }
  async get(table, query = '') {
    const r = await fetch(`${this.url}/rest/v1/${table}${query}`, { method: 'GET', headers: this.headers });
    if (!r.ok) throw new Error(`GET ${table} ${r.status}`);
    return r.json();
  }
  async post(table, data) {
    const r = await fetch(`${this.url}/rest/v1/${table}`, { method: 'POST', headers: this.headers, body: JSON.stringify(data) });
    if (!r.ok) throw new Error(`POST ${table} ${r.status}`);
    return r.json();
  }
  async patch(table, id, data) {
    const r = await fetch(`${this.url}/rest/v1/${table}?id=eq.${id}`, { method: 'PATCH', headers: this.headers, body: JSON.stringify(data) });
    if (!r.ok) throw new Error(`PATCH ${table} ${r.status}`);
    return r.json();
  }
}
const supabase = new SupabaseClient(supabaseUrl, supabaseKey);

/* =============================================================
   Settings: Populate Form from Data
   ============================================================= */
function $(id) { return document.getElementById(id); }

function populateSettingsForm(settings) {
  if (!settings || settings.length === 0) return;
  const s = settings[0];
  const map = {
    'video-resolution': s.video_resolution,
    'video-width': s.video_width,
    'video-height': s.video_height,
    'video-fps': s.video_fps,
    'video-duration': s.video_duration,
    'video-crf': s.video_crf,
    'video-preset': s.video_preset,
    'video-pixfmt': s.video_pixfmt,
    'video-scene-duration': s.video_scene_duration,
    'background-kenburns': s.background_kenburns,
    'background-cache-dir': s.background_cache_dir,
    'audio-tts-engine': s.audio_tts_engine,
    'audio-voice': s.audio_voice,
    'audio-speed': s.audio_speed,
    'ai-primary': s.ai_primary,
    'ai-primary-model': s.ai_primary_model,
    'ai-backup': s.ai_backup,
    'ai-backup-model': s.ai_backup_model,
    'ai-temperature': s.ai_temperature,
    'publishing-platform': s.publishing_platform,
    'publishing-category': s.publishing_category,
    'publishing-privacy': s.publishing_privacy,
    'publishing-language': s.publishing_language,
    'publishing-auto-upload': s.publishing_auto_upload,
    'pipeline-channel-analysis': s.pipeline_channel_analysis,
    'pipeline-content-finding': s.pipeline_content_finding,
    'pipeline-story-rewriting': s.pipeline_story_rewriting,
    'pipeline-tts': s.pipeline_tts,
    'pipeline-backgrounds': s.pipeline_backgrounds,
    'pipeline-thumbnail': s.pipeline_thumbnail,
    'pipeline-final-output': s.pipeline_final_output,
    'pipeline-max-retries': s.pipeline_max_retries,
    'pipeline-retry-delay': s.pipeline_retry_delay,
    'pipeline-stage-timeout': s.pipeline_stage_timeout,
    'api-nvidia': s.api_nvidia,
    'api-gemini': s.api_gemini,
    'api-pexels': s.api_pexels,
    'api-pixabay': s.api_pixabay,
    'api-unsplash': s.api_unsplash,
    'seo-title': s.seo_title,
    'seo-description': s.seo_description,
    'seo-tags': s.seo_tags,
  };

  for (const [id, val] of Object.entries(map)) {
    const el = $(id);
    if (!el) continue;
    if (el.type === 'checkbox') el.checked = !!val;
    else el.value = val ?? '';
  }

  // Range display values
  ['video-crf', 'background-kenburns', 'audio-speed', 'ai-temperature'].forEach(id => {
    const el = $(id);
    if (el) updateRangeDisplay(id);
  });

  // Conditional custom resolution
  toggleCustomResolution();

  // Source priority
  if (s.source_priority) {
    try {
      const order = typeof s.source_priority === 'string' ? JSON.parse(s.source_priority) : s.source_priority;
      const container = $('source-priority');
      if (container && Array.isArray(order)) {
        const items = container.querySelectorAll('.toggle-group');
        const lookup = {};
        items.forEach(item => {
          const cb = item.querySelector('input[type="checkbox"]');
          if (cb) lookup[cb.value] = item;
        });
        container.innerHTML = '';
        order.forEach(key => {
          if (lookup[key]) container.appendChild(lookup[key]);
        });
        // Append any remaining
        Object.values(lookup).forEach(item => {
          if (!item.parentNode) container.appendChild(item);
        });
      }
    } catch (e) { /* ignore parse errors */ }
  }
}

/* ---- Range Slider Display ---- */
function updateRangeDisplay(id) {
  const el = $(id);
  if (!el) return;
  const val = el.value;
  // Update inline label
  const labelSpan = document.getElementById(id + '-value');
  if (labelSpan) labelSpan.textContent = val;
  // Update range companion
  const container = el.closest('.range-container');
  if (container) {
    const display = container.querySelector('.range-value');
    if (display) display.textContent = val;
  }
}

/* ---- Custom Resolution Toggle ---- */
function toggleCustomResolution() {
  const sel = $('video-resolution');
  const group = $('custom-res-group');
  if (!sel || !group) return;
  group.classList.toggle('visible', sel.value === 'custom');
}

/* ---- Password Toggle (global) ---- */
function togglePassword(inputId, btn) {
  const input = $(inputId);
  if (!input) return;
  const isPassword = input.type === 'password';
  input.type = isPassword ? 'text' : 'password';
  btn.textContent = isPassword ? '\u{1F441}' : '\u{1F441}';
}

window.togglePassword = togglePassword;

/* =============================================================
   Settings: Save
   ============================================================= */
function gatherSettings() {
  function v(id) { const el = $(id); return el ? el.value : ''; }
  function c(id) { const el = $(id); return el ? el.checked : false; }

  // Source priority as JSON array
  const priority = [];
  const container = $('source-priority');
  if (container) {
    container.querySelectorAll('.toggle-group').forEach(item => {
      const cb = item.querySelector('input[type="checkbox"]');
      if (cb && cb.checked) priority.push(cb.value);
    });
  }

  return {
    video_resolution: v('video-resolution'),
    video_width: parseInt(v('video-width')) || 1920,
    video_height: parseInt(v('video-height')) || 1080,
    video_fps: parseInt(v('video-fps')) || 30,
    video_duration: parseInt(v('video-duration')) || 120,
    video_crf: parseInt(v('video-crf')) ?? 18,
    video_preset: v('video-preset'),
    video_pixfmt: v('video-pixfmt'),
    video_scene_duration: parseInt(v('video-scene-duration')) || 5,
    source_priority: JSON.stringify(priority),
    background_kenburns: parseFloat(v('background-kenburns')) || 1.03,
    background_cache_dir: v('background-cache-dir'),
    audio_tts_engine: v('audio-tts-engine'),
    audio_voice: v('audio-voice'),
    audio_speed: parseFloat(v('audio-speed')) || 0.95,
    ai_primary: v('ai-primary'),
    ai_primary_model: v('ai-primary-model'),
    ai_backup: v('ai-backup'),
    ai_backup_model: v('ai-backup-model'),
    ai_temperature: parseFloat(v('ai-temperature')) || 0.7,
    publishing_platform: v('publishing-platform'),
    publishing_category: v('publishing-category'),
    publishing_privacy: v('publishing-privacy'),
    publishing_language: v('publishing-language'),
    publishing_auto_upload: c('publishing-auto-upload'),
    pipeline_channel_analysis: c('pipeline-channel-analysis'),
    pipeline_content_finding: c('pipeline-content-finding'),
    pipeline_story_rewriting: c('pipeline-story-rewriting'),
    pipeline_tts: c('pipeline-tts'),
    pipeline_backgrounds: c('pipeline-backgrounds'),
    pipeline_thumbnail: c('pipeline-thumbnail'),
    pipeline_final_output: c('pipeline-final-output'),
    pipeline_max_retries: parseInt(v('pipeline-max-retries')) || 3,
    pipeline_retry_delay: parseFloat(v('pipeline-retry-delay')) || 5.0,
    pipeline_stage_timeout: parseInt(v('pipeline-stage-timeout')) || 300,
    api_nvidia: v('api-nvidia'),
    api_gemini: v('api-gemini'),
    api_pexels: v('api-pexels'),
    api_pixabay: v('api-pixabay'),
    api_unsplash: v('api-unsplash'),
    seo_title: v('seo-title'),
    seo_description: v('seo-description'),
    seo_tags: v('seo-tags'),
    updated_at: new Date().toISOString(),
  };
}

async function saveSettings() {
  const data = gatherSettings();
  try {
    const existing = await supabase.get('settings', '?select=id');
    if (existing.length > 0) {
      await supabase.patch('settings', existing[0].id, data);
    } else {
      await supabase.post('settings', data);
    }
    settingsCache = data;
    hasUnsavedChanges = false;
    updateSaveStatus();
    showNotification(t('save.success'), 'success');
  } catch (err) {
    console.error('Save error:', err);
    showNotification(t('save.error'), 'error');
  }
}

/* =============================================================
   Reset to Defaults
   ============================================================= */
function resetToDefaults() {
  if (!confirm(t('reset.confirm'))) return;
  for (const [id, val] of Object.entries(DEFAULTS)) {
    const el = $(id);
    if (!el) continue;
    if (el.type === 'checkbox') el.checked = !!val;
    else el.value = val;
  }
  // Reset source priority checkboxes
  const container = $('source-priority');
  if (container) {
    const order = ['pexels', 'pixabay', 'unsplash', 'gradient'];
    const items = container.querySelectorAll('.toggle-group');
    const lookup = {};
    items.forEach(item => {
      const cb = item.querySelector('input[type="checkbox"]');
      if (cb) lookup[cb.value] = item;
    });
    container.innerHTML = '';
    order.forEach(key => {
      if (lookup[key]) {
        const cb = lookup[key].querySelector('input[type="checkbox"]');
        if (cb) cb.checked = true;
        container.appendChild(lookup[key]);
      }
    });
  }
  // Range displays
  ['video-crf', 'background-kenburns', 'audio-speed', 'ai-temperature'].forEach(updateRangeDisplay);
  toggleCustomResolution();
  hasUnsavedChanges = true;
  updateSaveStatus();
  showNotification(t('reset.done'), 'info');
}

/* =============================================================
   Load Settings from Supabase
   ============================================================= */
async function loadSettings() {
  try {
    const result = await supabase.get('settings');
    settingsCache = result;
    populateSettingsForm(result);
    updateConnectionStatus(true);
  } catch (err) {
    console.error('Load error:', err);
    updateConnectionStatus(false);
  }
}

/* =============================================================
   Save Status
   ============================================================= */
function updateSaveStatus() {
  const el = $('save-status');
  if (!el) return;
  if (hasUnsavedChanges) {
    el.textContent = t('save.dirty');
    el.className = 'save-status dirty';
  } else {
    el.textContent = t('save.clean');
    el.className = 'save-status clean';
  }
}

/* =============================================================
   Connection Status
   ============================================================= */
function updateConnectionStatus(connected) {
  const indicator = $('connection-status');
  const text = $('connection-text');
  if (!indicator || !text) return;
  if (connected) {
    indicator.className = 'status-indicator connected';
    text.textContent = t('connection.connected');
  } else {
    indicator.className = 'status-indicator disconnected';
    text.textContent = t('connection.disconnected');
  }
}

/* =============================================================
   Run Pipeline
   ============================================================= */
async function runPipeline() {
  const btn = $('run-pipeline');
  const orig = btn.textContent;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + t('pipeline.running');
  const owner = window?.CONFIG?.GITHUB_OWNER || '';
  const repo = window?.CONFIG?.GITHUB_REPO || '';
  const token = window?.CONFIG?.GITHUB_TOKEN || '';
  if (!owner || !repo) {
    showNotification(t('pipeline.norepo'), 'error');
    btn.disabled = false;
    btn.textContent = orig;
    return;
  }
  try {
    const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/dispatches`, {
      method: 'POST',
      headers: {
        Authorization: `token ${token}`,
        Accept: 'application/vnd.github.v3+json',
      },
      body: JSON.stringify({ event_type: 'workflow_dispatch', client_payload: { trigger: 'manual', timestamp: new Date().toISOString() } }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    showNotification(t('pipeline.started'), 'success');
    updatePipelineStatus();
  } catch (err) {
    console.error('Pipeline trigger error:', err);
    showNotification(t('pipeline.failed'), 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

/* =============================================================
   Pipeline Status
   ============================================================= */
async function updatePipelineStatus() {
  try {
    const runs = await supabase.get('pipeline_runs', '?select=*&order=created_at.desc&limit=10');
    populatePipelineTable(runs);
  } catch (err) {
    console.error('Pipeline status error:', err);
  }
}

function populatePipelineTable(runs) {
  const tbody = document.querySelector('#pipeline-table tbody');
  if (!tbody) return;
  if (!runs || runs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">${t('pipeline.noRuns')}</td></tr>`;
    return;
  }
  tbody.innerHTML = '';
  runs.forEach(run => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${new Date(run.created_at).toLocaleString()}</td>
      <td><span class="status-badge ${run.status || 'idle'}">${t('status.' + (run.status || 'idle'))}</span></td>
      <td>${run.trigger || 'manual'}</td>
      <td>${run.duration ? run.duration + 's' : '—'}</td>
      <td><button class="btn-small" onclick="viewPipelineLogs('${run.id}')">${t('logs.view')}</button></td>
    `;
    tbody.appendChild(tr);
  });
}

/* =============================================================
   Pipeline Logs
   ============================================================= */
async function viewPipelineLogs(runId) {
  try {
    const logs = await supabase.get('pipeline_logs', `?pipeline_run_id=eq.${runId}&order=created_at.asc`);
    const container = $('modal-logs-container');
    if (!container) return;
    if (!logs || logs.length === 0) {
      container.innerHTML = `<p class="text-muted text-center">${t('logs.empty')}</p>`;
    } else {
      container.innerHTML = '';
      logs.forEach(log => {
        const div = document.createElement('div');
        div.className = 'log-entry';
        div.innerHTML = `
          <span class="log-timestamp">${new Date(log.created_at).toLocaleString()}</span>
          <span class="log-level ${log.level || 'INFO'}">${(log.level || 'INFO').toUpperCase()}</span>
          <span class="log-message">${log.message}</span>
        `;
        container.appendChild(div);
      });
    }
    $('logs-modal').classList.add('show');
  } catch (err) {
    console.error('Logs error:', err);
  }
}
window.viewPipelineLogs = viewPipelineLogs;

/* =============================================================
   Analytics
   ============================================================= */
async function updateAnalytics() {
  try {
    const data = await supabase.get('analytics', '?select=*&order=created_at.desc&limit=1');
    if (data.length > 0) {
      const d = data[0];
      if ($('analytics-videos')) $('analytics-videos').textContent = d.videos_published ?? 0;
      if ($('analytics-views')) $('analytics-views').textContent = d.total_views ?? 0;
      if ($('analytics-engagement')) $('analytics-engagement').textContent = (d.engagement_rate ?? 0) + '%';
    }
  } catch (err) {
    console.error('Analytics error:', err);
  }
}

/* =============================================================
   Notifications
   ============================================================= */
function showNotification(message, type = 'info') {
  const container = $('notifications');
  if (!container) return;
  const n = document.createElement('div');
  n.className = 'notification ' + type;
  n.textContent = message;
  container.appendChild(n);
  requestAnimationFrame(() => n.classList.add('show'));
  setTimeout(() => {
    n.classList.remove('show');
    setTimeout(() => { if (n.parentNode) n.parentNode.removeChild(n); }, 300);
  }, 3500);
}

/* =============================================================
   Navigation
   ============================================================= */
function setupNavigation() {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      const target = link.getAttribute('href').substring(1);
      document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
      const section = $(target);
      if (section) section.classList.add('active');
      // Close mobile sidebar
      $('sidebar').classList.remove('open');
      $('sidebar-overlay').classList.remove('open');
      if (target === 'analytics') updateAnalytics();
    });
  });
}

/* =============================================================
   Mobile Sidebar
   ============================================================= */
function setupMobileNav() {
  const hamburger = $('hamburger-btn');
  const sidebar = $('sidebar');
  const overlay = $('sidebar-overlay');
  if (!hamburger || !sidebar || !overlay) return;
  hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('open');
  });
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
  });
}

/* =============================================================
   Event Listeners
   ============================================================= */
function setupEventListeners() {
  // Save
  $('save-button').addEventListener('click', saveSettings);
  // Reset
  $('reset-button').addEventListener('click', resetToDefaults);
  // Run pipeline
  $('run-pipeline').addEventListener('click', runPipeline);
  // Language
  $('language-toggle').addEventListener('click', () => {
    setLanguage(currentLanguage === 'en' ? 'ar' : 'en');
    updateSaveStatus();
  });
  // Theme
  $('theme-toggle').addEventListener('click', () => {
    const html = document.documentElement;
    const theme = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  });
  // Modal close
  $('modal-close').addEventListener('click', () => {
    $('logs-modal').classList.remove('show');
  });
  $('logs-modal').addEventListener('click', e => {
    if (e.target === e.currentTarget) $('logs-modal').classList.remove('show');
  });

  // Range slider live updates
  document.querySelectorAll('input[type="range"]').forEach(el => {
    el.addEventListener('input', () => updateRangeDisplay(el.id));
    el.addEventListener('change', markDirty);
  });

  // Custom resolution toggle
  const resSel = $('video-resolution');
  if (resSel) {
    resSel.addEventListener('change', () => { toggleCustomResolution(); markDirty(); });
  }

  // Track unsaved changes on all inputs
  document.querySelectorAll('#settings-form input, #settings-form select, #settings-form textarea').forEach(el => {
    el.addEventListener('change', markDirty);
    el.addEventListener('input', markDirty);
  });
}

function markDirty() {
  hasUnsavedChanges = true;
  updateSaveStatus();
}

/* =============================================================
   Auto-save
   ============================================================= */
function setupAutoSave() {
  let timeout;
  document.querySelectorAll('#settings-form input, #settings-form select, #settings-form textarea').forEach(el => {
    el.addEventListener('change', () => {
      clearTimeout(timeout);
      timeout = setTimeout(saveSettings, 5000);
    });
  });
}

/* =============================================================
   Init
   ============================================================= */
async function initDashboard() {
  setLanguage(currentLanguage);
  await loadSettings();
  setupEventListeners();
  setupAutoSave();
  updateConnectionStatus(false);
}

document.addEventListener('DOMContentLoaded', () => {
  // Theme
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  initDashboard();
  setupNavigation();
  setupMobileNav();
  // Periodic updates
  setInterval(updatePipelineStatus, 30000);
  setInterval(updateAnalytics, 60000);
});
