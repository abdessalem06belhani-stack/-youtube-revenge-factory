const supabaseUrl = import.meta.env?.VITE_SUPABASE_URL || window?.CONFIG?.SUPABASE_URL || '';
const supabaseKey = import.meta.env?.VITE_SUPABASE_KEY || window?.CONFIG?.SUPABASE_KEY || '';

let currentLanguage = localStorage.getItem('language') || 'en';
let hasUnsavedChanges = false;
let settingsCache = {};

// Initialize the dashboard
async function initDashboard() {
    setLanguage(currentLanguage);
    await loadSettings();
    setupEventListeners();
    setupAutoSave();
    updateConnectionStatus();
}

// Set language (Arabic/English)
function setLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem('language', lang);
    
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = translations[lang][key] || el.textContent;
    });
    
    // Update direction
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
}

// Translations
const translations = {
    'en': {
        'app.title': 'YouTube Revenge Factory Dashboard',
        'nav.settings': 'Settings',
        'nav.pipeline': 'Pipeline',
        'nav.analytics': 'Analytics',
        'nav.logs': 'Logs',
        'settings.title': 'Settings',
        'settings.content': 'Content Source',
        'settings.ai': 'AI Configuration',
        'settings.video': 'Video Settings',
        'settings.backgrounds': 'Backgrounds',
        'settings.thumbnail': 'Thumbnail',
        'settings.seo': 'SEO',
        'settings.publishing': 'Publishing',
        'content.source': 'Content Source',
        'content.apiKey': 'API Key',
        'content.endpoint': 'Endpoint',
        'content.model': 'Model',
        'ai.provider': 'AI Provider',
        'ai.apiKey': 'API Key',
        'ai.model': 'Model',
        'ai.temperature': 'Temperature',
        'video.resolution': 'Resolution',
        'video.fps': 'FPS',
        'video.duration': 'Duration (seconds)',
        'backgrounds.provider': 'Background Provider',
        'backgrounds.apiKey': 'API Key',
        'thumbnail.style': 'Thumbnail Style',
        'thumbnail.template': 'Template',
        'thumbnail.overlay': 'Overlay Text',
        'seo.title': 'Video Title Template',
        'seo.description': 'Description Template',
        'seo.tags': 'Tags',
        'publishing.platform': 'Publishing Platform',
        'publishing.schedule': 'Schedule',
        'publishing.autoUpload': 'Auto Upload',
        'save': 'Save',
        'save.success': 'Settings saved successfully',
        'save.error': 'Error saving settings',
        'run.pipeline': 'Run Pipeline Now',
        'pipeline.status': 'Pipeline Status',
        'pipeline.logs': 'Pipeline Logs',
        'analytics.videos': 'Videos Published',
        'analytics.views': 'Total Views',
        'analytics.engagement': 'Engagement Rate',
        'status.idle': 'Idle',
        'status.running': 'Running',
        'status.completed': 'Completed',
        'status.error': 'Error',
        'connection.status': 'Connection Status',
        'connection.connected': 'Connected',
        'connection.disconnected': 'Disconnected',
        'theme.toggle': 'Toggle Theme',
        'language.toggle': 'العربية'
    },
    'ar': {
        'app.title': 'مصنع الانتقام على يوتيوب - لوحة التحكم',
        'nav.settings': 'الإعدادات',
        'nav.pipeline': 'خط الأنابيب',
        'nav.analytics': 'التحليلات',
        'nav.logs': 'السجلات',
        'settings.title': 'الإعدادات',
        'settings.content': 'مصدر المحتوى',
        'settings.ai': 'تكوين الذكاء الاصطناعي',
        'settings.video': 'إعدادات الفيديو',
        'settings.backgrounds': 'الخلفيات',
        'settings.thumbnail': 'الصور المصغرة',
        'settings.seo': 'تحسين محركات البحث',
        'settings.publishing': 'النشر',
        'content.source': 'مصدر المحتوى',
        'content.apiKey': 'مفتاح API',
        'content.endpoint': 'نقطة النهاية',
        'content.model': 'النموذج',
        'ai.provider': 'مزود الذكاء الاصطناعي',
        'ai.apiKey': 'مفتاح API',
        'ai.model': 'النموذج',
        'ai.temperature': 'درجة الحرارة',
        'video.resolution': 'الدقة',
        'video.fps': 'الإطارات في الثانية',
        'video.duration': 'المدة (بالثواني)',
        'backgrounds.provider': 'مزود الخلفيات',
        'backgrounds.apiKey': 'مفتاح API',
        'thumbnail.style': 'نمط الصورة المصغرة',
        'thumbnail.template': 'القالب',
        'thumbnail.overlay': 'نص التغطية',
        'seo.title': 'قالب عنوان الفيديو',
        'seo.description': 'قالب الوصف',
        'seo.tags': 'الوسوم',
        'publishing.platform': 'منصة النشر',
        'publishing.schedule': 'الجدول الزمني',
        'publishing.autoUpload': 'الرفع التلقائي',
        'save': 'حفظ',
        'save.success': 'تم حفظ الإعدادات بنجاح',
        'save.error': 'خطأ في حفظ الإعدادات',
        'run.pipeline': 'تشغيل خط الأنابيب الآن',
        'pipeline.status': 'حالة خط الأنابيب',
        'pipeline.logs': 'سجلات خط الأنابيب',
        'analytics.videos': 'عدد الفيديوهات المنشورة',
        'analytics.views': 'إجمالي المشاهدات',
        'analytics.engagement': 'معدل التفاعل',
        'status.idle': 'غير نشط',
        'status.running': 'يعمل',
        'status.completed': 'مكتمل',
        'status.error': 'خطأ',
        'connection.status': 'حالة الاتصال',
        'connection.connected': 'متصل',
        'connection.disconnected': 'غير متصل',
        'theme.toggle': 'تبديل المظهر',
        'language.toggle': 'English'
    }
};

// Supabase API client
class SupabaseClient {
    constructor(url, key) {
        this.url = url;
        this.key = key;
        this.headers = {
            'apikey': key,
            'Authorization': `Bearer ${key}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        };
    }

    async get(table, query = '') {
        const url = `${this.url}/rest/v1/${table}${query}`;
        const response = await fetch(url, {
            method: 'GET',
            headers: this.headers
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    }

    async post(table, data) {
        const url = `${this.url}/rest/v1/${table}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to save: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    }

    async patch(table, id, data) {
        const url = `${this.url}/rest/v1/${table}?id=eq.${id}`;
        const response = await fetch(url, {
            method: 'PATCH',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to update: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    }
}

// Initialize Supabase client
const supabase = new SupabaseClient(supabaseUrl, supabaseKey);

// Load settings from Supabase
async function loadSettings() {
    try {
        const settings = await supabase.get('settings');
        settingsCache = settings;
        populateSettingsForm(settings);
        updateConnectionStatus(true);
    } catch (error) {
        console.error('Failed to load settings:', error);
        updateConnectionStatus(false);
        showNotification(translations[currentLanguage]['save.error'], 'error');
    }
}

// Populate settings form with data
function populateSettingsForm(settings) {
    if (!settings || settings.length === 0) return;
    
    const setting = settings[0];
    
    // Populate each section
    document.getElementById('content-source').value = setting.content_source || '';
    document.getElementById('content-api-key').value = setting.content_api_key || '';
    document.getElementById('content-endpoint').value = setting.content_endpoint || '';
    document.getElementById('content-model').value = setting.content_model || '';
    
    document.getElementById('ai-provider').value = setting.ai_provider || '';
    document.getElementById('ai-api-key').value = setting.ai_api_key || '';
    document.getElementById('ai-model').value = setting.ai_model || '';
    document.getElementById('ai-temperature').value = setting.ai_temperature || '0.7';
    
    document.getElementById('video-resolution').value = setting.video_resolution || '1080x1920';
    document.getElementById('video-fps').value = setting.video_fps || '30';
    document.getElementById('video-duration').value = setting.video_duration || '120';
    
    document.getElementById('backgrounds-provider').value = setting.backgrounds_provider || '';
    document.getElementById('backgrounds-api-key').value = setting.backgrounds_api_key || '';
    
    document.getElementById('thumbnail-style').value = setting.thumbnail_style || 'modern';
    document.getElementById('thumbnail-template').value = setting.thumbnail_template || '';
    document.getElementById('thumbnail-overlay').value = setting.thumbnail_overlay || '';
    
    document.getElementById('seo-title').value = setting.seo_title || '';
    document.getElementById('seo-description').value = setting.seo_description || '';
    document.getElementById('seo-tags').value = setting.seo_tags || '';
    
    document.getElementById('publishing-platform').value = setting.publishing_platform || 'youtube';
    document.getElementById('publishing-schedule').value = setting.publishing_schedule || 'immediate';
    document.getElementById('publishing-auto-upload').checked = setting.publishing_auto_upload || false;
}

// Save settings to Supabase
async function saveSettings() {
    const setting = {
        content_source: document.getElementById('content-source').value,
        content_api_key: document.getElementById('content-api-key').value,
        content_endpoint: document.getElementById('content-endpoint').value,
        content_model: document.getElementById('content-model').value,
        
        ai_provider: document.getElementById('ai-provider').value,
        ai_api_key: document.getElementById('ai-api-key').value,
        ai_model: document.getElementById('ai-model').value,
        ai_temperature: parseFloat(document.getElementById('ai-temperature').value),
        
        video_resolution: document.getElementById('video-resolution').value,
        video_fps: parseInt(document.getElementById('video-fps').value),
        video_duration: parseInt(document.getElementById('video-duration').value),
        
        backgrounds_provider: document.getElementById('backgrounds-provider').value,
        backgrounds_api_key: document.getElementById('backgrounds-api-key').value,
        
        thumbnail_style: document.getElementById('thumbnail-style').value,
        thumbnail_template: document.getElementById('thumbnail-template').value,
        thumbnail_overlay: document.getElementById('thumbnail-overlay').value,
        
        seo_title: document.getElementById('seo-title').value,
        seo_description: document.getElementById('seo-description').value,
        seo_tags: document.getElementById('seo-tags').value,
        
        publishing_platform: document.getElementById('publishing-platform').value,
        publishing_schedule: document.getElementById('publishing-schedule').value,
        publishing_auto_upload: document.getElementById('publishing-auto-upload').checked,
        
        updated_at: new Date().toISOString()
    };
    
    try {
        // Check if settings exist
        const existing = await supabase.get('settings', '?select=id');
        
        if (existing.length > 0) {
            await supabase.patch('settings', existing[0].id, setting);
        } else {
            await supabase.post('settings', setting);
        }
        
        settingsCache = setting;
        hasUnsavedChanges = false;
        updateSaveStatus();
        showNotification(translations[currentLanguage]['save.success'], 'success');
    } catch (error) {
        console.error('Failed to save settings:', error);
        showNotification(translations[currentLanguage]['save.error'], 'error');
    }
}

// Setup event listeners for form inputs
function setupEventListeners() {
    // Save button
    document.getElementById('save-button').addEventListener('click', async () => {
        await saveSettings();
    });
    
    // Language toggle
    document.getElementById('language-toggle').addEventListener('click', () => {
        const newLang = currentLanguage === 'en' ? 'ar' : 'en';
        setLanguage(newLang);
        showNotification(`Switched to ${translations[newLang]['language.toggle']}`, 'info');
    });
    
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', () => {
        const html = document.documentElement;
        if (html.getAttribute('data-theme') === 'dark') {
            html.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        } else {
            html.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        }
    });
    
    // Run pipeline button
    document.getElementById('run-pipeline').addEventListener('click', () => {
        runPipeline();
    });
    
    // Form inputs - mark as having unsaved changes
    const formInputs = document.querySelectorAll('input, select, textarea');
    formInputs.forEach(input => {
        input.addEventListener('change', () => {
            hasUnsavedChanges = true;
            updateSaveStatus();
        });
        
        input.addEventListener('input', () => {
            hasUnsavedChanges = true;
            updateSaveStatus();
        });
    });
}

// Setup auto-save functionality
function setupAutoSave() {
    let autoSaveTimeout;
    
    const formInputs = document.querySelectorAll('input, select, textarea');
    formInputs.forEach(input => {
        input.addEventListener('change', () => {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                saveSettings();
            }, 5000); // Auto-save after 5 seconds of inactivity
        });
    });
}

// Update save status indicator
function updateSaveStatus() {
    const saveStatus = document.getElementById('save-status');
    if (hasUnsavedChanges) {
        saveStatus.textContent = currentLanguage === 'ar' ? 'هناك تغييرات غير محفوظة' : 'Unsaved changes';
        saveStatus.className = 'save-status dirty';
    } else {
        saveStatus.textContent = currentLanguage === 'ar' ? 'جميع التغييرات محفوظة' : 'All changes saved';
        saveStatus.className = 'save-status clean';
    }
}

// Update connection status
function updateConnectionStatus(connected) {
    const statusIndicator = document.getElementById('connection-status');
    const statusText = document.getElementById('connection-text');
    
    if (connected) {
        statusIndicator.className = 'status-indicator connected';
        statusText.textContent = translations[currentLanguage]['connection.connected'];
    } else {
        statusIndicator.className = 'status-indicator disconnected';
        statusText.textContent = translations[currentLanguage]['connection.disconnected'];
    }
}

// Run pipeline manually
async function runPipeline() {
    const runButton = document.getElementById('run-pipeline');
    const originalText = runButton.textContent;
    
    try {
        runButton.disabled = true;
        runButton.textContent = currentLanguage === 'ar' ? 'جارٍ التشغيل...' : 'Running...';
        
        // Trigger GitHub Actions workflow_dispatch
        const [owner, repo] = (window?.CONFIG?.GITHUB_REPO || '').split('/').filter(Boolean);
if (!owner || !repo) {
  showNotification(currentLanguage === 'ar' ? 'لم يتم تكوين المستودع في الإعدادات' : 'Repository not configured in settings', 'error');
  runButton.disabled = false;
  runButton.textContent = originalText;
  return;
}
const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/dispatches`, {
            method: 'POST',
            headers: {
                'Authorization': `token ${window?.CONFIG?.GITHUB_TOKEN || ''}`,
                'Accept': 'application/vnd.github.v3+json'
            },
            body: JSON.stringify({
                event_type: 'workflow_dispatch',
                client_payload: {
                    trigger: 'manual',
                    timestamp: new Date().toISOString()
                }
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to trigger workflow');
        }
        
        showNotification(currentLanguage === 'ar' ? 'تم تشغيل خط الأنابيب بنجاح' : 'Pipeline started successfully', 'success');
        
        // Update pipeline status
        await updatePipelineStatus();
        
    } catch (error) {
        console.error('Failed to run pipeline:', error);
        showNotification(currentLanguage === 'ar' ? 'خطأ في تشغيل خط الأنابيب' : 'Failed to run pipeline', 'error');
    } finally {
        runButton.disabled = false;
        runButton.textContent = originalText;
    }
}

// Update pipeline status
async function updatePipelineStatus() {
    try {
        const runs = await supabase.get('pipeline_runs', '?select=*&order=created_at.desc&limit=10');
        populatePipelineTable(runs);
    } catch (error) {
        console.error('Failed to update pipeline status:', error);
    }
}

// Populate pipeline table
function populatePipelineTable(runs) {
    const tableBody = document.querySelector('#pipeline-table tbody');
    tableBody.innerHTML = '';
    
    runs.forEach(run => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${new Date(run.created_at).toLocaleString()}</td>
            <td><span class="status ${run.status}">${translations[currentLanguage][`status.${run.status}`] || run.status}</span></td>
            <td>${run.trigger || 'manual'}</td>
            <td>${run.duration ? `${run.duration}s` : '-'}</td>
            <td><button class="btn-small" onclick="viewPipelineLogs('${run.id}')">View Logs</button></td>
        `;
        tableBody.appendChild(row);
    });
}

// View pipeline logs
async function viewPipelineLogs(runId) {
    try {
        const logs = await supabase.get('pipeline_logs', `?pipeline_run_id=eq.${runId}&order=created_at.asc`);
        const logsContainer = document.getElementById('logs-container');
        logsContainer.innerHTML = '';
        
        logs.forEach(log => {
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `
                <div class="log-timestamp">${new Date(log.created_at).toLocaleString()}</div>
                <div class="log-level ${log.level}">${log.level.toUpperCase()}</div>
                <div class="log-message">${log.message}</div>
            `;
            logsContainer.appendChild(logEntry);
        });
        
        document.getElementById('logs-modal').style.display = 'block';
    } catch (error) {
        console.error('Failed to load logs:', error);
    }
}

// Update analytics
async function updateAnalytics() {
    try {
        const analytics = await supabase.get('analytics', '?select=*&order=created_at.desc&limit=1');
        if (analytics.length > 0) {
            const data = analytics[0];
            document.getElementById('analytics-videos').textContent = data.videos_published || 0;
            document.getElementById('analytics-views').textContent = data.total_views || 0;
            document.getElementById('analytics-engagement').textContent = `${data.engagement_rate || 0}%`;
        }
    } catch (error) {
        console.error('Failed to update analytics:', error);
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const container = document.getElementById('notifications');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            container.removeChild(notification);
        }, 300);
    }, 3000);
}

// Setup navigation
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.content-section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update active state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Show section
            const target = link.getAttribute('href').substring(1);
            sections.forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(target).classList.add('active');
            
            // Update analytics when analytics section is shown
            if (target === 'analytics') {
                updateAnalytics();
            }
        });
    });
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Set initial theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    initDashboard();
    setupNavigation();
    
    // Update pipeline status and analytics periodically
    setInterval(updatePipelineStatus, 30000); // Every 30 seconds
    setInterval(updateAnalytics, 60000); // Every minute
});
