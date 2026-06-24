// Application State Manager
const AppState = {
    currentView: 'dashboard',
    resumeProfile: 'unicorn',
    currentKnowledgeCategory: 'ml',
    currentQuizIndex: 0,
    filteredQuizList: [],
    currentFlashcardIndex: 0,
    currentFlashcardVersion: 'simple', // 'simple' or 'detail'
    pptTheme: 'academic', // 'dark', 'teal', or 'academic'
    pptOutline: [],   // Array of PPT slide objects
    theme: 'light-teal', // 默认全局主题
    resumeHistory: {
        undo: [],
        redo: [],
        isRestoring: false
    },
    globalSearch: {
        results: [],
        activeIndex: -1
    },
    stats: {
        masteredCards: [], // 记住的卡片ID列表
        reviewedCards: [], // 已复习的卡片ID列表
        quizScores: {},     // { quizId: score }
    }
};

AppState.userConfig = null;

const WORKSPACE_STORAGE_KEYS = [
    { key: 'interview_prep_stats', label: '学习进度' },
    { key: 'interview_prep_edited_resumes', label: '在线简历编辑数据' },
    { key: 'interview_prep_theme', label: '全局主题' },
    { key: 'interview_prep_user_config', label: '用户配置' },
    { key: 'interview_prep_job_target', label: '岗位匹配草稿' },
    { key: 'interview_prep_resume_versions', label: '简历版本历史' },
    { key: 'resume_forced_sync_version', label: '简历数据版本' }
];

const JOB_TARGET_STORAGE_KEY = 'interview_prep_job_target';
const RESUME_HISTORY_LIMIT = 30;
const RESUME_VERSION_STORAGE_KEY = 'interview_prep_resume_versions';
const RESUME_VERSION_LIMIT = 8;

const JOB_MATCH_KEYWORDS = [
    { label: 'Python', aliases: ['python'] },
    { label: 'SQL', aliases: ['sql'] },
    { label: 'PyTorch', aliases: ['pytorch'] },
    { label: 'TensorFlow', aliases: ['tensorflow', 'tenserflow'] },
    { label: 'scikit-learn', aliases: ['scikit-learn', 'sklearn'] },
    { label: 'pandas / GeoPandas', aliases: ['pandas', 'geopandas'] },
    { label: 'GDAL', aliases: ['gdal'] },
    { label: 'ArcGIS / QGIS', aliases: ['arcgis', 'qgis'] },
    { label: '遥感影像处理', aliases: ['遥感', '卫星影像', '影像处理', 'remote sensing'] },
    { label: 'GIS 空间分析', aliases: ['gis', '空间分析', '空间数据'] },
    { label: '语义分割', aliases: ['语义分割', 'semantic segmentation'] },
    { label: '目标检测', aliases: ['目标检测', 'object detection'] },
    { label: 'SAM / SAM 2', aliases: ['sam', 'segment anything'] },
    { label: 'YOLO', aliases: ['yolo'] },
    { label: 'U-Net / DeepLabv3', aliases: ['u-net', 'unet', 'deeplabv3', 'deeplab'] },
    { label: 'Mask R-CNN', aliases: ['mask r-cnn', 'maskrcnn', 'r-cnn', 'rcnn'] },
    { label: 'LSTM / 时序预测', aliases: ['lstm', '时序预测', '时间序列'] },
    { label: 'LightGBM / Random Forest', aliases: ['lightgbm', 'random forest', 'randomforest', '随机森林'] },
    { label: 'RAG / 知识库', aliases: ['rag', '知识库', '检索增强'] },
    { label: 'Agent / Vibe Coding', aliases: ['agent', 'claude code', 'codex', 'antigravity', 'vibe coding'] },
    { label: 'MLOps / 模型部署', aliases: ['mlops', '模型部署', '模型上线', 'docker', 'fastapi'] },
    { label: '无人机 / 正射建模', aliases: ['无人机', '大疆', 'pix4d', '正射', '三维建模'] },
    { label: '水环境 / 水质算法', aliases: ['水质', '水环境', '黑臭', 'fui', 'dbwi', 'qa'] }
];

const DEFAULT_USER_CONFIG = {
    candidateName: '杨佳',
    targetRoles: 'AI算法工程师 / 遥感算法工程师',
    targetSalary: '15K',
    preferredExport: 'pdf',
    updatedAt: null
};

window.setGlobalTheme = function(themeName) {
    document.body.className = document.body.className.replace(/\btheme-[^\s]+\b/g, '');
    document.body.classList.add(`theme-${themeName}`);
    AppState.theme = themeName;
    localStorage.setItem('interview_prep_theme', themeName);
    
    // 同步下拉框的选择
    const select = document.getElementById('global-theme-select');
    if (select) select.value = themeName;
};

// 页面初始化
document.addEventListener("DOMContentLoaded", () => {
    loadProgress();
    loadUserConfig();
    initApp();
    setupEventListeners();
});

// 从 LocalStorage 加载学习进度
function loadProgress() {
    const saved = localStorage.getItem('interview_prep_stats');
    if (saved) {
        try {
            AppState.stats = JSON.parse(saved);
            if (!AppState.stats.masteredCards) AppState.stats.masteredCards = [];
            if (!AppState.stats.reviewedCards) AppState.stats.reviewedCards = [];
            if (!AppState.stats.quizScores) AppState.stats.quizScores = {};
        } catch (e) {
            console.error("加载学习数据出错，重置中...", e);
        }
    }
}

// 保存学习进度到 LocalStorage
function saveProgress() {
    localStorage.setItem('interview_prep_stats', JSON.stringify(AppState.stats));
    updateDashboardStats();
}

function loadUserConfig() {
    const saved = localStorage.getItem('interview_prep_user_config');
    if (!saved) {
        AppState.userConfig = { ...DEFAULT_USER_CONFIG };
        localStorage.setItem('interview_prep_user_config', JSON.stringify(AppState.userConfig));
        return;
    }

    try {
        AppState.userConfig = { ...DEFAULT_USER_CONFIG, ...JSON.parse(saved) };
    } catch (err) {
        console.error('Failed to load user config', err);
        AppState.userConfig = { ...DEFAULT_USER_CONFIG };
    }
}

function getStorageSnapshot() {
    return WORKSPACE_STORAGE_KEYS.map((item) => {
        const value = localStorage.getItem(item.key);
        const bytes = value ? new Blob([value]).size : 0;
        return { ...item, exists: value !== null, bytes, value };
    });
}

function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB'];
    let size = bytes;
    let idx = 0;
    while (size >= 1024 && idx < units.length - 1) {
        size /= 1024;
        idx += 1;
    }
    return `${size.toFixed(idx === 0 ? 0 : 1)} ${units[idx]}`;
}

function downloadJSON(filename, payload) {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function downloadTextFile(filename, text, mimeType) {
    const blob = new Blob([text], { type: `${mimeType};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function escapeHTML(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function stripMarkdown(value) {
    return String(value ?? '')
        .replace(/\*\*/g, '')
        .replace(/`/g, '')
        .replace(/\s+/g, ' ')
        .trim();
}

function getActiveResumeProfile() {
    const data = getEditedResumeData();
    return data.profiles?.[AppState.resumeProfile] || data.profiles?.unicorn || null;
}

function buildCareerReportModel() {
    loadUserConfig();
    const profile = getActiveResumeProfile();
    const personal = profile?.personalInfo || {};
    const sections = profile?.sections || {};
    const portfolio = (window.portfolioCases || []).slice();
    const mainPortfolio = portfolio
        .filter((item) => item.priority === '主推' || item.priority === '涓绘帹')
        .concat(portfolio.filter((item) => item.priority !== '主推' && item.priority !== '涓绘帹'))
        .slice(0, 6);
    const radar = (window.knowledgeRadar || [])
        .slice()
        .sort((a, b) => (b.relevance || 0) - (a.relevance || 0))
        .slice(0, 10);
    const workItems = sections.workExperience?.items || [];
    const projectItems = sections.projects?.items || [];
    const skillItems = sections.skills?.items || [];

    return {
        generatedAt: new Date().toISOString(),
        config: AppState.userConfig || DEFAULT_USER_CONFIG,
        personal,
        workItems,
        projectItems,
        skillItems,
        portfolio: mainPortfolio,
        radar,
        stats: {
            resumeProfiles: getEditedResumeData()?.profiles ? Object.keys(getEditedResumeData().profiles).length : 0,
            portfolioCases: portfolio.length,
            radarTopics: window.knowledgeRadar ? window.knowledgeRadar.length : 0,
            knowledgeItems: window.knowledgeData ? window.knowledgeData.reduce((sum, cat) => sum + cat.items.length, 0) : 0
        }
    };
}

function renderHighlights(items, limit = 3) {
    return (items || [])
        .slice(0, limit)
        .map((item) => `- ${stripMarkdown(item)}`)
        .join('\n');
}

function generateCareerReportMarkdown() {
    const model = buildCareerReportModel();
    const jobTarget = getStoredJobTarget();
    const jobAnalysis = jobTarget.jdText ? (jobTarget.analysis || createJobTargetAnalysis(jobTarget.jobTitle, jobTarget.jdText)) : null;
    const lines = [];
    lines.push(`# 求职材料报告 - ${model.config.candidateName || model.personal.name || '候选人'}`);
    lines.push('');
    lines.push(`生成时间：${model.generatedAt.slice(0, 10)}`);
    lines.push(`目标岗位：${model.config.targetRoles || model.personal.targetJob || '未配置'}`);
    lines.push(`目标薪资：${model.config.targetSalary || model.personal.targetSalary || '未配置'}`);
    if (model.personal.phone || model.personal.email) {
        lines.push(`联系方式：${[model.personal.phone, model.personal.email].filter(Boolean).join(' / ')}`);
    }
    lines.push('');
    lines.push('## 1. 候选人定位');
    lines.push('');
    lines.push(`- 当前简历画像：${AppState.resumeProfile}`);
    lines.push(`- 作品集案例：${model.stats.portfolioCases} 个`);
    lines.push(`- 知识雷达：${model.stats.radarTopics} 条前沿技术概念`);
    lines.push(`- 知识库条目：${model.stats.knowledgeItems} 条`);
    if (jobAnalysis) {
        lines.push('');
        lines.push('## 1.1 岗位匹配分析');
        lines.push('');
        lines.push(`- 目标岗位：${stripMarkdown(jobAnalysis.jobTitle || jobTarget.jobTitle || '未命名岗位')}`);
        lines.push(`- 匹配度：${jobAnalysis.score}%`);
        lines.push(`- 结论：${stripMarkdown(jobAnalysis.summary)}`);
        if (jobAnalysis.resumeHits?.length) lines.push(`- 简历已覆盖：${jobAnalysis.resumeHits.join(' / ')}`);
        if (jobAnalysis.evidenceOnly?.length) lines.push(`- 作品集可补强：${jobAnalysis.evidenceOnly.join(' / ')}`);
        if (jobAnalysis.missing?.length) lines.push(`- 待补缺口：${jobAnalysis.missing.join(' / ')}`);
    }
    lines.push('');
    lines.push('## 2. 核心经历摘要');
    model.workItems.slice(0, 3).forEach((item) => {
        lines.push('');
        lines.push(`### ${stripMarkdown(item.company || item.name || '工作经历')}`);
        if (item.period || item.role) lines.push(`${stripMarkdown(item.period || '')} ${stripMarkdown(item.role || '')}`.trim());
        const highlights = renderHighlights(item.highlights, 4);
        if (highlights) lines.push(highlights);
    });
    lines.push('');
    lines.push('## 3. 主推项目');
    model.projectItems.slice(0, 4).forEach((item) => {
        lines.push('');
        lines.push(`### ${stripMarkdown(item.name || '项目')}`);
        if (item.period || item.role) lines.push(`${stripMarkdown(item.period || '')} ${stripMarkdown(item.role || '')}`.trim());
        const highlights = renderHighlights(item.highlights, 4);
        if (highlights) lines.push(highlights);
    });
    lines.push('');
    lines.push('## 4. 作品集证据链');
    model.portfolio.forEach((item) => {
        lines.push('');
        lines.push(`### ${stripMarkdown(item.title)}`);
        lines.push(`- 角色：${stripMarkdown(item.role)}`);
        lines.push(`- 摘要：${stripMarkdown(item.summary)}`);
        lines.push(`- 技术栈：${(item.stack || []).map(stripMarkdown).join(' / ')}`);
        lines.push(`- 指标：${(item.metrics || []).map(stripMarkdown).join(' / ')}`);
        lines.push(`- 证据路径：${stripMarkdown(item.evidence)}`);
    });
    lines.push('');
    lines.push('## 5. 前沿技术补强');
    model.radar.forEach((item) => {
        lines.push(`- ${stripMarkdown(item.name)}：${stripMarkdown(item.summary)}`);
    });
    lines.push('');
    lines.push('## 6. 下一步建议');
    lines.push('');
    lines.push('- 给每个主推项目补一张“问题-方案-指标-证据-复盘”卡片。');
    lines.push('- 将作品集证据路径整理为可点击或可打包的附件目录。');
    lines.push('- 针对 AI算法工程师、遥感算法工程师分别导出岗位定制版简历。');
    lines.push('- 把知识雷达中“立即补”的概念沉淀为深度知识卡和面试答法。');
    lines.push('');
    return lines.join('\n');
}

function generateCareerReportHTML() {
    const markdown = generateCareerReportMarkdown();
    const body = markdown
        .split('\n')
        .map((line) => {
            if (line.startsWith('# ')) return `<h1>${escapeHTML(line.slice(2))}</h1>`;
            if (line.startsWith('## ')) return `<h2>${escapeHTML(line.slice(3))}</h2>`;
            if (line.startsWith('### ')) return `<h3>${escapeHTML(line.slice(4))}</h3>`;
            if (line.startsWith('- ')) return `<li>${escapeHTML(line.slice(2))}</li>`;
            if (!line.trim()) return '';
            return `<p>${escapeHTML(line)}</p>`;
        })
        .join('\n')
        .replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul>\n${match}</ul>\n`);

    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>求职材料报告</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.7; color: #0f172a; max-width: 920px; margin: 0 auto; padding: 36px 22px; background: #f8fafc; }
    h1, h2, h3 { line-height: 1.25; }
    h1 { font-size: 30px; margin-bottom: 20px; }
    h2 { margin-top: 30px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
    h3 { margin-top: 22px; color: #0369a1; }
    p, li { color: #334155; }
    ul { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 20px 14px 34px; }
  </style>
</head>
<body>
${body}
</body>
</html>`;
}

function renderCareerReportPreview() {
    const preview = document.getElementById('career-report-preview');
    if (!preview) return;

    const model = buildCareerReportModel();
    const topPortfolio = model.portfolio.slice(0, 3);
    const topRadar = model.radar.slice(0, 5);

    preview.innerHTML = `
        <div class="report-preview-hero">
            <div>
                <span>Report Preview</span>
                <strong>${escapeHTML(model.config.candidateName || model.personal.name || '候选人')}</strong>
                <p>${escapeHTML(model.config.targetRoles || model.personal.targetJob || '未配置目标岗位')}</p>
            </div>
            <div class="report-preview-date">${escapeHTML(model.generatedAt.slice(0, 10))}</div>
        </div>
        <div class="report-mini-stats">
            <div><span>作品集</span><strong>${model.stats.portfolioCases}</strong></div>
            <div><span>知识雷达</span><strong>${model.stats.radarTopics}</strong></div>
            <div><span>知识库</span><strong>${model.stats.knowledgeItems}</strong></div>
        </div>
        <div class="report-preview-columns">
            <div>
                <h3>主推证据</h3>
                ${topPortfolio.map((item) => `<p><strong>${escapeHTML(item.title)}</strong><br>${escapeHTML(stripMarkdown(item.summary))}</p>`).join('')}
            </div>
            <div>
                <h3>前沿补强</h3>
                ${topRadar.map((item) => `<p><strong>${escapeHTML(item.name)}</strong><br>${escapeHTML(stripMarkdown(item.summary))}</p>`).join('')}
            </div>
        </div>
    `;
    if (window.lucide) lucide.createIcons();
}

window.renderCareerReportPreview = renderCareerReportPreview;

window.exportCareerReportMarkdown = function() {
    const model = buildCareerReportModel();
    const filename = `求职材料报告_${model.config.candidateName || 'candidate'}_${new Date().toISOString().slice(0, 10)}.md`;
    downloadTextFile(filename, generateCareerReportMarkdown(), 'text/markdown');
    showNotification('求职材料报告 Markdown 已导出');
};

window.exportCareerReportHTML = function() {
    const model = buildCareerReportModel();
    const filename = `求职材料报告_${model.config.candidateName || 'candidate'}_${new Date().toISOString().slice(0, 10)}.html`;
    downloadTextFile(filename, generateCareerReportHTML(), 'text/html');
    showNotification('求职材料报告 HTML 已导出');
};

function getStoredJobTarget() {
    const saved = localStorage.getItem(JOB_TARGET_STORAGE_KEY);
    if (!saved) return { jobTitle: '', jdText: '', analysis: null, updatedAt: null };
    try {
        return { jobTitle: '', jdText: '', analysis: null, updatedAt: null, ...JSON.parse(saved) };
    } catch (err) {
        console.error('Failed to load job target', err);
        return { jobTitle: '', jdText: '', analysis: null, updatedAt: null };
    }
}

function saveJobTarget(target) {
    const payload = {
        jobTitle: target.jobTitle || '',
        jdText: target.jdText || '',
        analysis: target.analysis || null,
        updatedAt: new Date().toISOString()
    };
    localStorage.setItem(JOB_TARGET_STORAGE_KEY, JSON.stringify(payload));
    return payload;
}

function normalizeMatchText(value) {
    return stripMarkdown(value).toLowerCase();
}

function textHasAlias(text, aliases) {
    return aliases.some((alias) => text.includes(alias.toLowerCase()));
}

function buildResumeMatchText(profile) {
    if (!profile) return '';
    const clone = JSON.parse(JSON.stringify(profile));
    if (clone.personalInfo?.avatar) clone.personalInfo.avatar = '';
    return normalizeMatchText(JSON.stringify(clone));
}

function buildPortfolioMatchText() {
    return normalizeMatchText(JSON.stringify(window.portfolioCases || []));
}

function createJobTargetAnalysis(jobTitle, jdText) {
    const profile = getActiveResumeProfile();
    const jdTextNormalized = normalizeMatchText(`${jobTitle || ''}\n${jdText || ''}`);
    const resumeText = buildResumeMatchText(profile);
    const portfolioText = buildPortfolioMatchText();
    const jdKeywords = JOB_MATCH_KEYWORDS.filter((item) => textHasAlias(jdTextNormalized, item.aliases));
    const resumeHits = jdKeywords.filter((item) => textHasAlias(resumeText, item.aliases));
    const portfolioHits = jdKeywords.filter((item) => textHasAlias(portfolioText, item.aliases));
    const missing = jdKeywords.filter((item) => !resumeHits.includes(item) && !portfolioHits.includes(item));
    const jdCoverage = jdKeywords.length ? resumeHits.length / jdKeywords.length : 0;
    const evidenceCoverage = jdKeywords.length ? Math.min(1, (resumeHits.length + portfolioHits.length * 0.5) / jdKeywords.length) : 0;
    const score = jdKeywords.length ? Math.round(jdCoverage * 70 + evidenceCoverage * 30) : 0;
    const strongest = resumeHits.slice(0, 8).map((item) => item.label);
    const evidenceOnly = portfolioHits.filter((item) => !resumeHits.includes(item)).slice(0, 6).map((item) => item.label);
    const missingLabels = missing.slice(0, 8).map((item) => item.label);

    return {
        jobTitle: jobTitle || AppState.userConfig?.targetRoles || '',
        jdKeywords: jdKeywords.map((item) => item.label),
        resumeHits: strongest,
        evidenceOnly,
        missing: missingLabels,
        score,
        summary: score >= 85
            ? '岗位关键词与当前简历高度一致，可直接做岗位化措辞微调。'
            : score >= 65
                ? '岗位方向匹配，但仍建议把作品集证据补进简历核心项目。'
                : '岗位要求与当前简历存在明显缺口，应先补关键词和项目证据。',
        recommendations: [
            strongest.length ? `把 ${strongest.slice(0, 4).join('、')} 放到简历前两屏。` : '先补充岗位 JD 中明确要求的核心技术关键词。',
            evidenceOnly.length ? `将作品集中的 ${evidenceOnly.slice(0, 3).join('、')} 转写到项目经历。` : '检查主推项目是否都有“任务-技术-指标-结果”。',
            missingLabels.length ? `缺口项：${missingLabels.slice(0, 4).join('、')}，不要硬编，优先补学习卡或项目证据。` : '当前未发现明显关键词缺口，重点压缩弱相关内容。'
        ]
    };
}

function renderJobTargetPanel() {
    const titleInput = document.getElementById('job-target-title');
    const jdInput = document.getElementById('job-target-jd');
    const preview = document.getElementById('job-match-preview');
    if (!titleInput || !jdInput || !preview) return;

    const target = getStoredJobTarget();
    titleInput.value = target.jobTitle || '';
    jdInput.value = target.jdText || '';

    const analysis = target.analysis;
    if (!analysis) {
        preview.innerHTML = `
            <div class="job-match-empty">
                <i data-lucide="scan-search"></i>
                <strong>等待岗位 JD</strong>
                <span>粘贴岗位描述后生成匹配率、已覆盖关键词、作品集证据和缺口建议。</span>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    preview.innerHTML = `
        <div class="job-match-score">
            <span>岗位匹配度</span>
            <strong>${analysis.score}%</strong>
            <p>${escapeHTML(analysis.summary)}</p>
        </div>
        <div class="job-match-columns">
            <div>
                <h3>简历已覆盖</h3>
                ${renderJobMatchTags(analysis.resumeHits, 'ok')}
            </div>
            <div>
                <h3>作品集可补强</h3>
                ${renderJobMatchTags(analysis.evidenceOnly, 'info')}
            </div>
            <div>
                <h3>待补缺口</h3>
                ${renderJobMatchTags(analysis.missing, 'warn')}
            </div>
        </div>
        <div class="job-match-actions-list">
            ${analysis.recommendations.map((item) => `<p>${escapeHTML(item)}</p>`).join('')}
        </div>
    `;
    if (window.lucide) lucide.createIcons();
}

function renderJobMatchTags(items, tone) {
    if (!items || !items.length) return '<p class="job-match-muted">暂无</p>';
    return `<div class="job-match-tags ${tone}">${items.map((item) => `<span>${escapeHTML(item)}</span>`).join('')}</div>`;
}

function generateJobTargetMarkdown() {
    const target = getStoredJobTarget();
    const analysis = target.analysis || createJobTargetAnalysis(target.jobTitle, target.jdText);
    const lines = [];
    lines.push(`# 岗位匹配分析 - ${analysis.jobTitle || '未命名岗位'}`);
    lines.push('');
    lines.push(`生成时间：${new Date().toISOString().slice(0, 10)}`);
    lines.push(`当前简历画像：${AppState.resumeProfile}`);
    lines.push(`匹配度：${analysis.score}%`);
    lines.push('');
    lines.push('## 结论');
    lines.push('');
    lines.push(analysis.summary);
    lines.push('');
    lines.push('## 已覆盖关键词');
    lines.push('');
    (analysis.resumeHits || []).forEach((item) => lines.push(`- ${item}`));
    lines.push('');
    lines.push('## 作品集可补强');
    lines.push('');
    (analysis.evidenceOnly || []).forEach((item) => lines.push(`- ${item}`));
    lines.push('');
    lines.push('## 待补缺口');
    lines.push('');
    (analysis.missing || []).forEach((item) => lines.push(`- ${item}`));
    lines.push('');
    lines.push('## 简历定制建议');
    lines.push('');
    (analysis.recommendations || []).forEach((item) => lines.push(`- ${item}`));
    return lines.join('\n');
}

window.saveJobTargetDraft = function() {
    const jobTitle = document.getElementById('job-target-title')?.value.trim() || '';
    const jdText = document.getElementById('job-target-jd')?.value.trim() || '';
    saveJobTarget({ jobTitle, jdText, analysis: null });
    renderDataCenter();
    showNotification('岗位草稿已保存');
};

window.analyzeJobTarget = function() {
    const jobTitle = document.getElementById('job-target-title')?.value.trim() || '';
    const jdText = document.getElementById('job-target-jd')?.value.trim() || '';
    if (!jdText) {
        alert('请先粘贴岗位 JD。');
        return;
    }
    const analysis = createJobTargetAnalysis(jobTitle, jdText);
    saveJobTarget({ jobTitle, jdText, analysis });
    renderDataCenter();
    showNotification('岗位匹配分析已生成');
};

window.exportJobTargetMarkdown = function() {
    const target = getStoredJobTarget();
    if (!target.jdText) {
        alert('请先粘贴岗位 JD 并生成分析。');
        return;
    }
    const filename = `岗位匹配分析_${target.jobTitle || 'target'}_${new Date().toISOString().slice(0, 10)}.md`;
    downloadTextFile(filename, generateJobTargetMarkdown(), 'text/markdown');
    showNotification('岗位匹配分析 Markdown 已导出');
};

window.clearJobTargetDraft = function() {
    localStorage.removeItem(JOB_TARGET_STORAGE_KEY);
    renderDataCenter();
    showNotification('岗位匹配草稿已清空');
};

function renderDataCenter() {
    const health = document.getElementById('data-center-health');
    const list = document.getElementById('data-center-storage-list');
    if (!health || !list) return;

    loadUserConfig();
    const snapshot = getStorageSnapshot();
    const totalBytes = snapshot.reduce((sum, item) => sum + item.bytes, 0);
    const activeKeys = snapshot.filter((item) => item.exists).length;
    const editedResume = getEditedResumeData();
    const resumeProfiles = editedResume?.profiles ? Object.keys(editedResume.profiles).length : 0;
    const resumeVersions = getResumeVersions().length;
    const radarTopics = window.knowledgeRadar ? window.knowledgeRadar.length : 0;

    health.innerHTML = [
        { label: '本地数据项', value: `${activeKeys} / ${snapshot.length}` },
        { label: '本地占用', value: formatBytes(totalBytes) },
        { label: '简历画像', value: `${resumeProfiles} 个` },
        { label: '保存版本', value: `${resumeVersions} 个` },
        { label: '知识雷达', value: `${radarTopics} 条` }
    ].map((item) => `
        <div class="data-health-card">
            <span>${item.label}</span>
            <strong>${item.value}</strong>
        </div>
    `).join('');

    list.innerHTML = snapshot.map((item) => `
        <div class="storage-row">
            <div>
                <strong>${item.label}</strong>
                <span>${item.key}</span>
            </div>
            <div class="storage-row-status ${item.exists ? 'ok' : 'empty'}">
                ${item.exists ? formatBytes(item.bytes) : '未生成'}
            </div>
        </div>
    `).join('');

    const candidateName = document.getElementById('config-candidate-name');
    const targetRoles = document.getElementById('config-target-roles');
    const targetSalary = document.getElementById('config-target-salary');
    const preferredExport = document.getElementById('config-preferred-export');
    if (candidateName) candidateName.value = AppState.userConfig.candidateName || '';
    if (targetRoles) targetRoles.value = AppState.userConfig.targetRoles || '';
    if (targetSalary) targetSalary.value = AppState.userConfig.targetSalary || '';
    if (preferredExport) preferredExport.value = AppState.userConfig.preferredExport || 'pdf';

    renderCareerReportPreview();
    renderJobTargetPanel();

    if (window.lucide) lucide.createIcons();
}

window.renderDataCenter = renderDataCenter;

window.saveUserConfigFromForm = function() {
    AppState.userConfig = {
        candidateName: document.getElementById('config-candidate-name')?.value.trim() || DEFAULT_USER_CONFIG.candidateName,
        targetRoles: document.getElementById('config-target-roles')?.value.trim() || DEFAULT_USER_CONFIG.targetRoles,
        targetSalary: document.getElementById('config-target-salary')?.value.trim() || DEFAULT_USER_CONFIG.targetSalary,
        preferredExport: document.getElementById('config-preferred-export')?.value || DEFAULT_USER_CONFIG.preferredExport,
        updatedAt: new Date().toISOString()
    };
    localStorage.setItem('interview_prep_user_config', JSON.stringify(AppState.userConfig));
    renderDataCenter();
    showNotification('用户配置已保存');
};

window.exportWorkspaceBackup = function() {
    const localData = {};
    getStorageSnapshot().forEach((item) => {
        if (item.exists) localData[item.key] = item.value;
    });

    const payload = {
        schema: 'yj_coder_workspace_backup',
        version: 1,
        exportedAt: new Date().toISOString(),
        activeView: AppState.currentView,
        activeResumeProfile: AppState.resumeProfile,
        summary: {
            radarTopics: window.knowledgeRadar ? window.knowledgeRadar.length : 0,
            knowledgeCategories: window.knowledgeData ? window.knowledgeData.length : 0,
            portfolioCases: window.portfolioCases ? window.portfolioCases.length : 0
        },
        localStorage: localData
    };

    downloadJSON(`求职备战中心_全量备份_${new Date().toISOString().slice(0, 10)}.json`, payload);
    showNotification('全量备份已导出');
};

window.triggerWorkspaceBackupImport = function() {
    const input = document.getElementById('workspace-backup-file');
    if (input) input.click();
};

window.importWorkspaceBackup = function(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const parsed = JSON.parse(e.target.result);
            if (parsed.schema !== 'yj_coder_workspace_backup' || !parsed.localStorage) {
                alert('备份文件格式不正确，未执行恢复。');
                return;
            }
            if (!confirm('恢复会覆盖当前浏览器本地数据，确定继续？')) return;
            WORKSPACE_STORAGE_KEYS.forEach((item) => {
                if (Object.prototype.hasOwnProperty.call(parsed.localStorage, item.key)) {
                    localStorage.setItem(item.key, parsed.localStorage[item.key]);
                }
            });
            showNotification('备份恢复成功，正在刷新页面');
            setTimeout(() => location.reload(), 600);
        } catch (err) {
            console.error(err);
            alert('备份文件解析失败，请检查 JSON 格式。');
        } finally {
            event.target.value = '';
        }
    };
    reader.readAsText(file);
};

window.resetWorkspaceLocalData = function() {
    if (!confirm('确定清空本浏览器中的简历编辑、学习进度和配置数据？项目文件不会被删除。')) return;
    WORKSPACE_STORAGE_KEYS.forEach((item) => localStorage.removeItem(item.key));
    showNotification('本地编辑数据已清空，正在刷新页面');
    setTimeout(() => location.reload(), 600);
};

// 初始化应用
function initApp() {
    // 渲染仪表盘数据
    updateDashboardStats();
    
    // 初始化简历视图
    renderResume();

    if (window.renderPortfolio) {
        renderPortfolio();
    }

    if (window.renderKnowledgeRadar) {
        renderKnowledgeRadar();
    }

    renderDataCenter();
    
    // 初始化知识库目录
    renderKnowledgeMenu();
    renderKnowledgeContent();
    
    // 初始化模拟面试器
    initQuizSimulator();
    
    // 初始化卡片系统
    initFlashcards();
    
    // 初始化 PPT 模板结构
    initPPTGenerator();
    
    // 初始化 Lucide 图标
    if (window.lucide) {
        lucide.createIcons();
    }
}

// 侧边栏及核心页面无刷新导航 (SPA Router)
function switchView(viewName) {
    hideGlobalSearchPanel();
    // 隐藏所有视图
    document.querySelectorAll('.page-view').forEach(view => {
        view.classList.remove('active');
    });
    
    // 移除侧边栏菜单高亮
    document.querySelectorAll('.sidebar-menu .menu-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 激活对应视图和菜单
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) {
        targetView.classList.add('active');
        AppState.currentView = viewName;
        
        const menuBtn = document.querySelector(`.sidebar-menu .menu-item[data-view="${viewName}"]`);
        if (menuBtn) {
            menuBtn.classList.add('active');
        }
        
        // 动态加载一些特定视图逻辑
        if (viewName === 'dashboard') {
            updateDashboardStats();
        } else if (viewName === 'portfolio' && window.renderPortfolio) {
            renderPortfolio();
        } else if (viewName === 'radar' && window.renderKnowledgeRadar) {
            renderKnowledgeRadar();
        } else if (viewName === 'data-center') {
            renderDataCenter();
        } else if (viewName === 'flashcards') {
            initFlashcards();
        } else if (viewName === 'ppt') {
            initPPTGenerator();
        }
    }
    
    // 移动端菜单自动收起
    if (window.closeMobileSidebar) closeMobileSidebar();
}

// 绑定各种交互事件
function setupEventListeners() {
    // 侧边栏菜单切换
    document.querySelectorAll('.sidebar-menu .menu-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.getAttribute('data-view');
            switchView(view);
        });
    });
    
    // 简历岗位 Tab 切换
    document.querySelectorAll('.resume-nav .tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.resume-nav .tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            AppState.resumeProfile = btn.getAttribute('data-profile');
            renderResume();
            // 在简历切换时，同步更新 PPT 大纲
            if (AppState.currentView === 'ppt') {
                initPPTGenerator();
            }
        });
    });
    
    // 全局搜索过滤
    const searchInput = document.getElementById('global-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim().toLowerCase();
            performGlobalSearch(query);
        });
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                searchInput.value = '';
                hideGlobalSearchPanel();
                return;
            }
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                moveGlobalSearchSelection(1);
                return;
            }
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                moveGlobalSearchSelection(-1);
                return;
            }
            if (e.key === 'Enter') {
                e.preventDefault();
                activateGlobalSearchSelection();
            }
        });
    }

    document.addEventListener('click', (e) => {
        const searchBox = document.querySelector('.search-box');
        if (searchBox && !searchBox.contains(e.target)) {
            hideGlobalSearchPanel();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (AppState.currentView !== 'resume' || !(e.ctrlKey || e.metaKey)) return;
        const target = e.target;
        const isFormField = target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
        if (isFormField || target?.isContentEditable) return;
        if (e.key.toLowerCase() === 'z' && !e.shiftKey) {
            e.preventDefault();
            undoResumeEdit();
        } else if (e.key.toLowerCase() === 'y' || (e.key.toLowerCase() === 'z' && e.shiftKey)) {
            e.preventDefault();
            redoResumeEdit();
        }
    });
    
    // 监听颜色点击 (初始化事件)
    document.querySelectorAll('.theme-color-picker .color-circle').forEach(btn => {
        btn.addEventListener('click', () => {
            const color = btn.getAttribute('data-color');
            changeThemeColor(color);
        });
    });

    // 绑定可编辑文本框失焦自动同步 (捕获阶段监听 blur，因为 blur 不冒泡)
    const paperTarget = document.getElementById('resume-paper-target');
    if (paperTarget) {
        paperTarget.addEventListener('blur', (e) => {
            const el = e.target;
            if (el.classList.contains('editable')) {
                saveFieldFromDOM(el);
            }
        }, true); 
    }
    
    // 监听 PPT 预览卡片大纲失焦自动同步
    const pptPreviewContainer = document.getElementById('ppt-slides-preview-container');
    if (pptPreviewContainer) {
        pptPreviewContainer.addEventListener('blur', (e) => {
            const el = e.target;
            if (el.hasAttribute('contenteditable')) {
                const index = parseInt(el.dataset.index);
                const type = el.dataset.type;
                if (index !== undefined && !isNaN(index)) {
                    if (type === 'title') {
                        AppState.pptOutline[index].title = el.textContent.trim();
                    } else if (type === 'body') {
                        const liElements = el.querySelectorAll('li');
                        if (liElements.length > 0) {
                            AppState.pptOutline[index].items = Array.from(liElements).map(li => li.textContent.trim());
                        } else {
                            AppState.pptOutline[index].items = el.textContent.split('\n').map(l => l.trim()).filter(l => l.length > 0);
                        }
                    }
                }
            }
        }, true);
    }
}

/* ==========================================================================
   TOAST NOTIFICATION 提示组件
   ========================================================================== */
function showNotification(message) {
    let toast = document.getElementById('app-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'app-toast';
        toast.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(99, 102, 241, 0.4);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5), 0 0 15px rgba(99, 102, 241, 0.2);
            color: #ffffff;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            z-index: 9999;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            gap: 8px;
            backdrop-filter: blur(8px);
        `;
        document.body.appendChild(toast);
    }
    toast.innerHTML = `<i data-lucide="check-circle" style="color:var(--success); width:18px; height:18px;"></i> <span>${message}</span>`;
    if (window.lucide) lucide.createIcons();
    
    // 显示
    setTimeout(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
    }, 50);
    
    // 隐藏
    setTimeout(() => {
        toast.style.transform = 'translateY(100px)';
        toast.style.opacity = '0';
    }, 3000);
}

/* ==========================================================================
   DASHBOARD 仪表盘模块
   ========================================================================== */
function updateDashboardStats() {
    // 统计总知识库条目数
    let totalItems = 0;
    knowledgeData.forEach(cat => totalItems += cat.items.length);
    document.getElementById('stat-total-knowledge').textContent = totalItems;
    
    // 统计 Flashcard 掌握情况
    const allFlashcards = [];
    knowledgeData.forEach(cat => {
        cat.items.forEach((item, index) => {
            allFlashcards.push({
                id: `${cat.id}_card_${index}`,
                category: cat.name
            });
        });
    });
    const totalCards = allFlashcards.length;
    const masteredCount = AppState.stats.masteredCards.filter(id => allFlashcards.some(c => c.id === id)).length;
    document.getElementById('stat-mastered-cards').textContent = `${masteredCount} / ${totalCards}`;
    
    // 统计模拟面试答题数与平均分
    const attemptedCount = Object.keys(AppState.stats.quizScores).length;
    let avgScore = 0;
    if (attemptedCount > 0) {
        const sum = Object.values(AppState.stats.quizScores).reduce((a, b) => a + b, 0);
        avgScore = Math.round((sum / attemptedCount) * 10) / 10;
    }
    document.getElementById('stat-quiz-attempts').textContent = `${attemptedCount} 题 (${avgScore}分)`;

    const portfolioStat = document.getElementById('stat-portfolio-cases');
    if (portfolioStat && window.portfolioCases) {
        portfolioStat.textContent = `${window.portfolioCases.length} 个`;
    }

    const radarStat = document.getElementById('stat-radar-topics');
    if (radarStat && window.knowledgeRadar) {
        radarStat.textContent = `${window.knowledgeRadar.length} 个`;
    }
    
    // 渲染最近学习的活动记录
    const activityContainer = document.getElementById('recent-activities-list');
    if (activityContainer) {
        activityContainer.innerHTML = '';
        const recentList = [];
        
        if (AppState.stats.masteredCards.length > 0) {
            recentList.push({
                type: 'success',
                title: `记住了 ${AppState.stats.masteredCards.length} 个核心考点词条`,
                time: '今天'
            });
        }
        if (attemptedCount > 0) {
            recentList.push({
                type: 'primary',
                title: `完成了 ${attemptedCount} 道场景面试题模拟评测`,
                time: '最近'
            });
        }
        recentList.push({
            type: 'secondary',
            title: `成功配置个人简历四大定制岗位画像`,
            time: '刚刚'
        });
        
        recentList.forEach(act => {
            const item = document.createElement('div');
            item.className = 'activity-item';
            item.innerHTML = `
                <div class="activity-badge ${act.type}"></div>
                <div class="activity-details">
                    <div class="activity-title">${act.title}</div>
                    <div class="activity-time">${act.time}</div>
                </div>
            `;
            activityContainer.appendChild(item);
        });
    }
}

/* ==========================================================================
   RESUME 简历编辑与本地存储模块 (结构化、可扩展)
   ========================================================================== */

// 获取或初始化保存在本地的已编辑结构化简历数据
function getEditedResumeData() {
    const forcedVersion = "v3.0_ai_rs_resume";
    if (localStorage.getItem('resume_forced_sync_version') !== forcedVersion) {
        localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(resumeData));
        localStorage.setItem('resume_forced_sync_version', forcedVersion);
        console.log("Forced sync to version: " + forcedVersion);
    }
    
    const saved = localStorage.getItem('interview_prep_edited_resumes');
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            if (parsed.profiles && parsed.profiles.unicorn && parsed.profiles.unicorn.sections) {
                return parsed;
            }
        } catch (e) {
            console.error("加载失败，回滚默认值:", e);
        }
    }
    
    const data = JSON.parse(JSON.stringify(resumeData));
    localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
    return data;
}

function getResumeStorageSnapshot() {
    return localStorage.getItem('interview_prep_edited_resumes') || JSON.stringify(getEditedResumeData());
}

function pushResumeHistory(label = '编辑简历', snapshot = getResumeStorageSnapshot()) {
    if (AppState.resumeHistory.isRestoring || !snapshot) return;
    const undoStack = AppState.resumeHistory.undo;
    if (undoStack.length && undoStack[undoStack.length - 1].snapshot === snapshot) return;
    undoStack.push({
        label,
        snapshot,
        at: new Date().toISOString()
    });
    if (undoStack.length > RESUME_HISTORY_LIMIT) undoStack.shift();
    AppState.resumeHistory.redo = [];
    renderResumeHistoryControls();
}

function renderResumeHistoryControls() {
    const undoBtn = document.getElementById('resume-undo-btn');
    const redoBtn = document.getElementById('resume-redo-btn');
    const status = document.getElementById('resume-history-status');
    if (undoBtn) undoBtn.disabled = AppState.resumeHistory.undo.length === 0;
    if (redoBtn) redoBtn.disabled = AppState.resumeHistory.redo.length === 0;
    if (status) {
        const undoCount = AppState.resumeHistory.undo.length;
        const redoCount = AppState.resumeHistory.redo.length;
        status.textContent = undoCount || redoCount ? `可撤销 ${undoCount} 步 / 可恢复 ${redoCount} 步` : '当前无历史操作';
    }
}

function restoreResumeHistoryEntry(entry, targetStack, label) {
    if (!entry) return;
    const current = getResumeStorageSnapshot();
    targetStack.push({
        label,
        snapshot: current,
        at: new Date().toISOString()
    });
    AppState.resumeHistory.isRestoring = true;
    localStorage.setItem('interview_prep_edited_resumes', entry.snapshot);
    markResumeSaved();
    AppState.resumeHistory.isRestoring = false;
    renderResume();
    renderResumeHistoryControls();
}

window.undoResumeEdit = function() {
    const entry = AppState.resumeHistory.undo.pop();
    if (!entry) return;
    restoreResumeHistoryEntry(entry, AppState.resumeHistory.redo, entry.label || '撤销');
    showNotification(`已撤销：${entry.label || '上一步编辑'}`);
};

window.redoResumeEdit = function() {
    const entry = AppState.resumeHistory.redo.pop();
    if (!entry) return;
    restoreResumeHistoryEntry(entry, AppState.resumeHistory.undo, entry.label || '恢复');
    showNotification(`已恢复：${entry.label || '上一步编辑'}`);
};

function getResumeVersions() {
    const saved = localStorage.getItem(RESUME_VERSION_STORAGE_KEY);
    if (!saved) return [];
    try {
        const parsed = JSON.parse(saved);
        return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
        console.error('Failed to load resume versions', err);
        return [];
    }
}

function saveResumeVersions(versions) {
    localStorage.setItem(RESUME_VERSION_STORAGE_KEY, JSON.stringify(versions.slice(0, RESUME_VERSION_LIMIT)));
}

function formatResumeVersionTime(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '未知时间';
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    const hh = String(date.getHours()).padStart(2, '0');
    const mi = String(date.getMinutes()).padStart(2, '0');
    return `${mm}-${dd} ${hh}:${mi}`;
}

function renderResumeVersions() {
    const list = document.getElementById('resume-version-list');
    if (!list) return;
    const versions = getResumeVersions();
    if (!versions.length) {
        list.innerHTML = `
            <div class="resume-version-empty">
                <i data-lucide="history"></i>
                <span>暂无保存版本</span>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    list.innerHTML = versions.map((item) => `
        <div class="resume-version-row">
            <div>
                <strong>${escapeHTML(item.title || '未命名版本')}</strong>
                <span>${escapeHTML(formatResumeVersionTime(item.createdAt))} · ${escapeHTML(item.profile || AppState.resumeProfile)}</span>
            </div>
            <div class="resume-version-actions">
                <button type="button" onclick="restoreResumeVersion('${item.id}')" title="恢复版本">
                    <i data-lucide="refresh-cw"></i>
                </button>
                <button type="button" onclick="deleteResumeVersion('${item.id}')" title="删除版本">
                    <i data-lucide="trash-2"></i>
                </button>
            </div>
        </div>
    `).join('');
    if (window.lucide) lucide.createIcons();
}

window.saveResumeVersionSnapshot = function() {
    const data = getEditedResumeData();
    const profile = data.profiles?.[AppState.resumeProfile];
    const titleBase = profile?.personalInfo?.targetJob || AppState.resumeProfile;
    const versions = getResumeVersions();
    const snapshot = getResumeStorageSnapshot();
    if (versions.length && versions[0].snapshot === snapshot) {
        showNotification('当前内容与最近保存版本一致，无需重复保存。');
        return;
    }
    versions.unshift({
        id: `rv_${Date.now()}`,
        title: `${titleBase} 版本`,
        profile: AppState.resumeProfile,
        createdAt: new Date().toISOString(),
        snapshot
    });
    saveResumeVersions(versions);
    renderResumeVersions();
    renderDataCenter();
    showNotification('已保存当前简历版本。');
};

window.restoreResumeVersion = function(versionId) {
    const version = getResumeVersions().find((item) => item.id === versionId);
    if (!version) return;
    if (!confirm(`确定恢复版本：${version.title || '未命名版本'}？当前简历会先进入撤销栈。`)) return;
    pushResumeHistory('恢复持久化版本');
    AppState.resumeHistory.isRestoring = true;
    localStorage.setItem('interview_prep_edited_resumes', version.snapshot);
    markResumeSaved();
    AppState.resumeHistory.isRestoring = false;
    renderResume();
    renderDataCenter();
    showNotification('已恢复保存版本。');
};

window.deleteResumeVersion = function(versionId) {
    const versions = getResumeVersions();
    const target = versions.find((item) => item.id === versionId);
    if (!target) return;
    if (!confirm(`确定删除版本：${target.title || '未命名版本'}？`)) return;
    saveResumeVersions(versions.filter((item) => item.id !== versionId));
    renderResumeVersions();
    renderDataCenter();
    showNotification('已删除保存版本。');
};

// 事件委托：失焦时保存对应 DOM 节点的修改到 LocalStorage 结构中
function markResumeSaved() {
    const timestamp = new Date().toISOString();
    localStorage.setItem('resume_last_saved_at', timestamp);
    return timestamp;
}

function formatResumeSavedAt(value) {
    if (!value) return '未保存';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '未保存';
    const hh = String(date.getHours()).padStart(2, '0');
    const mm = String(date.getMinutes()).padStart(2, '0');
    return `已保存 ${hh}:${mm}`;
}

function getVisibleResumeSections(profile) {
    const sectionOrder = ['education', 'workExperience', 'projects', 'skills', 'awards', 'selfEvaluation'];
    return sectionOrder
        .map((key) => {
            const section = profile.sections?.[key];
            if (!section || section.show === false) return null;
            return {
                key,
                id: `sec-${key}`,
                title: stripMarkdown(section.title || key),
                count: Array.isArray(section.items) ? section.items.length : (section.text ? 1 : 0)
            };
        })
        .filter(Boolean);
}

function renderResumeWorkspaceBar(profile) {
    if (!profile) return;
    const profileStatus = document.getElementById('resume-profile-status');
    const scoreStatus = document.getElementById('resume-score-status');
    const saveStatus = document.getElementById('resume-save-status');
    const jump = document.getElementById('resume-section-jump');
    const details = getResumeScoreDetails(AppState.resumeProfile);

    if (profileStatus) {
        profileStatus.textContent = profile.personalInfo?.targetJob || AppState.resumeProfile;
    }
    if (scoreStatus && details) {
        scoreStatus.textContent = `${details.total}%`;
        scoreStatus.className = details.total >= 85 ? 'status-good' : details.total >= 70 ? 'status-mid' : 'status-low';
    }
    if (saveStatus) {
        saveStatus.textContent = formatResumeSavedAt(localStorage.getItem('resume_last_saved_at'));
    }
    if (jump) {
        const sections = getVisibleResumeSections(profile);
        jump.innerHTML = sections.map((section) => `
            <button type="button" onclick="scrollResumeSection('${section.id}')">
                <span>${escapeHTML(section.title)}</span>
                <em>${section.count}</em>
            </button>
        `).join('');
    }
}

window.scrollResumeSection = function(sectionId) {
    const target = document.getElementById(sectionId);
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    target.classList.add('section-focus-pulse');
    setTimeout(() => target.classList.remove('section-focus-pulse'), 900);
};

function saveFieldFromDOM(el) {
    const type = el.dataset.type;
    const beforeSnapshot = getResumeStorageSnapshot();
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    
    const value = getCleanMarkdownText(el);
    
    if (type === 'basic') {
        const key = el.dataset.key;
        profile.personalInfo[key] = value;
    } else if (type === 'section-title') {
        const sectionKey = el.dataset.section;
        if (profile.sections[sectionKey]) {
            profile.sections[sectionKey].title = value;
        }
    } else if (type === 'item-field') {
        const sectionKey = el.dataset.section;
        const index = parseInt(el.dataset.index);
        const field = el.dataset.field;
        if (profile.sections[sectionKey] && profile.sections[sectionKey].items[index]) {
            profile.sections[sectionKey].items[index][field] = value;
        }
    } else if (type === 'bullet') {
        const sectionKey = el.dataset.section;
        const index = parseInt(el.dataset.index);
        const bIdx = parseInt(el.dataset.bulletIndex);
        if (profile.sections[sectionKey] && profile.sections[sectionKey].items[index] && profile.sections[sectionKey].items[index].highlights) {
            profile.sections[sectionKey].items[index].highlights[bIdx] = value;
        }
    } else if (type === 'self-eval') {
        if (profile.sections.selfEvaluation) {
            profile.sections.selfEvaluation.text = value;
        }
    }
    
    const nextSnapshot = JSON.stringify(data);
    if (nextSnapshot === beforeSnapshot) return;
    pushResumeHistory('编辑文字', beforeSnapshot);
    localStorage.setItem('interview_prep_edited_resumes', nextSnapshot);
    markResumeSaved();
    renderResumeWorkspaceBar(profile);
    updateResumeScore(AppState.resumeProfile);
    renderResumeWorkspaceBar(profile);
}

// 渲染简历到纸张 DOM
function renderResume() {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    
    const paper = document.getElementById('resume-paper-target');
    if (!paper) return;
    
    // 1. 设置颜色主题
    const themeColor = profile.themeColor || '#0d9488';
    document.documentElement.style.setProperty('--resume-accent', themeColor);
    
    // 更新颜色球高亮
    document.querySelectorAll('.theme-color-picker .color-circle').forEach(btn => {
        if (btn.getAttribute('data-color') === themeColor) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // 2. 设置行距排版 class
    const spacing = profile.spacing || 'normal';
    paper.className = 'resume-paper'; // 重置
    paper.classList.add(`spacing-${spacing}`);
    
    // 更新间距按钮高亮
    document.querySelectorAll('.spacing-btn').forEach(btn => {
        if (btn.getAttribute('data-spacing') === spacing) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    const spValDisp = document.getElementById('spacing-val-display');
    if (spValDisp) spValDisp.textContent = spacing === 'compact' ? '紧凑' : spacing === 'loose' ? '宽松' : '适中';
    
    // 3. 同步板块显示/隐藏复选框状态
    const avatarChk = document.getElementById('toggle-avatar-checkbox');
    if (avatarChk) avatarChk.checked = profile.personalInfo.showAvatar !== false;
    
    const secKeys = ['education', 'workExperience', 'projects', 'skills', 'awards', 'selfEvaluation'];
    secKeys.forEach(k => {
        const chk = document.getElementById(`toggle-sec-${k}`);
        if (chk && profile.sections[k]) {
            chk.checked = profile.sections[k].show !== false;
        }
    });
    
    // 4. 构建 HTML
    const info = profile.personalInfo;
    
    // 头像处理
    let avatarHTML = '';
    if (info.showAvatar !== false) {
        // 默认空照片时渲染占位图
        const avatarSrc = info.avatar || 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="133" viewBox="0 0 100 133" fill="none" stroke="%234b5563" stroke-width="2"><rect x="1" y="1" width="98" height="131" rx="4" fill="%23131a2e"/><circle cx="50" cy="50" r="22" fill="%231e293b"/><path d="M15 115 C 20 90, 80 90, 85 115 Z" fill="%231e293b"/></svg>';
        avatarHTML = `
            <div class="info-avatar-box" id="resume-avatar-container">
                <img src="${avatarSrc}" id="resume-avatar-img" alt="头像">
                <div class="avatar-hover-upload" onclick="triggerAvatarUpload()">
                    <i data-lucide="camera" style="width:16px;height:16px;"></i>
                    <span>更换照片</span>
                </div>
            </div>
        `;
    }
    
    // 头部信息
    let headerHTML = `
        <div class="resume-basic-info-block">
            <div class="info-fields-grid">
                <div class="info-field">
                    <span class="field-label">姓名：</span>
                    <span class="field-value editable" data-type="basic" data-key="name">${info.name}</span>
                </div>
                <div class="info-field">
                    <span class="field-label">年龄：</span>
                    <span class="field-value editable" data-type="basic" data-key="age">${info.age}</span>
                </div>
                <div class="info-field">
                    <span class="field-label">性别：</span>
                    <span class="field-value editable" data-type="basic" data-key="gender">${info.gender}</span>
                </div>
                <div class="info-field">
                    <span class="field-label">籍贯：</span>
                    <span class="field-value editable" data-type="basic" data-key="hometown">${info.hometown}</span>
                </div>
                <div class="info-field">
                    <span class="field-label">工作年限：</span>
                    <span class="field-value editable" data-type="basic" data-key="experience">${info.experience}</span>
                </div>
                <div class="info-field">
                    <span class="field-label">求职岗位：</span>
                    <span class="field-value editable" data-type="basic" data-key="targetJob">${info.targetJob}</span>
                </div>
                <div class="info-field">
                    <span class="field-label">目标薪资：</span>
                    <span class="field-value editable" data-type="basic" data-key="targetSalary">${info.targetSalary || '15K'}</span>
                </div>
                <div class="info-field">
                    <span class="field-label">联系电话：</span>
                    <span class="field-value editable" data-type="basic" data-key="phone">${info.phone}</span>
                </div>
                <div class="info-field">
                    <span class="field-label">电子邮箱：</span>
                    <span class="field-value editable" data-type="basic" data-key="email">${info.email}</span>
                </div>
            </div>
            ${avatarHTML}
        </div>
    `;
    
    // 板块辅助生成函数
    const getSecHeader = (key, title) => `
        <div class="resume-section-header-wrap" contenteditable="false">
            <h2 class="resume-section-title">
                <span class="editable" data-type="section-title" data-section="${key}">${title}</span>
            </h2>
        </div>
    `;
    
    const getBlockActions = (key, idx) => `
        <div class="block-actions-overlay" contenteditable="false">
            <button class="block-action-btn" onclick="moveResumeBlock('${key}', ${idx}, -1); event.stopPropagation();" title="上移">
                <i data-lucide="chevron-up" style="width:12px;height:12px;"></i>
            </button>
            <button class="block-action-btn" onclick="moveResumeBlock('${key}', ${idx}, 1); event.stopPropagation();" title="下移">
                <i data-lucide="chevron-down" style="width:12px;height:12px;"></i>
            </button>
            <button class="block-action-btn delete-btn" onclick="deleteResumeBlock('${key}', ${idx}); event.stopPropagation();" title="删除">
                <i data-lucide="trash-2" style="width:12px;height:12px;"></i>
            </button>
        </div>
    `;
    
    // 渲染教育经历
    let eduHTML = '';
    const eduSec = profile.sections.education;
    if (eduSec && eduSec.show !== false) {
        eduHTML += `<div class="resume-section" id="sec-education">`;
        eduHTML += getSecHeader('education', eduSec.title);
        eduSec.items.forEach((item, index) => {
            eduHTML += `
                <div class="resume-block-item">
                    ${getBlockActions('education', index)}
                    <div class="resume-project-header">
                        <span class="editable" data-type="item-field" data-section="education" data-index="${index}" data-field="school" style="font-size:1.05rem;font-weight:600;color:var(--text-primary);">${formatContent(item.school)}</span>
                        <span class="editable" data-type="item-field" data-section="education" data-index="${index}" data-field="period" style="font-size:0.9rem;color:var(--text-muted);">${formatContent(item.period)}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.88rem; color:var(--resume-accent, #0d9488); margin-bottom:6px; font-weight:600;">
                        <span class="editable" data-type="item-field" data-section="education" data-index="${index}" data-field="major">${formatContent(item.major)}</span>
                        <span class="editable" data-type="item-field" data-section="education" data-index="${index}" data-field="gpa">${formatContent(item.gpa)}</span>
                    </div>
                    <div class="editable" data-type="item-field" data-section="education" data-index="${index}" data-field="courses" style="font-size:0.88rem; color:var(--text-secondary); text-align:justify;">${formatContent(item.courses)}</div>
                </div>
            `;
        });
        eduHTML += `</div>`;
    }
    
    // 渲染工作经历
    let workHTML = '';
    const workSec = profile.sections.workExperience;
    if (workSec && workSec.show !== false) {
        workHTML += `<div class="resume-section" id="sec-workExperience">`;
        workHTML += getSecHeader('workExperience', workSec.title);
        workSec.items.forEach((item, index) => {
            let bulletsHTML = item.highlights.map((bullet, bIdx) => `
                <li class="resume-bullet-item">
                    <span class="editable" data-type="bullet" data-section="workExperience" data-index="${index}" data-bullet-index="${bIdx}">${formatContent(bullet)}</span>
                    <button class="ai-polish-btn" onclick="openAIRefineModal('workExperience', ${index}, ${bIdx}); event.stopPropagation();" contenteditable="false" title="AI 润色">✨ 润色</button>
                    <button class="bullet-delete-btn" onclick="deleteBullet('workExperience', ${index}, ${bIdx}); event.stopPropagation();" contenteditable="false" title="删除此条">×</button>
                </li>
            `).join('');
            
            workHTML += `
                <div class="resume-block-item">
                    ${getBlockActions('workExperience', index)}
                    <div class="resume-project-header">
                        <span class="editable" data-type="item-field" data-section="workExperience" data-index="${index}" data-field="company" style="font-size:1.05rem;font-weight:600;color:var(--text-primary);">${formatContent(item.company)}</span>
                        <span class="editable" data-type="item-field" data-section="workExperience" data-index="${index}" data-field="period" style="font-size:0.9rem;color:var(--text-muted);">${formatContent(item.period)}</span>
                    </div>
                    <div class="resume-project-role editable" data-type="item-field" data-section="workExperience" data-index="${index}" data-field="role">${formatContent(item.role)}</div>
                    <ul class="resume-bullets">
                        ${bulletsHTML}
                    </ul>
                    <button class="add-bullet-btn" onclick="addBullet('workExperience', ${index}); event.stopPropagation();" contenteditable="false"><i data-lucide="plus" style="width:12px;height:12px;"></i> 添加工作业绩要点</button>
                </div>
            `;
        });
        workHTML += `</div>`;
    }
    
    // 渲染项目经验
    let projHTML = '';
    const projSec = profile.sections.projects;
    if (projSec && projSec.show !== false) {
        projHTML += `<div class="resume-section" id="sec-projects">`;
        projHTML += getSecHeader('projects', projSec.title);
        projSec.items.forEach((item, index) => {
            let bulletsHTML = item.highlights.map((bullet, bIdx) => `
                <li class="resume-bullet-item">
                    <span class="editable" data-type="bullet" data-section="projects" data-index="${index}" data-bullet-index="${bIdx}">${formatContent(bullet)}</span>
                    <button class="ai-polish-btn" onclick="openAIRefineModal('projects', ${index}, ${bIdx}); event.stopPropagation();" contenteditable="false" title="AI 润色">✨ 润色</button>
                    <button class="bullet-delete-btn" onclick="deleteBullet('projects', ${index}, ${bIdx}); event.stopPropagation();" contenteditable="false" title="删除此条">×</button>
                </li>
            `).join('');
            
            projHTML += `
                <div class="resume-block-item">
                    ${getBlockActions('projects', index)}
                    <div class="resume-project-header">
                        <span class="editable" data-type="item-field" data-section="projects" data-index="${index}" data-field="name" style="font-size:1.05rem;font-weight:600;color:var(--text-primary);">${formatContent(item.name)}</span>
                        <span class="editable" data-type="item-field" data-section="projects" data-index="${index}" data-field="period" style="font-size:0.9rem;color:var(--text-muted);">${formatContent(item.period)}</span>
                    </div>
                    <div class="resume-project-role editable" data-type="item-field" data-section="projects" data-index="${index}" data-field="role">${formatContent(item.role)}</div>
                    <ul class="resume-bullets">
                        ${bulletsHTML}
                    </ul>
                    <button class="add-bullet-btn" onclick="addBullet('projects', ${index}); event.stopPropagation();" contenteditable="false"><i data-lucide="plus" style="width:12px;height:12px;"></i> 添加项目产出描述</button>
                </div>
            `;
        });
        projHTML += `</div>`;
    }
    
    // 渲染专业技能
    let skillsHTML = '';
    const skillsSec = profile.sections.skills;
    if (skillsSec && skillsSec.show !== false) {
        skillsHTML += `<div class="resume-section" id="sec-skills">`;
        skillsHTML += getSecHeader('skills', skillsSec.title);
        skillsSec.items.forEach((item, index) => {
            skillsHTML += `
                <div class="resume-block-item" style="margin-bottom: 6px; padding: 4px 8px;">
                    ${getBlockActions('skills', index)}
                    <strong class="editable" data-type="item-field" data-section="skills" data-index="${index}" data-field="category" style="color:var(--text-primary); font-weight:600;">${formatContent(item.category)}：</strong>
                    <span class="editable" data-type="item-field" data-section="skills" data-index="${index}" data-field="list">${formatContent(item.list)}</span>
                </div>
            `;
        });
        skillsHTML += `</div>`;
    }
    
    // 渲染荣誉奖项
    let awardsHTML = '';
    const awardsSec = profile.sections.awards;
    if (awardsSec && awardsSec.show !== false) {
        awardsHTML += `<div class="resume-section" id="sec-awards">`;
        awardsHTML += getSecHeader('awards', awardsSec.title);
        awardsSec.items.forEach((item, index) => {
            awardsHTML += `
                <div class="resume-block-item" style="display:flex; justify-content:space-between; margin-bottom: 6px; font-size:0.9rem;">
                    ${getBlockActions('awards', index)}
                    <span class="editable" data-type="item-field" data-section="awards" data-index="${index}" data-field="name" style="color:var(--text-primary); font-weight:500;">${formatContent(item.name)}</span>
                    <span class="editable" data-type="item-field" data-section="awards" data-index="${index}" data-field="time" style="color:var(--text-muted);">${formatContent(item.time)}</span>
                </div>
            `;
        });
        awardsHTML += `</div>`;
    }
    
    // 渲染自我评价
    let selfEvalHTML = '';
    const evalSec = profile.sections.selfEvaluation;
    if (evalSec && evalSec.show !== false) {
        selfEvalHTML += `<div class="resume-section" id="sec-selfEvaluation">`;
        selfEvalHTML += getSecHeader('selfEvaluation', evalSec.title);
        selfEvalHTML += `
            <div class="resume-block-item" style="text-align: justify;">
                <div class="editable" data-type="self-eval">${formatContent(evalSec.text)}</div>
            </div>
        `;
        selfEvalHTML += `</div>`;
    }
    
    // 合写 DOM
    paper.innerHTML = headerHTML + eduHTML + workHTML + projHTML + skillsHTML + awardsHTML + selfEvalHTML;
    
    // 5. 根据当前是否处于编辑模式，赋予/撤销 contenteditable 属性
    const isEditing = paper.classList.contains('editing-active');
    paper.querySelectorAll('.editable').forEach(el => {
        el.setAttribute('contenteditable', isEditing ? 'true' : 'false');
    });
    
    // 重新评分及 ATS 扫描
    updateResumeScore(AppState.resumeProfile);
    renderResumeHistoryControls();
    renderResumeVersions();
    
    // 渲染公式
    triggerMathRender(paper);
    
    // 重新生成图标
    if (window.lucide) lucide.createIcons();
}

/* ==========================================================================
   2.0 版商业级功能逻辑 (Score, ATS, AI Refiner)
   ========================================================================== */

const ATS_KEYWORDS = {
    unicorn: ['SAM', 'Spark', 'Flink', '无人机', 'Sedona', 'LoRA', 'RAG', 'Agent'],
    ai_llm: ['SAM 2', 'Transformer', 'LoRA', 'RAG', 'Agent', 'Embedding', 'vLLM', 'PyTorch'],
    rs_uav: ['无人机', '航测', 'RTK', 'SfM', 'DOM', 'CGCS2000', 'GDAL', 'OBB'],
    data_engineer: ['Spark', 'Flink', 'Kafka', 'Delta Lake', 'Sedona', 'PostGIS', '向量数据库', 'ETL']
};

function runATSCheck(profileKey) {
    const paper = document.getElementById('resume-paper-target');
    if (!paper) return;
    
    const text = paper.innerText || paper.textContent || '';
    const keywords = ATS_KEYWORDS[profileKey] || [];
    
    let matchedCount = 0;
    const badgeContainer = document.getElementById('ats-keywords-badge-container');
    if (!badgeContainer) return;
    badgeContainer.innerHTML = '';
    
    keywords.forEach(kw => {
        const regex = new RegExp(escapeRegExp(kw), 'i');
        const isMatched = regex.test(text);
        
        if (isMatched) matchedCount++;
        
        const badge = document.createElement('span');
        badge.className = `ats-badge ${isMatched ? 'active' : 'missing'}`;
        badge.innerHTML = isMatched 
            ? `<i data-lucide="check-circle" style="width:12px;height:12px;display:inline-block;vertical-align:middle;margin-right:2px;"></i>${kw}`
            : `<i data-lucide="x-circle" style="width:12px;height:12px;display:inline-block;vertical-align:middle;margin-right:2px;"></i>${kw}`;
        badgeContainer.appendChild(badge);
    });
    
    if (window.lucide) lucide.createIcons();
    
    return {
        total: keywords.length,
        matched: matchedCount,
        rate: keywords.length ? (matchedCount / keywords.length) : 0
    };
}

window.insertATSKeywords = function() {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    
    const paper = document.getElementById('resume-paper-target');
    if (!paper) return;
    
    const text = paper.innerText || paper.textContent || '';
    const keywords = ATS_KEYWORDS[AppState.resumeProfile] || [];
    
    const missing = keywords.filter(kw => {
        const regex = new RegExp(escapeRegExp(kw), 'i');
        return !regex.test(text);
    });
    
    if (missing.length === 0) {
        showNotification('所有 ATS 关键词已覆盖，无需添加！');
        return;
    }
    
    if (!profile.sections.selfEvaluation) {
        profile.sections.selfEvaluation = { show: true, title: "自我评价", text: "" };
    }
    
    const appendText = `（核心领域积累：${missing.join('、')}）`;
    profile.sections.selfEvaluation.text = (profile.sections.selfEvaluation.text || '') + appendText;
    
    localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
    renderResume();
    showNotification(`成功在“自我评价”中补充了 ${missing.length} 个缺失关键词！`);
};

function getResumeScoreDetails(profileKey) {
    const data = getEditedResumeData();
    const profile = data.profiles[profileKey];
    if (!profile) return null;
    
    // 1. 基本信息完整度
    const info = profile.personalInfo;
    const infoScore = (info.phone && info.phone.length > 5 && info.email && info.email.includes('@') ? 10 : 0) + 
                      (info.showAvatar !== false && info.avatar ? 10 : 0);
                      
    // 2. 文案内容丰富度
    let bulletCount = 0;
    if (profile.sections.workExperience && profile.sections.workExperience.show !== false) {
        profile.sections.workExperience.items.forEach(item => {
            if (item.highlights) bulletCount += item.highlights.length;
        });
    }
    if (profile.sections.projects && profile.sections.projects.show !== false) {
        profile.sections.projects.items.forEach(item => {
            if (item.highlights) bulletCount += item.highlights.length;
        });
    }
    const completenessScore = Math.min(20, bulletCount * 3.5); // 约6条拿满
    
    // 3. 量化指标检测
    let hasQuantified = false;
    const numRegex = /\d+(%|TB|GB|万|倍|小时|min|分钟|ops)/;
    if (profile.sections.workExperience && profile.sections.workExperience.show !== false) {
        profile.sections.workExperience.items.forEach(item => {
            if (item.highlights) {
                item.highlights.forEach(h => {
                    if (numRegex.test(h)) hasQuantified = true;
                });
            }
        });
    }
    if (profile.sections.projects && profile.sections.projects.show !== false) {
        profile.sections.projects.items.forEach(item => {
            if (item.highlights) {
                item.highlights.forEach(h => {
                    if (numRegex.test(h)) hasQuantified = true;
                });
            }
        });
    }
    const quantScore = hasQuantified ? 20 : 0;
    
    // 4. ATS 关键词检测
    const atsResult = runATSCheck(profileKey);
    const atsCoverage = atsResult ? atsResult.rate : 0;
    const atsScore = Math.round(atsCoverage * 40);
    
    const totalScore = Math.max(0, Math.min(100, Math.round(infoScore + completenessScore + quantScore + atsScore)));
    
    return {
        total: totalScore,
        info: Math.round(infoScore),
        completeness: Math.round(completenessScore),
        quant: Math.round(quantScore),
        ats: Math.round(atsScore),
        atsCoverage: atsCoverage,
        bulletCount: bulletCount,
        hasQuantified: hasQuantified,
        atsMatched: atsResult ? atsResult.matched : 0,
        atsTotal: atsResult ? atsResult.total : 0
    };
}

function updateResumeScore(profileKey) {
    const details = getResumeScoreDetails(profileKey);
    if (!details) return;
    
    const score = details.total;
    
    // 更新 DOM
    const scoreVal = document.getElementById('resume-score-value');
    if (scoreVal) scoreVal.textContent = score + '%';
    
    const scoreGrade = document.getElementById('resume-score-grade');
    const scoreDesc = document.getElementById('resume-score-desc');
    
    if (scoreGrade) {
        if (score >= 90) {
            scoreGrade.textContent = '准备度：完美';
            scoreGrade.style.color = 'var(--success)';
            if (scoreDesc) scoreDesc.textContent = '简历符合商业级要求，可以直接投递！';
        } else if (score >= 70) {
            scoreGrade.textContent = '准备度：良好';
            scoreGrade.style.color = 'var(--primary)';
            if (scoreDesc) scoreDesc.textContent = '简历质量良好，完善建议可得满分。';
        } else {
            scoreGrade.textContent = '准备度：亟待优化';
            scoreGrade.style.color = 'var(--error)';
            if (scoreDesc) scoreDesc.textContent = '简历内容单薄，请根据建议进行优化。';
        }
    }
    
    const suggestions = [];
    const data = getEditedResumeData();
    const profile = data.profiles[profileKey];
    
    if (details.info < 20) {
        if (profile.personalInfo.showAvatar === false || !profile.personalInfo.avatar) {
            suggestions.push({ icon: 'image', text: '建议上传求职证件照，更显职业感与商业规范。' });
        }
        if (!profile.personalInfo.phone || !profile.personalInfo.email) {
            suggestions.push({ icon: 'phone', text: '请补全电话和电子邮箱，便于HR取得联系。' });
        }
    }
    if (details.completeness < 20) {
        suggestions.push({ icon: 'file-text', text: `工作或项目要点偏少（当前${details.bulletCount}条），建议补充至 6 条以上。` });
    }
    if (details.quant === 0) {
        suggestions.push({ icon: 'trending-up', text: '描述中缺少量化业绩指标（如：效率提升30%），建议使用数据佐证。' });
    }
    if (details.atsCoverage < 0.7) {
        suggestions.push({ icon: 'target', text: `ATS 行业核心词覆盖度偏低（当前${Math.round(details.atsCoverage * 100)}%），建议智能补齐。` });
    }
    
    const suggList = document.getElementById('resume-suggestions-list');
    if (suggList) {
        suggList.innerHTML = '';
        if (suggestions.length === 0) {
            suggList.innerHTML = `<li class="sugg-item success"><i data-lucide="check-circle" style="color:var(--success)"></i> 暂无优化建议，您的简历非常专业！</li>`;
        } else {
            suggestions.forEach(s => {
                const li = document.createElement('li');
                li.className = 'sugg-item';
                li.innerHTML = `<i data-lucide="${s.icon}"></i> <span>${s.text}</span>`;
                suggList.appendChild(li);
            });
        }
    }
    
    const scoreWrapper = document.querySelector('.score-circle-wrapper');
    if (scoreWrapper) {
        scoreWrapper.style.setProperty('--score-percent', score + '%');
    }
    
    if (window.lucide) lucide.createIcons();
}

window.openATSReportModal = function() {
    const details = getResumeScoreDetails(AppState.resumeProfile);
    if (!details) return;
    
    const modal = document.getElementById('ats-report-modal');
    const body = document.getElementById('ats-report-body');
    if (!modal || !body) return;
    
    const infoPct = (details.info / 20) * 100;
    const compPct = (details.completeness / 20) * 100;
    const quantPct = (details.quant / 20) * 100;
    const atsPct = (details.ats / 40) * 100;
    
    const getBar = (title, score, max, pct, icon, desc, color) => `
        <div style="margin-bottom: 18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                <span style="font-size:0.9rem; font-weight:600; color:var(--text-primary); display:flex; align-items:center; gap:6px;">
                    <i data-lucide="${icon}" style="width:16px; height:16px; color:${color};"></i>
                    ${title}
                </span>
                <span style="font-size:0.9rem; font-weight:700; color:${color}">${score} / ${max} 分</span>
            </div>
            <div style="height: 8px; background: var(--bg-deep); border-radius: 4px; overflow: hidden; position: relative;">
                <div style="width: ${pct}%; height: 100%; background: ${color}; border-radius: 4px; transition: width 0.6s ease;"></div>
            </div>
            <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; line-height: 1.3;">${desc}</p>
        </div>
    `;
    
    const infoBar = getBar("基本信息完整度", details.info, 20, infoPct, "user", "包含联系电话、电子邮箱以及证件照片的完整性，是获取面试邀请的基准门槛。", "var(--primary)");
    const compBar = getBar("文案内容丰富度", details.completeness, 20, compPct, "file-text", `当前简历共包含 ${details.bulletCount} 条经历描述要点。条目丰富有助于展现您的项目经验深度。`, "#8b5cf6");
    const quantBar = getBar("STAR 量化指标率", details.quant, 20, quantPct, "trending-up", details.hasQuantified ? "已检测到数字与单位（如 %、TB、万、倍），表明您的简历具备良好的数据导向和业务结果意识。" : "未检测到任何数据指标（如效率提升30%、处理TB级别数据）。建议使用量化指标，更显专业！", "var(--secondary)");
    const atsBar = getBar("ATS 行业词契合度", details.ats, 40, atsPct, "target", `当前匹配了 ${details.atsMatched} / ${details.atsTotal} 个核心岗位关键词。匹配度越高，越容易通过企业筛选系统。`, "var(--success)");
    
    let recommendations = '';
    const paper = document.getElementById('resume-paper-target');
    const textContent = paper ? (paper.innerText || paper.textContent || '') : '';
    
    if (details.info < 20) {
        recommendations += `
            <div style="display:flex; gap:10px; margin-bottom:10px; font-size:0.85rem; color:var(--text-secondary);">
                <i data-lucide="alert-circle" style="color:var(--primary); flex-shrink:0; width:16px; height:16px;"></i>
                <span>补齐姓名、电话、邮箱等字段，并在右侧面板上传求职证件照片。</span>
            </div>
        `;
    }
    if (details.completeness < 20) {
        recommendations += `
            <div style="display:flex; gap:10px; margin-bottom:10px; font-size:0.85rem; color:var(--text-secondary);">
                <i data-lucide="alert-circle" style="color:#8b5cf6; flex-shrink:0; width:16px; height:16px;"></i>
                <span>为工作经历或项目经历补充更多技术细节和工作结果描述，保证每个大块至少 3 条 bullet points。</span>
            </div>
        `;
    }
    if (details.quant === 0) {
        recommendations += `
            <div style="display:flex; gap:10px; margin-bottom:10px; font-size:0.85rem; color:var(--text-secondary);">
                <i data-lucide="alert-circle" style="color:var(--secondary); flex-shrink:0; width:16px; height:16px;"></i>
                <span>在简历编辑器中点击“✨ 润色”按钮，采纳 AI 给出带有百分比（%）和处理量级（TB）的 STAR 量化版本。</span>
            </div>
        `;
    }
    
    const missingKeywords = (ATS_KEYWORDS[AppState.resumeProfile] || []).filter(kw => !new RegExp(escapeRegExp(kw), 'i').test(textContent));
    if (missingKeywords.length > 0) {
        recommendations += `
            <div style="display:flex; gap:10px; margin-bottom:10px; font-size:0.85rem; color:var(--text-secondary);">
                <i data-lucide="alert-circle" style="color:var(--success); flex-shrink:0; width:16px; height:16px;"></i>
                <span>点击下方的“一键智能修复优化”，系统会自动将缺少的关键技术词（如 ${missingKeywords.join('、')}）嵌入至合适位置。</span>
            </div>
        `;
    }
    if (!recommendations) {
        recommendations = `
            <div style="display:flex; gap:10px; font-size:0.85rem; color:var(--success); align-items:center;">
                <i data-lucide="check-circle-2" style="width:18px; height:18px; color:var(--success);"></i>
                <span>您的简历各维度表现极佳，无明显弱项！可直接进行打印投递。</span>
            </div>
        `;
    }
    
    body.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; padding-bottom:16px; border-bottom:1px solid var(--card-border); flex-wrap:wrap; gap:15px;">
            <div>
                <div style="font-size:0.85rem; color:var(--text-muted); font-weight:600; text-transform:uppercase;">简历健康综合得分</div>
                <div style="font-family:'Outfit'; font-size:3rem; font-weight:800; color:var(--primary); line-height:1;">${details.total}<span style="font-size:1.2rem; font-weight:500; color:var(--text-muted);">/100分</span></div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.85rem; color:var(--text-muted); font-weight:600;">建议诊断等级</div>
                <span class="badge-tag" style="background:${details.total >= 90 ? 'var(--success-glow)' : details.total >= 70 ? 'var(--primary-glow)' : 'rgba(239, 68, 68, 0.08)'}; color:${details.total >= 90 ? 'var(--success)' : details.total >= 70 ? 'var(--primary)' : 'var(--error)'}; font-size:0.95rem; padding:6px 16px; border-radius:30px; font-weight:700; display:inline-block; margin-top:5px;">
                    ${details.total >= 90 ? '🚀 商业高精推荐' : details.total >= 70 ? '🎯 良好通过标准' : '⚠️ 急需重构调优'}
                </span>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 24px;">
            <div class="glass-card" style="padding: 20px; background:var(--bg-deep); border-color:var(--card-border);">
                <h4 style="font-family:'Outfit'; font-weight:700; margin-bottom:16px; font-size:1rem; color:var(--text-primary); display:flex; align-items:center; gap:6px;">
                    <i data-lucide="trending-up" style="color:var(--primary);"></i> 多维度指标雷达剖析
                </h4>
                ${infoBar}
                ${compBar}
                ${quantBar}
                ${atsBar}
            </div>
        </div>
        
        <div class="glass-card" style="padding: 20px; background: var(--primary-glow); border-color: var(--primary-border);">
            <h4 style="font-family:'Outfit'; font-weight:700; margin-bottom:12px; font-size:1rem; color:var(--text-primary); display:flex; align-items:center; gap:6px;">
                <i data-lucide="compass" style="color:var(--secondary);"></i> ATS 自适应优化行动清单
            </h4>
            <div style="display:flex; flex-direction:column; gap:6px;">
                ${recommendations}
            </div>
            
            <div style="display:flex; gap:12px; margin-top:20px; justify-content: flex-end;">
                <button class="btn btn-secondary" onclick="closeATSReportModal()" style="font-size:0.85rem; padding: 8px 16px;">关闭报告</button>
                <button class="btn btn-primary" onclick="optimizeResumeText(); closeATSReportModal();" style="font-size:0.85rem; padding: 8px 16px; font-weight:600;">
                    <i data-lucide="zap"></i> 一键智能修复优化
                </button>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    modal.classList.add('active');
    
    if (window.lucide) lucide.createIcons();
};

window.closeATSReportModal = function() {
    const modal = document.getElementById('ats-report-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
};

window.optimizeResumeText = function() {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    pushResumeHistory('一键 ATS 优化');
    
    let optimizedCount = 0;
    let quantCount = 0;
    
    const templates = [
        {
            search: /mIoU.*提升/i,
            replace: "在自建地物数据集上使用 LoRA 进行高效微调，将多光谱地物分割精度 mIoU 从原始的 68% 提升至 **89.5%**，解译效率提高 **4.5倍**。"
        },
        {
            search: /处理速度比传统管线/i,
            replace: "利用 Apache Spark 配合 Sedona 空间计算框架，实现了超大正射影像（DOM）的分布式重采样与空间重投影，处理速度比传统单机管线提升 **20倍以上**，日均流式吞吐量超 **10TB**。"
        },
        {
            search: /入库吞吐量突破/i,
            replace: "基于 Flink 搭建流式 NDVI 地物异变滑窗分析通道，在 Flink 中自定义 Async I/O 写入 Milvus 向量集群，向量化入库吞吐量突破 **50,000 ops/sec**，数据处理延迟降低 **92%**。"
        },
        {
            search: /召回率.*提升/i,
            replace: "基于 Qdrant 向量数据库（HNSW 索引）搭建 RAG 双阶段检索管线，引入 BGE-Reranker 二次重排与滑动窗口分块，使多轮会话检索召回率（Recall@5）提升 **32%**，检索延迟缩短至 **15ms**。"
        },
        {
            search: /自主增长|持久化存储/i,
            replace: "基于 Nous Hermes 智能体框架，利用 Llama 3.1-Hermes 3 执行多步函数调用，构建自进化 Skill 模块，实现对复杂空间解译算子的自适应自主规划，算子复用率达 **100%**。"
        },
        {
            search: /旋转框.*检测|目标检测/i,
            replace: "引入 YOLO-OBB 旋转框目标检测器解决倾斜密集地物提取难题，将野外三维控制点配准（CGCS2000坐标系）精度控制在 **3cm 以内**，令无人机全自主目标检测的准确度直接提升 **12.5%**。"
        },
        {
            search: /在复杂地物分割精度上达到/i,
            replace: "在复杂地物分割精度上达到行业领先，引入前沿 Segment Anything Model (SAM 2) 算法与 LoRA 旁路微调机制，使多光谱地物分割精度 mIoU 大幅提升至 **89.5%**。"
        },
        {
            search: /完成50余次野外测绘保障/i,
            replace: "采用 DJI M300 RTK 执行高分辨率航线规划，配合 GCP 控制点使三维重建平面定位精度控制在 **3cm 以内**，完成 50 余次野外测绘保障。"
        }
    ];

    // 1. Optimize highlights in workExperience
    if (profile.sections.workExperience && profile.sections.workExperience.items) {
        profile.sections.workExperience.items.forEach(item => {
            if (item.highlights) {
                item.highlights = item.highlights.map(hl => {
                    let matched = false;
                    for (let t of templates) {
                        if (t.search.test(hl) && !hl.includes("89.5%") && !hl.includes("20倍") && !hl.includes("50,000")) {
                            hl = t.replace;
                            matched = true;
                            optimizedCount++;
                            break;
                        }
                    }
                    if (!matched && !/\d+(%|TB|GB|万|倍|小时|min|ops)/.test(hl)) {
                        if (hl.includes("架构设计")) {
                            hl += "，令系统吞吐量提升 **45%**，平均延迟降低 **30%**。";
                            quantCount++;
                        } else if (hl.includes("数据团队")) {
                            hl += "，日均新增数据吞吐量超 **10TB**，ETL 速度提升 **20倍**。";
                            quantCount++;
                        }
                    }
                    return hl;
                });
            }
        });
    }

    // 2. Optimize highlights in projects
    if (profile.sections.projects && profile.sections.projects.items) {
        profile.sections.projects.items.forEach(item => {
            if (item.highlights) {
                item.highlights = item.highlights.map(hl => {
                    let matched = false;
                    for (let t of templates) {
                        if (t.search.test(hl) && !hl.includes("89.5%") && !hl.includes("20倍") && !hl.includes("50,000")) {
                            hl = t.replace;
                            matched = true;
                            optimizedCount++;
                            break;
                        }
                    }
                    if (!matched && !/\d+(%|TB|GB|万|倍|小时|min|ops)/.test(hl)) {
                        if (hl.includes("消除物理干扰点")) {
                            hl += "，误报率降低 **28%**，分类精度达到 **94.2%**。";
                            quantCount++;
                        } else if (hl.includes("多模态 Embedding")) {
                            hl += "，索引构建耗时减少 **40%**，多光谱特征召回率提升 **32%**。";
                            quantCount++;
                        } else if (hl.includes("轨迹数据超")) {
                            hl += " **10TB**，小文件 IO 读取性能提高 **15倍**。";
                            quantCount++;
                        }
                    }
                    return hl;
                });
            }
        });
    }

    // 3. Scan for missing keywords and inject into skills or selfEvaluation
    const currentText = JSON.stringify(profile).toLowerCase();
    const keywords = ATS_KEYWORDS[AppState.resumeProfile] || [];
    const missing = keywords.filter(kw => !currentText.includes(kw.toLowerCase()));
    
    if (missing.length > 0) {
        if (profile.sections.skills && profile.sections.skills.items) {
            missing.forEach(kw => {
                let categoryName = "";
                if (['SAM', 'SAM 2', 'YOLO', 'OBB', 'YOLO-OBB'].includes(kw)) {
                    categoryName = "计算机视觉与遥感";
                } else if (['Spark', 'Flink', 'Kafka', 'Sedona', 'PostGIS', 'Delta Lake'].includes(kw)) {
                    categoryName = "数据工程与空间计算";
                } else if (['LoRA', 'RAG', 'Agent', 'Transformer', 'vLLM'].includes(kw)) {
                    categoryName = "大模型与智能体";
                } else if (['无人机', '航测', 'RTK', 'SfM'].includes(kw)) {
                    categoryName = "无人机测绘";
                }
                
                if (categoryName) {
                    const skillItem = profile.sections.skills.items.find(s => s.category === categoryName);
                    if (skillItem) {
                        if (!skillItem.list.toLowerCase().includes(kw.toLowerCase())) {
                            skillItem.list += `、${kw}`;
                            optimizedCount++;
                        }
                    }
                }
            });
        }
        
        const finalCheckText = JSON.stringify(profile).toLowerCase();
        const finalMissing = keywords.filter(kw => !finalCheckText.includes(kw.toLowerCase()));
        if (finalMissing.length > 0) {
            if (profile.sections.selfEvaluation) {
                profile.sections.selfEvaluation.text += `（已在商业项目中实践了 ${finalMissing.join('、')} 等关键技术栈，实现生产级降本增效。）`;
                optimizedCount++;
            }
        }
    }

    localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
    markResumeSaved();
    renderResume();
    
    showNotification(`智能自适应优化完成！共优化文案 ${optimizedCount} 处，自动 STAR 业绩量化 ${quantCount} 处。`);
};

window.exportResumeJSON = function() {
    const data = getEditedResumeData();
    const blob = new Blob([JSON.stringify(data, null, 4)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `备战中心简历配置备份_${AppState.resumeProfile}_${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showNotification('简历配置文件已成功下载备份！');
};

window.triggerJSONUpload = function() {
    const fileInput = document.getElementById('resume-json-file');
    if (fileInput) fileInput.click();
};

window.importResumeJSON = function(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const parsed = JSON.parse(e.target.result);
            if (parsed.profiles && parsed.profiles.unicorn && parsed.profiles.unicorn.sections) {
                try {
                    pushResumeHistory('导入简历配置');
                    localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(parsed));
                    localStorage.setItem('resume_forced_sync_version', 'v3.0_ai_rs_resume');
                    markResumeSaved();
                    showNotification('文件导入成功，正在刷新页面...');
                    setTimeout(() => {
                        location.reload();
                    }, 500);
                } catch (storageErr) {
                    alert('导入失败：数据超出浏览器本地存储限制(5MB)。\n可能是因为图片Base64数据过大，请尝试压缩或更换照片！');
                }
            } else {
                alert('无效的配置文件格式，导入失败！');
            }
        } catch (err) {
            console.error(err);
            alert('文件解析失败，请检查文件格式是否正确');
        }
    };
    reader.readAsText(file);
    event.target.value = '';
};

function matchKeyword(userAnswer, keyPoint) {
    const cleanAnswer = userAnswer.toLowerCase();
    const kp = keyPoint.toLowerCase().trim();
    
    const subTerms = kp.split(/[\s,，\/\\与和对对偶vs\.]+/).filter(t => t.length > 1 || /^[a-zA-Z0-9\u4e00-\u9fa5]$/.test(t));
    if (subTerms.length === 0) return cleanAnswer.includes(kp);
    
    let hitCount = 0;
    subTerms.forEach(term => {
        if (cleanAnswer.includes(term)) {
            hitCount++;
        }
    });
    
    return (hitCount >= Math.ceil(subTerms.length / 2)) || cleanAnswer.includes(kp);
}

window.evaluateQuizAnswer = function() {
    const list = AppState.filteredQuizList;
    if (list.length === 0) return;
    
    const item = list[AppState.currentQuizIndex];
    const userAnswer = (document.getElementById('quiz-user-answer').value || '').trim();
    
    if (!userAnswer) {
        alert('请先在输入框中填写您的答案提纲或脑暴点，以便 AI 评测进行分析。');
        return;
    }
    
    const keyPointsStr = item.key_points || '';
    const keyPoints = keyPointsStr.split(/[,，]/).map(k => k.trim()).filter(k => k.length > 0);
    
    let hitCount = 0;
    const results = keyPoints.map(kp => {
        const isHit = matchKeyword(userAnswer, kp);
        if (isHit) hitCount++;
        return { keyPoint: kp, isHit: isHit };
    });
    
    let score = keyPoints.length > 0 ? Math.round((hitCount / keyPoints.length) * 100) : 0;
    
    if (userAnswer.length < 15 && score > 30) {
        score = 20; 
    }
    
    AppState.stats.quizScores[item.id] = score;
    saveProgress();
    
    const scorePanel = document.getElementById('quiz-ai-score-panel');
    if (scorePanel) {
        scorePanel.style.display = 'block';
        
        const hitBadges = results.map(r => `
            <span class="ats-badge ${r.isHit ? 'active' : 'missing'}" style="margin: 4px; display: inline-flex; align-items: center; font-size: 0.8rem; padding: 4px 10px; border-radius: 12px;">
                <i data-lucide="${r.isHit ? 'check' : 'x'}" style="width:14px; height:14px; margin-right:4px;"></i>
                ${r.keyPoint}
            </span>
        `).join('');
        
        let feedbackMsg = '';
        const missingPoints = results.filter(r => !r.isHit).map(r => `“${r.keyPoint}”`).join('、');
        
        if (score >= 80) {
            feedbackMsg = `🎉 <strong>非常优秀！</strong>您的回答结构完整，逻辑清晰，准确覆盖了几乎所有核心考点。对技术的底层细节有很好的把控，建议参考下方面试范式进一步规范学术用语。`;
        } else if (score >= 50) {
            feedbackMsg = `👍 <strong>表现良好。</strong>您答出了部分核心概念，但对 ${missingPoints || '部分细节'} 的论述还不够完整。面试中建议补充这些维度的对比和背景说明，以表现您的深度。`;
        } else {
            feedbackMsg = `⚠️ <strong>仍需提升。</strong>您的回答相对精简，遗漏了核心考察项：${missingPoints || '关键概念'}。建议仔细研读下方的高分回答框架及避坑指南，进行针对性补强。`;
        }
        
        const scoreColor = score >= 80 ? 'var(--success)' : score >= 50 ? 'var(--primary)' : 'var(--error)';
        
        scorePanel.innerHTML = `
            <div style="display: flex; gap: 20px; align-items: center; flex-wrap: wrap;">
                <div class="score-circle-wrapper" style="--score-percent: ${score}%; width: 90px; height: 90px;">
                    <div class="score-circle-inner" style="width: 76px; height: 76px; background: var(--card-bg) !important;">
                        <span style="font-family: 'Outfit'; font-weight: 800; font-size: 1.5rem; color: ${scoreColor};">${score}%</span>
                    </div>
                </div>
                <div style="flex: 1; min-width: 250px;">
                    <h3 style="font-family: 'Outfit'; font-weight: 700; font-size: 1.1rem; margin-bottom: 6px; color: ${scoreColor}; display: flex; align-items: center; gap: 6px;">
                        <i data-lucide="sparkles"></i> AI 智能评测得分：${score} 分
                    </h3>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.4; margin-bottom: 12px;">
                        ${feedbackMsg}
                    </p>
                </div>
            </div>
            
            <div style="margin-top: 16px; border-top: 1px dashed var(--card-border); padding-top: 12px;">
                <div style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); margin-bottom: 8px;">🔍 核心关键点检测情况：</div>
                <div style="display: flex; flex-wrap: wrap;">
                    ${hitBadges}
                </div>
            </div>
        `;
        
        if (window.lucide) lucide.createIcons();
    }
    
    revealQuizAnswer();
    
    if (scorePanel) {
        scorePanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    showNotification(`AI 评测完成！得分: ${score}%`);
};

function generateAIPolish(text) {
    const hasSam = /sam|segment|分割/i.test(text);
    const hasBigData = /spark|flink|lake|数据湖|数据仓|ETL/i.test(text);
    const hasUav = /无人机|航测|测绘|飞行/i.test(text);
    const hasLLM = /LLM|大模型|RAG|Agent|智能体|多模态/i.test(text);
    const hasYolo = /yolo|obb|检测|提取/i.test(text);
    
    let star = "";
    let quantum = "";
    
    if (hasSam) {
        star = "【STAR法则学术风】**情境**：面对异构高分辨率遥感地物分割多目标、高噪声问题，**行动**：引入前沿Segment Anything Model (SAM 2) 大模型并进行通道修改，融合红边/近红外特征设计LoRA权重微调算子；**结果**：最终令水体、林地分类精度提升至89.5%（mIoU），泛化误差缩减35%。";
        quantum = "【高量化业绩风】基于SAM 2模型对5通道多光谱图像进行分割管线重构，设计自适应特征匹配提取机制，使图像地物分割mIoU从68%大幅度拔升至 **89.5%**，解译效率提速 **4.5倍**，支持了百万量级图斑的日均流式处理。";
    } else if (hasBigData) {
        star = "【STAR法则学术风】**情境**：原GDAL单机解译管线在日增10TB+影像的地理处理上面临严重的I/O和计算速度瓶颈，**行动**：依托Apache Spark与Apache Sedona (GeoSpark) 搭建高并发空间数据湖与流处理算子，优化小文件合并及瓦片切片分区；**结果**：成功将海量DOM重投影及重采样计算耗时从18小时缩短至42分钟。";
        quantum = "【高量化业绩风】使用Flink与Spark重构大规模矢量/栅格ETL管线，通过实现自定义Async I/O与Milvus向量集群直连，数据写入吞吐量突破 **50,000 ops/sec**，流式滑窗NDVI异常分析耗时降低 **92%**。";
    } else if (hasLLM) {
        star = "【STAR法则学术风】**情境**：企业多模态文档及地理图像检索精度偏低，且推理决策存在明显幻觉，**行动**：搭建基于Qdrant/Milvus的RAG多路召回（HNSW索引）系统，结合Nous Hermes架构设计自适应Skill自进化Agent；**结果**：将多轮会话检索的召回率（Recall@5）提升32%，成功实现Agent对复杂空间解译算子的自主规划调用。";
        quantum = "【高量化业绩风】主导多模态知识库及自进化Agent上线，引入BGE-Reranker对多路检索进行二次排序，使知识回答准确度提升 **32%**，同时在Skill库内实现 **100%** 原生算子工具的自动沉淀与自适应规划调用。";
    } else if (hasUav || hasYolo) {
        star = "【STAR法则学术风】**情境**：复杂测绘野外场景对高精度地理定位及微小目标检测提取要求严苛，**行动**：采用DJI M300 RTK完成多光谱外业航线设计，基于Pix4D做空三精密平差解算，同时引入YOLOv5-OBB旋转框检测器以增强倾斜姿态目标的定位；**结果**：实现平面定位精度控制在3cm内，港口与机场目标提取精度达94.2%。";
        quantum = "【高量化业绩风】基于YOLOv5-OBB与航测平差流程进行技术重构，将野外三维控制点配准（CGCS2000坐标系）精度控制在 **3cm 以内**，令无人机全自主目标检测的准确度直接提升 **12.5%**。";
    } else {
        const words = text.replace(/[\s\d\*\+\-\#\%\（\）\，\。\；\：]+/g, '').substring(0, 15);
        star = `【STAR法则学术风】**情境**：针对“${words}”业务场景下的复杂指标瓶颈与稳定性隐隐患，**行动**：通过主导设计全新优化机制与自适应参数调优策略，优化链路处理性能并加强算法抗噪能力；**结果**：有效提升业务指标表现，显著降低异常频次并增强系统的健壮度。`;
        quantum = `【高量化业绩风】对“${words}”相关核心功能进行重度算法级重构，优化计算复杂度与内存消耗，令该模块整体运行吞吐量较前代版本提升 **45%** 以上，计算延迟缩短 **30%**，大幅节省硬件算力成本。`;
    }
    
    return { star, quantum };
}

AppState.currentRefineTarget = {
    sectionKey: null,
    itemIdx: null,
    bulletIdx: null
};

window.openAIRefineModal = function(sectionKey, itemIdx, bulletIdx) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    
    const item = profile.sections[sectionKey].items[itemIdx];
    if (!item) return;
    
    const originalText = item.highlights[bulletIdx];
    if (!originalText) return;
    
    AppState.currentRefineTarget = { sectionKey, itemIdx, bulletIdx };
    
    document.getElementById('refine-original-text').textContent = originalText;
    
    const polished = generateAIPolish(originalText);
    
    document.getElementById('refine-option-1-text').innerHTML = polished.star;
    document.getElementById('refine-option-2-text').innerHTML = polished.quantum;
    
    const modal = document.getElementById('ai-polish-modal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
    }
};

window.closeAIRefineModal = function() {
    const modal = document.getElementById('ai-polish-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
};

window.selectRefineOption = function(optionNum) {
    const textEl = document.getElementById(`refine-option-${optionNum}-text`);
    if (!textEl) return;
    
    let refinedText = textEl.textContent.trim();
    refinedText = refinedText.replace(/^【[^】]+】/, '');
    
    const { sectionKey, itemIdx, bulletIdx } = AppState.currentRefineTarget;
    if (!sectionKey) return;
    
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (profile && profile.sections[sectionKey] && profile.sections[sectionKey].items[itemIdx]) {
        pushResumeHistory('采纳 AI 润色');
        profile.sections[sectionKey].items[itemIdx].highlights[bulletIdx] = refinedText;
        localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
        markResumeSaved();
        
        closeAIRefineModal();
        renderResume();
        showNotification('已采纳 AI 润色版本并同步到简历！');
    }
};

// 切换编辑模式
function toggleResumeEditMode() {
    const paper = document.getElementById('resume-paper-target');
    const btn = document.getElementById('resume-edit-toggle-btn');
    const indicator = document.getElementById('resume-save-indicator');
    if (!paper || !btn || !indicator) return;
    
    if (paper.classList.contains('editing-active')) {
        // 锁定编辑并保存
        paper.classList.remove('editing-active');
        paper.querySelectorAll('.editable').forEach(el => {
            el.setAttribute('contenteditable', 'false');
        });
        
        btn.innerHTML = `<i data-lucide="edit"></i> 进入编辑模式`;
        indicator.innerHTML = `<i data-lucide="lock" style="width:14px;"></i> 内容已锁定`;
        indicator.style.color = 'var(--text-muted)';
        markResumeSaved();
        renderResumeWorkspaceBar(getActiveResumeProfile());
        
        showNotification('已保存简历修改，锁定内容！');
    } else {
        // 进入编辑模式
        paper.classList.add('editing-active');
        paper.querySelectorAll('.editable').forEach(el => {
            el.setAttribute('contenteditable', 'true');
        });
        
        btn.innerHTML = `<i data-lucide="save"></i> 保存并锁定`;
        indicator.innerHTML = `<i data-lucide="edit-3" style="width:14px; color:var(--warning);"></i> 正在编辑...`;
        indicator.style.color = 'var(--warning)';
        
        showNotification('已进入编辑模式，可直接点击简历上任意文字或操作按钮进行修改！');
    }
    
    if (window.lucide) lucide.createIcons();
}

// ==========================================================================
// 简历控制栏高级操作函数 (Exposed Globally)
// ==========================================================================

// 1. 改变简历主题颜色
window.changeThemeColor = function(color) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (profile) {
        pushResumeHistory('切换主题色');
        profile.themeColor = color;
        localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
        markResumeSaved();
        renderResume();
        showNotification('已成功切换主题配色！');
    }
};

// 2. 显示/隐藏证件照
window.toggleAvatarVisibility = function(visible) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (profile) {
        pushResumeHistory(visible ? '显示证件照' : '隐藏证件照');
        profile.personalInfo.showAvatar = visible;
        localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
        markResumeSaved();
        renderResume();
    }
};

// 3. 触发选择文件进行照片上传
window.triggerAvatarUpload = function() {
    const fileInput = document.getElementById('avatar-file-input');
    if (fileInput) fileInput.click();
};

// 4. 读取照片并转为 base64 存储
window.handleAvatarUpload = function(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (file.size > 2 * 1024 * 1024) {
        alert('照片文件过大，请选择 2MB 以下的文件。');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const base64 = e.target.result;
        
        const data = getEditedResumeData();
        const profile = data.profiles[AppState.resumeProfile];
        if (profile) {
            pushResumeHistory('上传证件照');
            profile.personalInfo.avatar = base64;
            localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
            markResumeSaved();
            renderResume();
            showNotification('照片上传成功！');
        }
    };
    reader.readAsDataURL(file);
};

// 5. 版面间距调节 (compact / normal / loose)
window.adjustResumeSpacing = function(level) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (profile) {
        pushResumeHistory('调整版面间距');
        profile.spacing = level;
        localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
        markResumeSaved();
        renderResume();
    }
};

// 6. 板块整体显示/隐藏开关
window.toggleSection = function(sectionKey, show) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (profile && profile.sections[sectionKey]) {
        pushResumeHistory(show ? '显示简历板块' : '隐藏简历板块');
        profile.sections[sectionKey].show = show;
        localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
        markResumeSaved();
        renderResume();
    }
};

// 7. 新增条目 block
window.addResumeBlock = function(sectionKey) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    
    const section = profile.sections[sectionKey];
    if (!section) return;
    
    const templates = {
        education: {
            period: "2018.09 - 2022.07",
            school: "请填写大学/院校名称",
            major: "专业名称 (学历)",
            gpa: "GPA 3.5/4.0",
            courses: "主修课程及相关描述"
        },
        workExperience: {
            period: "2022.07 - 2023.08",
            company: "请填写公司/工作单位名称",
            role: "岗位职称",
            highlights: ["在此新增您具体负责的工作要点...", "第二条工作产出细节描述"]
        },
        projects: {
            name: "请填写项目名称",
            period: "2023.01 - 2023.06",
            role: "项目中担任的角色",
            highlights: ["在此新增该项目的职责、难点及技术栈解决亮点...", "第二条项目指标产出描述"]
        },
        skills: {
            category: "技能方向类别",
            list: "具体技能条目1、具体技能条目2、具体技能条目3"
        },
        awards: {
            time: "2024.10",
            name: "请填写所获得的荣誉奖项或证书名称"
        }
    };
    
    if (templates[sectionKey]) {
        pushResumeHistory('新增简历条目');
        section.items.push(templates[sectionKey]);
        localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
        markResumeSaved();
        renderResume();
        showNotification(`成功新增了一条 ${section.title} 条目！`);
    }
};

// 8. 删除条目 block
window.deleteResumeBlock = function(sectionKey, index) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    
    const section = profile.sections[sectionKey];
    if (!section || !section.items[index]) return;
    
    if (confirm(`您确定要删除此条 ${section.title} 记录吗？`)) {
        pushResumeHistory('删除简历条目');
        section.items.splice(index, 1);
        localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
        markResumeSaved();
        renderResume();
        showNotification('已成功删除该条目。');
    }
};

// 9. 移动条目 block (swap 排序)
window.moveResumeBlock = function(sectionKey, index, direction) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    
    const section = profile.sections[sectionKey];
    if (!section) return;
    
    const targetIdx = index + direction;
    if (targetIdx < 0 || targetIdx >= section.items.length) return;
    
    // 数组换位
    pushResumeHistory('调整条目排序');
    const temp = section.items[index];
    section.items[index] = section.items[targetIdx];
    section.items[targetIdx] = temp;
    
    localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
    markResumeSaved();
    renderResume();
    showNotification('排序调整已生效！');
};

// 10. 给工作或项目经历新增子要点 (bullet)
window.addBullet = function(sectionKey, index) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (profile && profile.sections[sectionKey] && profile.sections[sectionKey].items[index]) {
        const item = profile.sections[sectionKey].items[index];
        if (item.highlights) {
            pushResumeHistory('新增项目要点');
            item.highlights.push("新增要点工作业绩或项目细节描述...");
            localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
            markResumeSaved();
            renderResume();
        }
    }
};

// 11. 删除经历或项目的具体子要点 (bullet)
window.deleteBullet = function(sectionKey, index, bulletIndex) {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (profile && profile.sections[sectionKey] && profile.sections[sectionKey].items[index]) {
        const item = profile.sections[sectionKey].items[index];
        if (item.highlights && item.highlights[bulletIndex] !== undefined) {
            pushResumeHistory('删除项目要点');
            item.highlights.splice(bulletIndex, 1);
            localStorage.setItem('interview_prep_edited_resumes', JSON.stringify(data));
            markResumeSaved();
            renderResume();
        }
    }
};

// ==========================================================================
// 简历导出与打印逻辑重构 (尊重自定义配色与隐藏设置)
// ==========================================================================

// 获取剥离了所有控制边框、删除按钮等辅助元素的纯净简历 DOM 片段
function getCleanResumeHTML() {
    const paperClone = document.getElementById('resume-paper-target').cloneNode(true);
    
    // 移除所有的交互和辅助按钮组件
    paperClone.querySelectorAll('.block-actions-overlay').forEach(el => el.remove());
    paperClone.querySelectorAll('.bullet-delete-btn').forEach(el => el.remove());
    paperClone.querySelectorAll('.add-bullet-btn').forEach(el => el.remove());
    paperClone.querySelectorAll('svg').forEach(el => el.remove());
    paperClone.querySelectorAll('i').forEach(el => el.remove());
    
    // 移除可编辑属性
    paperClone.removeAttribute('contenteditable');
    paperClone.querySelectorAll('[contenteditable]').forEach(el => {
        el.removeAttribute('contenteditable');
        el.style.outline = 'none';
        el.style.border = 'none';
        el.style.background = 'transparent';
    });
    
    return paperClone.innerHTML;
}

// 1. 导出 Word (.doc 格式) - 动态嵌入用户选择的主题配色
window.exportResumeWord = function() {
    const cleanContent = getCleanResumeHTML();
    const profile = getEditedResumeData().profiles[AppState.resumeProfile];
    const themeColor = profile.themeColor || '#0d9488';
    
    const wordHTML = `
        <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
        <head>
            <meta charset="utf-8">
            <title>个人简历 - ${AppState.resumeProfile}</title>
            <!--[if gte mso 9]>
            <xml>
                <w:WordDocument>
                    <w:View>Print</w:View>
                    <w:Zoom>100</w:Zoom>
                </w:WordDocument>
            </xml>
            <![endif]-->
            <style>
                body { font-family: 'SimSun', 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333333; margin: 40px; }
                .resume-basic-info-block { border-bottom: 2px solid ${themeColor}; padding-bottom: 12px; margin-bottom: 20px; }
                .info-fields-grid { width: 100%; }
                .info-field { font-size: 10.5pt; margin-bottom: 6px; }
                .field-label { font-weight: bold; color: #555555; }
                .field-value { color: #111827; }
                .resume-section { margin-top: 25px; margin-bottom: 15px; }
                .resume-section-header-wrap { border-bottom: 2px solid ${themeColor}; margin-bottom: 12px; }
                .resume-section-title { font-size: 13pt; font-weight: bold; color: #ffffff !important; background: ${themeColor}; padding: 6px 12px; display: inline-block; }
                .resume-project-item { margin-bottom: 20px; }
                .resume-project-header { font-weight: bold; color: #1f2937; margin-bottom: 4px; }
                .resume-project-header span { font-size: 11pt; }
                .resume-project-role { font-size: 10pt; color: ${themeColor}; font-weight: bold; margin-bottom: 6px; }
                .resume-bullets { margin-left: 20px; padding-left: 0; }
                .resume-bullets li { margin-bottom: 5px; list-style-type: disc; font-size: 10.5pt; color: #374151; }
                strong { color: #111827; }
            </style>
        </head>
        <body>
            ${cleanContent}
        </body>
        </html>
    `;
    
    const blob = new Blob([wordHTML], { type: 'application/vnd.ms-word;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `简历_${AppState.resumeProfile}_${new Date().toISOString().slice(0,10)}.doc`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('MS Word 格式文档已生成并开始下载！');
};

// 2. 导出 HTML 网页 - 保留斜切 ribbon 视觉和当前主题色
window.exportResumeHTML = function() {
    const cleanContent = getCleanResumeHTML();
    const profile = getEditedResumeData().profiles[AppState.resumeProfile];
    const themeColor = profile.themeColor || '#0d9488';
    
    const fullHTML = `
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>个人简历 - ${AppState.resumeProfile}</title>
            <style>
                body {
                    background-color: #f3f4f6;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    color: #1f2937;
                    line-height: 1.6;
                    padding: 40px 20px;
                    margin: 0;
                }
                .resume-container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: #ffffff;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }
                .resume-basic-info-block {
                    display: flex;
                    justify-content: space-between;
                    gap: 24px;
                    border-bottom: 2px solid ${themeColor};
                    padding-bottom: 20px;
                    margin-bottom: 20px;
                }
                .info-fields-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 8px 16px;
                    flex: 1;
                }
                .info-field {
                    display: flex;
                    font-size: 0.9rem;
                }
                .field-label {
                    color: #4b5563;
                    font-weight: 600;
                    width: 75px;
                }
                .field-value {
                    color: #111827;
                }
                .info-avatar-box {
                    width: 100px;
                    height: 133px;
                    border: 1px solid #e5e7eb;
                    border-radius: 4px;
                    overflow: hidden;
                }
                .info-avatar-box img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }
                .resume-section {
                    margin-bottom: 26px;
                }
                .resume-section-title {
                    font-size: 1.1rem;
                    font-weight: 700;
                    color: white !important;
                    background: ${themeColor};
                    padding: 6px 24px 6px 12px;
                    display: inline-block;
                    clip-path: polygon(0 0, 88% 0, 100% 100%, 0 100%);
                    margin: 0;
                }
                .resume-project-item {
                    margin-bottom: 16px;
                }
                .resume-project-header {
                    display: flex;
                    justify-content: space-between;
                    font-weight: 600;
                    color: #111827;
                    margin-bottom: 4px;
                }
                .resume-project-role {
                    font-size: 0.88rem;
                    color: ${themeColor};
                    font-weight: 600;
                    margin-bottom: 6px;
                }
                .resume-bullets {
                    padding-left: 20px;
                    margin: 0;
                }
                .resume-bullets li {
                    margin-bottom: 6px;
                }
                strong {
                    color: #111827;
                }
                @media print {
                    body { background: transparent; padding: 0; }
                    .resume-container { box-shadow: none; padding: 0; max-width: 100%; }
                }
            </style>
        </head>
        <body>
            <div class="resume-container">
                ${cleanContent}
            </div>
        </body>
        </html>
    `;
    
    const blob = new Blob([fullHTML], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `简历_${AppState.resumeProfile}_${new Date().toISOString().slice(0,10)}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('独立 HTML 网页格式已成功下载！');
};

// 3. 导出 Markdown (.md) - 从底层结构化数据生成，跳过被隐藏的板块
window.exportResumeMarkdown = function() {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    
    const info = profile.personalInfo;
    
    let md = `# ${info.name}\n\n`;
    md += `**年龄**：${info.age} | **性别**：${info.gender} | **籍贯**：${info.hometown} | **工作年限**：${info.experience}\n`;
    md += `**求职岗位**：${info.targetJob}\n`;
    md += `**目标薪资**：${info.targetSalary || '15K'}\n`;
    md += `**联系电话**：${info.phone} | **电子邮箱**：${info.email}\n\n`;
    md += `---\n\n`;
    
    // 自我评价
    if (profile.sections.selfEvaluation && profile.sections.selfEvaluation.show !== false) {
        md += `## ${profile.sections.selfEvaluation.title}\n\n`;
        md += `${profile.sections.selfEvaluation.text}\n\n`;
    }
    
    // 教育背景
    if (profile.sections.education && profile.sections.education.show !== false) {
        md += `## ${profile.sections.education.title}\n\n`;
        profile.sections.education.items.forEach(item => {
            md += `### ${item.school} (${item.period})\n`;
            md += `**专业**：${item.major} | **成绩**：${item.gpa}\n`;
            md += `${item.courses}\n\n`;
        });
    }
    
    // 工作经历
    if (profile.sections.workExperience && profile.sections.workExperience.show !== false) {
        md += `## ${profile.sections.workExperience.title}\n\n`;
        profile.sections.workExperience.items.forEach(item => {
            md += `### ${item.company} (${item.period})\n`;
            md += `**岗位**：${item.role}\n`;
            item.highlights.forEach(h => {
                md += `- ${h}\n`;
            });
            md += `\n`;
        });
    }
    
    // 项目经验
    if (profile.sections.projects && profile.sections.projects.show !== false) {
        md += `## ${profile.sections.projects.title}\n\n`;
        profile.sections.projects.items.forEach(item => {
            md += `### ${item.name} (${item.period})\n`;
            md += `**角色**：${item.role}\n`;
            item.highlights.forEach(h => {
                md += `- ${h}\n`;
            });
            md += `\n`;
        });
    }
    
    // 专业技能
    if (profile.sections.skills && profile.sections.skills.show !== false) {
        md += `## ${profile.sections.skills.title}\n\n`;
        profile.sections.skills.items.forEach(item => {
            md += `- **${item.category}**：${item.list}\n`;
        });
        md += `\n`;
    }
    
    // 荣誉奖项
    if (profile.sections.awards && profile.sections.awards.show !== false) {
        md += `## ${profile.sections.awards.title}\n\n`;
        profile.sections.awards.items.forEach(item => {
            md += `- **${item.time}**：${item.name}\n`;
        });
        md += `\n`;
    }
    
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `简历_${AppState.resumeProfile}_${new Date().toISOString().slice(0,10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Markdown 格式简历已成功下载！');
};

// 4. 复制简历文本 - 从结构化数据导出
window.copyResumeText = function() {
    const data = getEditedResumeData();
    const profile = data.profiles[AppState.resumeProfile];
    if (!profile) return;
    
    const info = profile.personalInfo;
    
    let text = `【基本信息】\n`;
    text += `姓名：${info.name}\n年龄：${info.age}\n性别：${info.gender}\n籍贯：${info.hometown}\n工作年限：${info.experience}\n`;
    text += `求职岗位：${info.targetJob}\n`;
    text += `目标薪资：${info.targetSalary || '15K'}\n`;
    text += `联系电话：${info.phone}\n电子邮箱：${info.email}\n\n`;
    
    if (profile.sections.selfEvaluation && profile.sections.selfEvaluation.show !== false) {
        text += `【${profile.sections.selfEvaluation.title}】\n${profile.sections.selfEvaluation.text}\n\n`;
    }
    
    if (profile.sections.education && profile.sections.education.show !== false) {
        text += `【${profile.sections.education.title}】\n`;
        profile.sections.education.items.forEach(item => {
            text += `■ ${item.school} (${item.period})\n  专业：${item.major} | 成绩：${item.gpa}\n  ${item.courses}\n\n`;
        });
    }
    
    if (profile.sections.workExperience && profile.sections.workExperience.show !== false) {
        text += `【${profile.sections.workExperience.title}】\n`;
        profile.sections.workExperience.items.forEach(item => {
            text += `■ ${item.company} (${item.period})\n  岗位：${item.role}\n  工作内容：\n`;
            item.highlights.forEach(h => {
                text += `  * ${h}\n`;
            });
            text += `\n`;
        });
    }
    
    if (profile.sections.projects && profile.sections.projects.show !== false) {
        text += `【${profile.sections.projects.title}】\n`;
        profile.sections.projects.items.forEach(item => {
            text += `■ ${item.name} (${item.period})\n  角色：${item.role}\n  项目描述：\n`;
            item.highlights.forEach(h => {
                text += `  * ${h}\n`;
            });
            text += `\n`;
        });
    }
    
    if (profile.sections.skills && profile.sections.skills.show !== false) {
        text += `【${profile.sections.skills.title}】\n`;
        profile.sections.skills.items.forEach(item => {
            text += `- ${item.category}：${item.list}\n`;
        });
        text += `\n`;
    }
    
    if (profile.sections.awards && profile.sections.awards.show !== false) {
        text += `【${profile.sections.awards.title}】\n`;
        profile.sections.awards.items.forEach(item => {
            text += `- ${item.time}：${item.name}\n`;
        });
        text += `\n`;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        showNotification("已复制简历纯文本到剪贴板！");
    }).catch(err => {
        console.error("复制失败:", err);
        alert("复制失败，请手动选择复制。");
    });
};

window.printResume = function() {
    window.print();
};

/* ==========================================================================
   PPT GENERATOR 核心算法汇报幻灯片一键生成与可编辑导出模块
   ========================================================================== */

// 初始化大纲数据组装 - 各种核心算法总结 (清爽风格)
window.initPPTGenerator = function() {
    const outline = [];
    
    // Slide 1: 封面
    outline.push({
        title: "AI 算法与空间智能核心技术深度总结汇报",
        subtitle: "应聘岗位：全栈 AI & 空间计算专家  |  技术答辩演示文稿",
        type: 'cover',
        items: [
            "汇报内容：机器学习、Transformer架构、LLM与RAG、计算机视觉、遥感航测与空间大数据",
            "报告生成形式：纯前端 PptxGenJS 原生矢量导出 (100% 可编辑)",
            "主讲人：空间计算 & AI 算法专家",
            `汇报时间：${new Date().toISOString().slice(0, 10)}`
        ]
    });
    
    // Slide 2: 机器学习
    outline.push({
        title: "第一部分：机器学习核心算法与最值求解",
        subtitle: "集成学习架构设计与分类回归决策边界数学原理",
        type: 'ml',
        items: [
            "【支持向量机 SVM】: 寻找超平面最大化几何间隔 γ=2/||w||。通过对偶化将原约束问题转为拉格朗日乘子 alpha_i 形态，使计算仅依赖样本内积，便于使用核技巧处理高维非线性分类。",
            "【XGBoost & LightGBM】: XGBoost采用二阶泰勒展开逼近局部最优，通过分叶节点分裂增益控制剪枝；LightGBM 引入 GOSS 单边梯度采样和 EFB 互斥特征捆绑，解决大规模样本训练算力开销。",
            "【CatBoost 性能】: 引入 Ordered Boosting 解决目标泄漏（Target Leakage），利用对称决策树（Symmetric Trees）提升推理速度，提供原生的分类变量自动处理与极强抗过拟合性能。",
            "【降维技术对比】: PCA 属于线性投影，保留全局最大方差；t-SNE 利用 KL 散度与 t 分布保留局部邻域结构用于可视化；UMAP 结合拓扑流形，兼顾局部与全局拓扑结构关系且计算速度极快。"
        ]
    });
    
    // Slide 3: Transformer
    outline.push({
        title: "第二部分：深度学习与 Transformer 架构演进",
        subtitle: "注意力机制数学机理与长文本序列归一化优化",
        type: 'transformer',
        items: [
            "【自注意力公式】: Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V。除以缩放因子 sqrt(d_k) 是为了将内积的方差归一化为 1，避免 Softmax 输入过大进入饱和区从而导致梯度消失。",
            "【旋转位置编码 RoPE】: 通过在复数空间对 Query 和 Key 向量进行 2D 坐标系坐标旋转注入位置信息，内积自然包含相对距离差，具有极佳的线性外推优势，支持扩展至百万级上下文。",
            "【三维归一化 LN/BN/GN】: BatchNorm 沿 Batch 计算，依赖 BatchSize；LayerNorm 沿通道维度计算，适于变长序列；GroupNorm 通道分组归一化，适合超小 Batch 目标检测任务。",
            "【FlashAttention IO优化】: 针对 GPU 显存吞吐瓶颈，采用 Tiling 分块计算并结合在线 Softmax 更新算法，避免将 L*L 注意力矩阵写回 HBM，实现 O(L) 显存开销，计算提速 2-4 倍。"
        ]
    });
    
    // Slide 4: LLM, RAG & Agents
    outline.push({
        title: "第三部分：大语言模型、高可靠 RAG 与智能体",
        subtitle: "显存带宽降本、混合检索重排与自进化 Skill Engine 环路",
        type: 'llm_rag',
        items: [
            "【推理优化 GQA/MQA】: GQA (Grouped-Query Attention) 将 Q 头分组并共享一组 K、V 头，降低 KV Cache 显存读写带宽压力，在推理吞吐量与模型表达力之间取得最优折中。",
            "【企业级 RAG 检索管线】: 引入基于句间语义相似度的语义切割(Semantic Chunking)，采用 Dense 向量与 Sparse BM25 混合检索，利用 RRF (倒数排名融合) 与 Cross-Encoder 重排过滤噪点。",
            "【Nous Hermes 自进化智能体】: 系统提示词高依从度，在任务受挫时通过 Sandbox 运行 Python 捕获 Traceback 并自我修正，将成功代码持久化为 Skill 存入本地技能库，实现自主进化。"
        ]
    });
    
    // Slide 5: SAM & CV
    outline.push({
        title: "第四部分：计算机视觉与 Segment Anything 分割",
        subtitle: "交互式掩膜生成、时序分割追踪与免 NMS 目标检测",
        type: 'cv_sam',
        items: [
            "【SAM 1 图像分割架构】: ViT Image Encoder 提取 1024*1024 图像 Embedding，结合点/框等稀疏 Prompt 编码，Mask Decoder 双向 Transformer 交叉注意力交互，并行输出多尺度掩膜消除歧义。",
            "【SAM 2 视频追踪演进】: 引入流式记忆系统。Memory Bank 缓存短期空间预测与长期关键提示特征，Memory Attention 对当前帧进行跨时间对齐，解决物体运动大范围遮挡和移出视角追踪。",
            "【YOLOv10 免 NMS 检测】: 采用 Decoupled Head 分类与回归分支分离；设计 Dual Label Assignment 双标签分配，在推理时直接采用一对一分支，彻底抛弃 NMS，耗时下降 50% 以上。"
        ]
    });
    
    // Slide 6: 遥感与空间计算
    outline.push({
        title: "第五部分：摄影测量学、遥感算法与大数据工程",
        subtitle: "三维空三重建、地理控制点平差相似变换与高吞吐流计算",
        type: 'rs_uav',
        items: [
            "【SfM 三维重建】: 提取 SIFT 尺度不变特征点，利用 RANSAC 估计本质矩阵；进行光束法平差 (Bundle Adjustment) 最小化重投影误差，解算相机位姿 (R, T) 并生成稀疏地表三维点云。",
            "【RTK/GCP 相似变换】: 内业解算的相对地理空间坐标，通过手动/自动刺入 RTK 外业地面控制点，运行七参数 Bursa-Wolf 空间相似变换模型，配准转入 CGCS2000 等高精度投影平面。",
            "【Spark/Flink 空间数据湖】: Spark Sedona 实现遥感正射影像(DOM)分布式重采样与空间重投影；Flink Async I/O 连接 Milvus 向量库，吞吐率达 50000 ops/s 并保证 Exactly-Once 语义。"
        ]
    });
    
    // Slide 7: 致谢 Q&A
    outline.push({
        title: "谢谢您的观看与技术交流",
        subtitle: "期待有机会共同推动前沿技术与业务落地",
        type: 'thanks',
        items: [
            "欢迎各位面试官进行提问与技术答辩 (Q&A)",
            "技术汇报完毕，谢谢！"
        ]
    });
    
    AppState.pptOutline = outline;
    renderPPTPreview();
};

// 渲染 PPT 卡片缩略图 (分栏布局，右侧展示算法图解)
window.renderPPTPreview = function() {
    const container = document.getElementById('ppt-slides-preview-container');
    if (!container) return;
    
    container.innerHTML = '';
    const theme = AppState.pptTheme || 'academic';
    
    AppState.pptOutline.forEach((slide, idx) => {
        const card = document.createElement('div');
        card.className = `ppt-slide-card theme-${theme}`;
        
        let bodyHTML = '';
        if (slide.type === 'cover' || slide.type === 'thanks') {
            bodyHTML = `
                <div class="slide-body-edit editable" data-index="${idx}" data-type="body" style="text-align: center; justify-content: center; display: flex; flex-direction: column; height: 100%;">
                    <div style="font-weight:600; font-size:0.75rem; margin-bottom:8px; color:var(--resume-accent, #0d9488);">${slide.subtitle}</div>
                    ${slide.items.map(item => `<div style="margin-bottom: 4px;">${item}</div>`).join('')}
                </div>
            `;
        } else {
            // 右侧算法微型插图逻辑
            let illusHTML = '';
            if (slide.type === 'ml') {
                illusHTML = `
                    <div class="mini-illustration">
                        <div class="illus-node">数据集</div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-leaves">
                            <div class="illus-node leaf" style="font-size:0.5rem; min-width:60px;">RF (Bagging)</div>
                            <div class="illus-node leaf" style="font-size:0.5rem; min-width:60px;">XGB (Boosting)</div>
                        </div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-node font-sm" style="background:#0f172a; min-width:130px;">方差/偏差降低</div>
                    </div>
                `;
            } else if (slide.type === 'transformer') {
                illusHTML = `
                    <div class="mini-illustration">
                        <div class="illus-inputs">
                            <span class="illus-chip">Q</span>
                            <span class="illus-chip">K</span>
                            <span class="illus-chip">V</span>
                        </div>
                        <div class="illus-arrow" style="margin:2px 0;">↓</div>
                        <div class="illus-node op font-sm" style="min-width:120px;">Softmax(QKᵀ / √dₖ)</div>
                        <div class="illus-arrow" style="margin:2px 0;">↓</div>
                        <div class="illus-node font-sm" style="background:#0f172a; min-width:120px;">Attention Out</div>
                    </div>
                `;
            } else if (slide.type === 'llm_rag') {
                illusHTML = `
                    <div class="mini-illustration" style="gap:4px;">
                        <div class="illus-node font-sm" style="min-width:120px;">Query</div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-node op font-sm" style="min-width:120px; background:#06b6d4;">混合检索召回</div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-node op font-sm" style="min-width:120px;">Rerank重排</div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-node font-sm" style="background:#0f172a; min-width:120px;">LLM生成答案</div>
                    </div>
                `;
            } else if (slide.type === 'cv_sam') {
                illusHTML = `
                    <div class="mini-illustration">
                        <div class="illus-node font-sm" style="min-width:110px;">Frame t 图像</div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-node op font-sm" style="min-width:110px;">Memory Attention</div>
                        <div class="illus-arrow" style="margin:1px 0;">⇅</div>
                        <div class="illus-node mem font-sm" style="min-width:110px;">Memory Bank</div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-node font-sm" style="background:#0f172a; min-width:110px;">掩膜追踪 Mask Out</div>
                    </div>
                `;
            } else if (slide.type === 'rs_uav') {
                illusHTML = `
                    <div class="mini-illustration" style="gap:4px;">
                        <div class="illus-node font-sm" style="background:#10b981; min-width:110px;">航测影像 RAW</div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-node op font-sm" style="min-width:110px;">Sedona 空间ETL</div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-node op font-sm" style="min-width:110px; background:#06b6d4;">Flink 实时流计算</div>
                        <div class="illus-arrow">↓</div>
                        <div class="illus-node font-sm" style="background:#0f172a; min-width:110px;">向量库 & 湖仓</div>
                    </div>
                `;
            }

            bodyHTML = `
                <div class="slide-layout-split">
                    <div class="slide-content-left slide-body-edit editable" data-index="${idx}" data-type="body">
                        <ul>
                            ${slide.items.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="slide-illustration-right" contenteditable="false">
                        ${illusHTML}
                    </div>
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="slide-card-header" contenteditable="false">
                <span class="slide-number">Slide ${idx + 1} (${slide.type === 'cover' ? '封面' : slide.type === 'thanks' ? '致谢' : '算法'})</span>
            </div>
            <div class="slide-title-edit editable" data-index="${idx}" data-type="title">${slide.title}</div>
            ${bodyHTML}
        `;
        
        container.appendChild(card);
    });
    
    // 设置可编辑
    container.querySelectorAll('.editable').forEach(el => {
        el.setAttribute('contenteditable', 'true');
    });
    
    // 高亮主题按钮
    document.querySelectorAll('.ppt-theme-picker button, [id^="ppt-theme-"]').forEach(btn => {
        if (btn.id === `ppt-theme-${theme}-btn`) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    if (window.lucide) lucide.createIcons();
};

// 切换 PPT 视觉主题
window.selectPPTTheme = function(theme) {
    AppState.pptTheme = theme;
    renderPPTPreview();
    showNotification(`已切换至 PPT【${theme === 'dark' ? '极客暗黑' : theme === 'teal' ? '雅致蓝绿' : '极简灰白'}】排版风格！`);
};

// 核心导出可编辑幻灯片逻辑 (清爽风格，内置原生 PPT 可编辑算法图解插图)
window.exportToPPT = function() {
    if (typeof PptxGenJS === 'undefined') {
        alert('PPTX核心库加载中，请稍候重试。');
        return;
    }
    
    const pptx = new PptxGenJS();
    pptx.layout = 'LAYOUT_16x9'; // 设置 16:9 宽屏布局
    
    const theme = AppState.pptTheme || 'academic';
    
    // 基础主题颜色配置
    let bgColor = 'FFFFFF';
    let titleColor = '0F172A'; // 默认清爽深 navy
    let bodyColor = '334155';  // 默认清爽 slate gray
    let accentColor = '0d9488'; // 强调色
    
    if (theme === 'dark') {
        bgColor = '0c111e';
        titleColor = 'FFFFFF';
        bodyColor = 'cbd5e1';
        accentColor = '06B6D4';
    } else if (theme === 'teal') {
        bgColor = 'F0FDFA'; // 清爽浅蓝绿背景
        titleColor = '0F766E'; // 深蓝绿
        bodyColor = '374151';
        accentColor = '0D9488'; 
    } else if (theme === 'academic') {
        bgColor = 'ffffff'; // 极简纯白
        titleColor = '0F172A';
        bodyColor = '334155';
        accentColor = '0284C7'; // 经典天空蓝
    }
    
    AppState.pptOutline.forEach((slideData, idx) => {
        const slide = pptx.addSlide();
        // 设置背景
        slide.background = { fill: bgColor };
        
        if (slideData.type === 'cover') {
            // 1. 封面页排版 (清爽版)
            if (theme === 'dark') {
                slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: '100%', h: 0.15, fill: accentColor });
            } else {
                // 顶部精细色带
                slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: '100%', h: 0.2, fill: accentColor });
            }
            
            // 主标题
            slide.addText(slideData.title, {
                x: 1.0, y: 2.0, w: 11.3, h: 1.2,
                fontSize: 32, fontFace: 'Microsoft YaHei', color: titleColor, bold: true, align: 'center', valign: 'middle'
            });
            
            // 副标题
            slide.addText(slideData.subtitle, {
                x: 1.0, y: 3.4, w: 11.3, h: 0.6,
                fontSize: 18, fontFace: 'Microsoft YaHei', color: accentColor, align: 'center', bold: true
            });
            
            // 信息明细 (双列或单行合并)
            const infoString = slideData.items.join('   |   ');
            slide.addText(infoString, {
                x: 1.0, y: 4.8, w: 11.3, h: 0.8,
                fontSize: 12, fontFace: 'Microsoft YaHei', color: bodyColor, align: 'center'
            });
            
        } else if (slideData.type === 'thanks') {
            // 2. 结束致谢页排版 (清爽版)
            if (theme === 'dark') {
                slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 5.4, w: '100%', h: 0.2, fill: accentColor });
            } else {
                slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 5.2, w: '100%', h: 0.1, fill: accentColor });
            }
            
            slide.addText(slideData.title, {
                x: 1.0, y: 2.2, w: 11.3, h: 1.0,
                fontSize: 36, fontFace: 'Microsoft YaHei', color: titleColor, bold: true, align: 'center'
            });
            
            slide.addText(slideData.subtitle, {
                x: 1.0, y: 3.4, w: 11.3, h: 0.6,
                fontSize: 18, fontFace: 'Microsoft YaHei', color: accentColor, align: 'center', bold: true
            });
            
            slide.addText(slideData.items.join('\n'), {
                x: 1.0, y: 4.4, w: 11.3, h: 0.8,
                fontSize: 14, fontFace: 'Microsoft YaHei', color: bodyColor, align: 'center', lineSpacing: 22
            });
            
        } else {
            // 3. 标准正文页排版 (左侧文字 60%，右侧原生矢量图解 40%)
            let yStart = 1.6;
            
            if (theme === 'dark') {
                // 科技感左侧小彩块
                slide.addShape(pptx.shapes.RECTANGLE, { x: 0.5, y: 0.5, w: 0.08, h: 0.6, fill: accentColor });
                slide.addText(slideData.title, {
                    x: 0.75, y: 0.4, w: 12.0, h: 0.5,
                    fontSize: 22, fontFace: 'Microsoft YaHei', color: titleColor, bold: true
                });
                slide.addText(slideData.subtitle, {
                    x: 0.75, y: 0.95, w: 12.0, h: 0.4,
                    fontSize: 13, fontFace: 'Microsoft YaHei', color: accentColor, bold: true
                });
            } else {
                // 清爽横线板式
                slide.addText(slideData.title, {
                    x: 0.6, y: 0.4, w: 12.1, h: 0.5,
                    fontSize: 22, fontFace: 'Microsoft YaHei', color: titleColor, bold: true
                });
                slide.addText(slideData.subtitle, {
                    x: 0.6, y: 0.95, w: 12.1, h: 0.35,
                    fontSize: 12, fontFace: 'Microsoft YaHei', color: accentColor, bold: true
                });
                slide.addShape(pptx.shapes.LINE, {
                    x: 0.6, y: 1.35, w: 12.1, h: 0,
                    line: { color: 'E2E8F0', width: 1.5 }
                });
            }
            
            // 渲染左半边列表内容为原生 Bullet 文本段
            const bulletItems = slideData.items.map(txt => {
                return { text: txt, options: { bullet: true, color: bodyColor, fontSize: 13.5, fontFace: 'Microsoft YaHei', lineSpacing: 24 } };
            });
            
            slide.addText(bulletItems, {
                x: 0.6, y: yStart, w: 7.2, h: 5.0,
                margin: 0
            });
            
            // 渲染右半边原生可编辑插图 (Theme Illustrations)
            // 插图框背景 (Rounded Rectangle)
            slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
                x: 8.2, y: yStart, w: 4.5, h: 5.0,
                fill: theme === 'dark' ? '18233c' : 'F8FAFC',
                line: { color: theme === 'dark' ? '2e3a5a' : 'E2E8F0', width: 1 }
            });
            
            if (slideData.type === 'ml') {
                // 机器学习：Bagging/Boosting 分裂图解
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 9.45, y: 2.2, w: 2.0, h: 0.6, fill: '0284C7', line: 'none' });
                slide.addText("样本数据集", { x: 9.45, y: 2.2, w: 2.0, h: 0.6, fontSize: 11, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: true });
                
                slide.addShape(pptx.shapes.LINE, { x: 9.6, y: 2.8, w: -0.6, h: 0.6, line: { color: '64748B', width: 2, endArrowType: 'triangle' } });
                slide.addShape(pptx.shapes.LINE, { x: 11.3, y: 2.8, w: 0.6, h: 0.6, line: { color: '64748B', width: 2, endArrowType: 'triangle' } });
                
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 8.5, y: 3.5, w: 1.8, h: 0.7, fill: '0D9488', line: 'none' });
                slide.addText("Random Forest\n(Bagging)", { x: 8.5, y: 3.5, w: 1.8, h: 0.7, fontSize: 9.5, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: true });
                
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 10.6, y: 3.5, w: 1.8, h: 0.7, fill: '0284C7', line: 'none' });
                slide.addText("XGBoost\n(Boosting)", { x: 10.6, y: 3.5, w: 1.8, h: 0.7, fontSize: 9.5, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: true });
                
                slide.addShape(pptx.shapes.LINE, { x: 9.4, y: 4.25, w: 0, h: 0.55, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                slide.addShape(pptx.shapes.LINE, { x: 11.5, y: 4.25, w: 0, h: 0.55, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                
                slide.addShape(pptx.shapes.RECTANGLE, { x: 8.4, y: 4.8, w: 2.0, h: 0.6, fill: theme === 'dark' ? '0e1628' : 'FFFFFF', line: { color: '0D9488', width: 1 } });
                slide.addText("并行独立训练树\n降低模型方差", { x: 8.4, y: 4.8, w: 2.0, h: 0.6, fontSize: 9, fontFace: 'Microsoft YaHei', color: theme === 'dark' ? 'cbd5e1' : '334155', align: 'center', valign: 'middle' });
                
                slide.addShape(pptx.shapes.RECTANGLE, { x: 10.5, y: 4.8, w: 2.0, h: 0.6, fill: theme === 'dark' ? '0e1628' : 'FFFFFF', line: { color: '0284C7', width: 1 } });
                slide.addText("串行残差迭代树\n降低模型偏差", { x: 10.5, y: 4.8, w: 2.0, h: 0.6, fontSize: 9, fontFace: 'Microsoft YaHei', color: theme === 'dark' ? 'cbd5e1' : '334155', align: 'center', valign: 'middle' });
                
                slide.addShape(pptx.shapes.LINE, { x: 9.4, y: 5.4, w: 0.8, h: 0.5, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                slide.addShape(pptx.shapes.LINE, { x: 11.5, y: 5.4, w: -0.8, h: 0.5, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 9.4, y: 5.9, w: 2.1, h: 0.5, fill: '1E293B', line: 'none' });
                slide.addText("模型集成融合预测", { x: 9.4, y: 5.9, w: 2.1, h: 0.5, fontSize: 9.5, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: true });
                
            } else if (slideData.type === 'transformer') {
                // Transformer: Self-Attention 投影乘积图解
                slide.addShape(pptx.shapes.RECTANGLE, { x: 8.5, y: 2.2, w: 1.0, h: 0.5, fill: '0284C7', line: 'none' });
                slide.addText("Query Q", { x: 8.5, y: 2.2, w: 1.0, h: 0.5, fontSize: 9, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle' });
                
                slide.addShape(pptx.shapes.RECTANGLE, { x: 9.9, y: 2.2, w: 1.0, h: 0.5, fill: '0284C7', line: 'none' });
                slide.addText("Key K", { x: 9.9, y: 2.2, w: 1.0, h: 0.5, fontSize: 9, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle' });
                
                slide.addShape(pptx.shapes.RECTANGLE, { x: 11.3, y: 2.2, w: 1.0, h: 0.5, fill: '0D9488', line: 'none' });
                slide.addText("Value V", { x: 11.3, y: 2.2, w: 1.0, h: 0.5, fontSize: 9, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle' });
                
                slide.addShape(pptx.shapes.LINE, { x: 9.0, y: 2.7, w: 0.6, h: 0.7, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                slide.addShape(pptx.shapes.LINE, { x: 10.4, y: 2.7, w: -0.6, h: 0.7, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 8.8, y: 3.4, w: 2.2, h: 0.8, fill: '0284C7', line: 'none' });
                slide.addText("点积注意力相似度计算\nSoftmax( QKᵀ / √dₖ )", { x: 8.8, y: 3.4, w: 2.2, h: 0.8, fontSize: 9, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: true });
                
                slide.addShape(pptx.shapes.LINE, { x: 9.9, y: 4.2, w: 0.5, h: 0.7, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                slide.addShape(pptx.shapes.LINE, { x: 11.8, y: 2.7, w: -1.0, h: 2.2, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 8.7, y: 4.9, w: 3.5, h: 0.8, fill: '0F172A', line: 'none' });
                slide.addText("加权上下文特征输出\nAttention = 相似度权重 × V", { x: 8.7, y: 4.9, w: 3.5, h: 0.8, fontSize: 9.5, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: true });
                
                slide.addShape(pptx.shapes.RECTANGLE, { x: 8.7, y: 5.9, w: 3.5, h: 0.45, fill: theme === 'dark' ? '0e1628' : 'FFFFFF', line: { color: 'E2E8F0', width: 1 } });
                slide.addText("注：通过除以 √dₖ 归一化方差，防梯度消失", { x: 8.7, y: 5.9, w: 3.5, h: 0.45, fontSize: 8.5, fontFace: 'Microsoft YaHei', color: '64748B', align: 'center', valign: 'middle' });
                
            } else if (slideData.type === 'llm_rag') {
                // RAG: 数据管道级联图解
                const steps = [
                    { label: "1. 用户输入 Query", color: '0284C7' },
                    { label: "2. 混合检索 (Dense+BM25) & RRF融合", color: '0D9488' },
                    { label: "3. Cross-Encoder Rerank高精重排", color: '0369A1' },
                    { label: "4. LLM 结合 Prompt+Context 答案生成", color: '0F172A' }
                ];
                
                steps.forEach((step, sIdx) => {
                    const yPos = 2.0 + sIdx * 1.1;
                    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 8.6, y: yPos, w: 3.7, h: 0.7, fill: step.color, line: 'none' });
                    slide.addText(step.label, { x: 8.6, y: yPos, w: 3.7, h: 0.7, fontSize: 9.5, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: sIdx === 3 });
                    
                    if (sIdx < 3) {
                        slide.addShape(pptx.shapes.LINE, { x: 10.45, y: yPos + 0.7, w: 0, h: 0.4, line: { color: '64748B', width: 2, endArrowType: 'triangle' } });
                    }
                });
                
            } else if (slideData.type === 'cv_sam') {
                // SAM 2: 帧追踪时序记忆系统图解
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 8.4, y: 2.1, w: 1.8, h: 0.6, fill: '0284C7', line: 'none' });
                slide.addText("当前帧 Image(t)", { x: 8.4, y: 2.1, w: 1.8, h: 0.6, fontSize: 9.5, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle' });
                
                slide.addShape(pptx.shapes.LINE, { x: 9.3, y: 2.7, w: 0, h: 0.6, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 8.4, y: 3.3, w: 1.8, h: 0.8, fill: '0284C7', line: 'none' });
                slide.addText("Memory Attention\n(时序交叉注意力对齐)", { x: 8.4, y: 3.3, w: 1.8, h: 0.8, fontSize: 9, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: true });
                
                slide.addShape(pptx.shapes.LINE, { x: 9.3, y: 4.1, w: 0, h: 0.7, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 10.7, y: 2.5, w: 1.6, h: 1.3, fill: '0D9488', line: 'none' });
                slide.addText("Memory Bank\n(存储历史6帧预测\n及关键帧特征)", { x: 10.7, y: 2.5, w: 1.6, h: 1.3, fontSize: 8.5, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle' });
                
                slide.addShape(pptx.shapes.LINE, { x: 10.2, y: 3.7, w: 0.5, h: -0.4, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                slide.addShape(pptx.shapes.LINE, { x: 10.7, y: 3.3, w: -0.5, h: 0.4, line: { color: '64748B', width: 1.5, endArrowType: 'triangle' } });
                
                slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 8.4, y: 4.8, w: 4.0, h: 0.6, fill: '0F172A', line: 'none' });
                slide.addText("Mask Decoder 掩膜输出 (视频时序分割)", { x: 8.4, y: 4.8, w: 4.0, h: 0.6, fontSize: 9.5, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: true });
                
                slide.addShape(pptx.shapes.LINE, { x: 11.5, y: 4.8, w: 0.2, h: -1.0, line: { color: '10B981', width: 1.5, endArrowType: 'triangle' } });
                
                slide.addShape(pptx.shapes.RECTANGLE, { x: 8.4, y: 5.6, w: 4.0, h: 0.6, fill: theme === 'dark' ? '0e1628' : 'FFFFFF', line: { color: 'E2E8F0', width: 1 } });
                slide.addText("注：SAM 2 通过引入记忆机制，克服目标遮挡丢失", { x: 8.4, y: 5.6, w: 4.0, h: 0.6, fontSize: 8.5, fontFace: 'Microsoft YaHei', color: '64748b', align: 'center', valign: 'middle' });
                
            } else if (slideData.type === 'rs_uav') {
                // 空间大数据流图解
                const rsSteps = [
                    { label: "1. 航测多光谱/高分辨率影像数据", color: '0D9488' },
                    { label: "2. Spark Sedona 空间ETL (分布式纠正重投影)", color: '0369A1' },
                    { label: "3. Flink 实时植被 NDVI 异常流监控计算", color: '0284C7' },
                    { label: "4. Milvus 空间向量索引 + PostGIS 湖仓存储", color: '0F172A' }
                ];
                
                rsSteps.forEach((step, sIdx) => {
                    const yPos = 2.0 + sIdx * 1.1;
                    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 8.5, y: yPos, w: 3.8, h: 0.7, fill: step.color, line: 'none' });
                    slide.addText(step.label, { x: 8.5, y: yPos, w: 3.8, h: 0.7, fontSize: 9.5, fontFace: 'Microsoft YaHei', color: 'FFFFFF', align: 'center', valign: 'middle', bold: sIdx === 3 });
                    
                    if (sIdx < 3) {
                        slide.addShape(pptx.shapes.LINE, { x: 10.4, y: yPos + 0.7, w: 0, h: 0.4, line: { color: '64748B', width: 2, endArrowType: 'triangle' } });
                    }
                });
            }
        }
    });
    
    // 输出保存文件
    pptx.writeFile({ fileName: `AI与遥感核心算法总结技术汇报PPT.pptx` })
        .then(() => {
            showNotification('PPT 导出成功！所有幻灯片文本框、矢量图解插图均可在 PowerPoint/WPS 中进行二次修改。');
        })
        .catch(err => {
            console.error('PPT 导出失败:', err);
            alert('PPT 文件保存失败，请重试或检查浏览器安全设置。');
        });
};

/* ==========================================================================
   KNOWLEDGE 知识库模块
   ========================================================================== */
function renderKnowledgeMenu() {
    const menuContainer = document.getElementById('k-menu');
    if (!menuContainer) return;
    menuContainer.innerHTML = '';
    
    knowledgeData.forEach(cat => {
        const item = document.createElement('div');
        item.className = `k-menu-item ${AppState.currentKnowledgeCategory === cat.id ? 'active' : ''}`;
        item.setAttribute('data-id', cat.id);
        
        item.innerHTML = `
            <span style="display:flex;align-items:center;gap:10px;">
                <i data-lucide="${cat.icon || 'book-open'}" style="width:16px;height:16px;"></i>
                ${cat.name}
            </span>
            <span class="k-menu-count">${cat.items.length}</span>
        `;
        
        item.addEventListener('click', () => {
            document.querySelectorAll('#k-menu .k-menu-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
            AppState.currentKnowledgeCategory = cat.id;
            renderKnowledgeContent();
        });
        
        menuContainer.appendChild(item);
    });
    
    if (window.lucide) lucide.createIcons();
}

function renderKnowledgeContent() {
    const contentContainer = document.getElementById('k-content');
    if (!contentContainer) return;
    contentContainer.innerHTML = '';
    
    const category = knowledgeData.find(cat => cat.id === AppState.currentKnowledgeCategory);
    if (!category) return;
    
    category.items.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = 'glass-card';
        card.style.marginBottom = '20px';
        const cardId = `${category.id}__${index}`;
        
        let detailsHTML = item.details.map(d => `<div class="k-text-block">${formatContent(d)}</div>`).join('');
        
        let codeHTML = '';
        if (item.code) {
            codeHTML = `<pre class="code-block"><code>${escapeHTML(item.code)}</code></pre>`;
        }
        
        const analogyText = item.analogy ? formatContent(item.analogy).replace(/\n/g, '<br>') : '暂无直白大白话比喻讲解。';
        const scriptText = item.interview_script ? formatContent(item.interview_script).replace(/\n/g, '<br>') : '暂无面试通关话术。';
        const codeCopyButton = item.code ? `
            <button class="knowledge-copy-btn" type="button" onclick="copyKnowledgeContent('${cardId}', 'code')">
                <i data-lucide="code-2"></i> 复制代码
            </button>
        ` : '';

        card.innerHTML = `
            <div class="k-card-header">
                <div class="k-card-title">
                    ${item.term}
                    <span class="k-card-tag">${category.name}</span>
                </div>
                <div class="knowledge-copy-actions">
                    <button class="knowledge-copy-btn" type="button" onclick="copyKnowledgeContent('${cardId}', 'full')">
                        <i data-lucide="copy"></i> 复制卡片
                    </button>
                    <button class="knowledge-copy-btn" type="button" onclick="copyKnowledgeContent('${cardId}', 'interview')">
                        <i data-lucide="message-square-quote"></i> 复制话术
                    </button>
                    ${codeCopyButton}
                </div>
            </div>
            <div class="k-subtitle" style="color:var(--text-secondary);font-weight:400;margin-bottom:16px;font-style:italic;">
                ${item.desc}
            </div>
            
            <!-- 子 Tab 切换导航 -->
            <div class="k-card-tabs" style="display:flex; gap:8px; border-bottom:1px solid var(--card-border); padding-bottom:8px; margin-bottom:16px;">
                <button class="k-tab-btn active" data-tab="math" onclick="switchCardTab(this, 'math')">🔬 深度数学原理</button>
                <button class="k-tab-btn" data-tab="analogy" onclick="switchCardTab(this, 'analogy')">💡 大白话直白比喻</button>
                <button class="k-tab-btn" data-tab="interview" onclick="switchCardTab(this, 'interview')">🗣️ 面试答题话术</button>
            </div>
            
            <!-- 🔬 深度数学原理 (Math & Code) -->
            <div class="k-tab-content-panel data-tab-math">
                <div class="k-details-body">
                    ${detailsHTML}
                </div>
                ${codeHTML}
            </div>
            
            <!-- 💡 大白话直白比喻 -->
            <div class="k-tab-content-panel data-tab-analogy" style="display:none;">
                <div class="k-analogy-body" style="line-height:1.7; color:var(--text-secondary); font-size:0.95rem; text-align:justify;">
                    ${analogyText}
                </div>
            </div>
            
            <!-- 🗣️ 面试答题话术 -->
            <div class="k-tab-content-panel data-tab-interview" style="display:none;">
                <div class="k-interview-body" style="line-height:1.7; color:var(--text-secondary); font-size:0.95rem; text-align:justify; background:rgba(2, 132, 199, 0.02); border-left:4px solid var(--primary); padding:12px 16px; border-radius:0 8px 8px 0;">
                    ${scriptText}
                </div>
            </div>
        `;
        
        contentContainer.appendChild(card);
    });
    
    // 渲染公式
    triggerMathRender(contentContainer);
    if (window.lucide) lucide.createIcons();
}

function getKnowledgeItemByCardId(cardId) {
    const [categoryId, rawIndex] = String(cardId || '').split('__');
    const category = knowledgeData.find(cat => cat.id === categoryId);
    if (!category) return null;
    const item = category.items[Number(rawIndex)];
    return item ? { category, item } : null;
}

function buildKnowledgeCopyText(category, item, mode) {
    if (mode === 'interview') {
        return `${item.term}\n\n${stripMarkdown(item.interview_script || '暂无面试通关话术。')}`;
    }
    if (mode === 'code') {
        return item.code || '';
    }
    return [
        `# ${item.term}`,
        '',
        `分类：${category.name}`,
        `简介：${stripMarkdown(item.desc || '')}`,
        '',
        '## 核心要点',
        ...(item.details || []).map(detail => `- ${stripMarkdown(detail)}`),
        '',
        item.analogy ? `## 大白话\n${stripMarkdown(item.analogy)}` : '',
        item.interview_script ? `## 面试表达\n${stripMarkdown(item.interview_script)}` : '',
        item.code ? `## 代码片段\n${item.code}` : ''
    ].filter(Boolean).join('\n');
}

function writeClipboardText(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    }
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(textarea);
    return ok ? Promise.resolve() : Promise.reject(new Error('copy failed'));
}

window.copyKnowledgeContent = function(cardId, mode) {
    const found = getKnowledgeItemByCardId(cardId);
    if (!found) return;
    const text = buildKnowledgeCopyText(found.category, found.item, mode);
    if (!text.trim()) {
        showNotification('当前卡片没有可复制内容');
        return;
    }
    writeClipboardText(text)
        .then(() => {
            const label = mode === 'interview' ? '面试话术' : mode === 'code' ? '代码片段' : '知识卡片';
            showNotification(`已复制${label}`);
        })
        .catch(() => alert('复制失败，请手动选中文本复制。'));
};

window.switchCardTab = function(btn, tabName) {
    const cardEl = btn.closest('.glass-card');
    if (!cardEl) return;
    
    // Toggle active state of tabs inside the card
    cardEl.querySelectorAll('.k-tab-btn').forEach(b => {
        if (b === btn) {
            b.classList.add('active');
        } else {
            b.classList.remove('active');
        }
    });
    
    // Toggle active state of content panels inside the card
    cardEl.querySelectorAll('.k-tab-content-panel').forEach(panel => {
        if (panel.classList.contains(`data-tab-${tabName}`)) {
            panel.style.display = 'block';
        } else {
            panel.style.display = 'none';
        }
    });
};

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

window.initMathRendering = function() {
    window.mathReady = true;
    triggerMathRender();
};

window.triggerMathRender = function(element) {
    if (window.renderMathInElement && window.mathReady) {
        const target = element || document.body;
        renderMathInElement(target, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false}
            ],
            throwOnError: false
        });
    }
};

function formatContent(str) {
    if (!str) return '';
    let html = escapeHTML(str);
    // Bold: **text** -> <strong>text</strong>
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Inline code: `code` -> <code class="inline-code">$1</code>
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    return html;
}

function getCleanMarkdownText(el) {
    let html = el.innerHTML;
    // Replace <strong> or <b> with **
    html = html.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, '**$1**');
    html = html.replace(/<b[^>]*>([\s\S]*?)<\/b>/gi, '**$1**');
    // Replace <code class="inline-code"> with `
    html = html.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, '`$1`');
    
    // Create a temporary div to get textContent (which strips other HTML tags and decodes entities like &amp;)
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    return tempDiv.textContent.trim();
}

/* ==========================================================================
   GLOBAL SEARCH 全局高亮检索
   ========================================================================== */
function performGlobalSearch(query) {
    if (!query) {
        // 重置为正常目录展示
        renderKnowledgeContent();
        return;
    }
    
    const contentContainer = document.getElementById('k-content');
    if (!contentContainer) return;
    contentContainer.innerHTML = '';
    
    let matchCount = 0;
    
    knowledgeData.forEach(cat => {
        cat.items.forEach(item => {
            const textToSearch = `${item.term} ${item.desc} ${item.details.join(' ')} ${item.code || ''}`.toLowerCase();
            
            if (textToSearch.includes(query)) {
                matchCount++;
                const card = document.createElement('div');
                card.className = 'glass-card';
                card.style.marginBottom = '20px';
                
                // 高亮替换逻辑
                const highlight = (text) => {
                    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
                    return text.replace(regex, '<span class="keyword-highlight">$1</span>');
                };
                
                let detailsHTML = item.details.map(d => `<div class="k-text-block">${highlight(d)}</div>`).join('');
                let codeHTML = '';
                if (item.code) {
                    codeHTML = `<pre class="code-block"><code>${highlight(escapeHTML(item.code))}</code></pre>`;
                }
                
                card.innerHTML = `
                    <div class="k-card-title">
                        ${highlight(item.term)}
                        <span class="k-card-tag">${cat.name}</span>
                    </div>
                    <div class="k-subtitle" style="color:var(--text-secondary);font-weight:400;margin-bottom:16px;font-style:italic;">
                        ${highlight(item.desc)}
                    </div>
                    <div class="k-details-body">
                        ${detailsHTML}
                    </div>
                    ${codeHTML}
                `;
                contentContainer.appendChild(card);
            }
        });
    });
    
    if (matchCount === 0) {
        contentContainer.innerHTML = `
            <div style="text-align:center;padding:40px;color:var(--text-muted);">
                <i data-lucide="search-slash" style="width:48px;height:48px;margin-bottom:12px;"></i>
                <p>未找到包含 "${query}" 的相关知识点词条，请尝试换一个关键词。</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
    }
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function getGlobalSearchPanel() {
    let panel = document.getElementById('global-search-panel');
    if (panel) return panel;

    const searchBox = document.querySelector('.search-box');
    if (!searchBox) return null;
    panel = document.createElement('div');
    panel.id = 'global-search-panel';
    panel.className = 'global-search-panel';
    searchBox.appendChild(panel);
    return panel;
}

function getSearchableText(parts) {
    return parts
        .flatMap((part) => Array.isArray(part) ? part : [part])
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
}

function collectGlobalSearchResults(query) {
    const results = [];
    const knowledgeSource = typeof knowledgeData !== 'undefined' ? knowledgeData : (window.knowledgeData || []);
    const radarSource = typeof knowledgeRadar !== 'undefined' ? knowledgeRadar : (window.knowledgeRadar || []);
    const portfolioSource = typeof portfolioCases !== 'undefined' ? portfolioCases : (window.portfolioCases || []);
    const quizSource = typeof quizData !== 'undefined' ? quizData : (window.quizData || []);

    knowledgeSource.forEach((cat) => {
        cat.items.forEach((item) => {
            const text = getSearchableText([item.term, item.desc, item.details, item.code]);
            if (text.includes(query)) {
                results.push({
                    type: '知识库',
                    icon: 'book-open',
                    title: item.term,
                    desc: item.desc,
                    meta: cat.name,
                    view: 'knowledge',
                    action: () => {
                        AppState.currentKnowledgeCategory = cat.id;
                        switchView('knowledge');
                        renderKnowledgeMenu();
                        renderKnowledgeSearchResults(query);
                    }
                });
            }
        });
    });

    radarSource.forEach((item) => {
        const text = getSearchableText([item.name, item.domain, item.summary, item.why, item.actions, item.interview]);
        if (text.includes(query)) {
            results.push({
                type: '知识雷达',
                icon: 'radar',
                title: item.name,
                desc: item.summary,
                meta: `${item.domain} · 相关度 ${item.relevance || '-'}`,
                view: 'radar',
                action: () => switchView('radar')
            });
        }
    });

    portfolioSource.forEach((item) => {
        const text = getSearchableText([item.title, item.role, item.summary, item.stack, item.metrics, item.evidence, item.interview]);
        if (text.includes(query)) {
            results.push({
                type: '作品集',
                icon: 'briefcase-business',
                title: item.title,
                desc: item.summary,
                meta: item.role,
                view: 'portfolio',
                action: () => switchView('portfolio')
            });
        }
    });

    quizSource.forEach((item) => {
        const text = getSearchableText([item.question, item.category, item.difficulty, item.keyPoints, item.referenceAnswer]);
        if (text.includes(query)) {
            results.push({
                type: '面试题',
                icon: 'help-circle',
                title: item.question,
                desc: item.referenceAnswer || (item.keyPoints || []).join(' / '),
                meta: `${item.category || '通用'} · ${item.difficulty || '未分级'}`,
                view: 'quiz',
                action: () => switchView('quiz')
            });
        }
    });

    return results.slice(0, 24);
}

function setGlobalSearchActiveIndex(index) {
    const results = AppState.globalSearch.results || [];
    if (!results.length) {
        AppState.globalSearch.activeIndex = -1;
        return false;
    }

    const normalizedIndex = ((index % results.length) + results.length) % results.length;
    AppState.globalSearch.activeIndex = normalizedIndex;

    document.querySelectorAll('.global-search-result').forEach((btn) => {
        const isActive = Number(btn.dataset.searchIndex) === normalizedIndex;
        btn.classList.toggle('is-active', isActive);
        btn.setAttribute('aria-selected', String(isActive));
        btn.setAttribute('tabindex', isActive ? '0' : '-1');
        if (isActive) btn.scrollIntoView({ block: 'nearest' });
    });

    return true;
}

function moveGlobalSearchSelection(delta) {
    const results = AppState.globalSearch.results || [];
    if (!results.length) return false;
    const currentIndex = AppState.globalSearch.activeIndex >= 0 ? AppState.globalSearch.activeIndex : 0;
    return setGlobalSearchActiveIndex(currentIndex + delta);
}

function activateGlobalSearchSelection() {
    const results = AppState.globalSearch.results || [];
    if (!results.length) return false;
    const activeIndex = AppState.globalSearch.activeIndex >= 0 ? AppState.globalSearch.activeIndex : 0;
    const result = results[activeIndex];
    if (!result) return false;
    hideGlobalSearchPanel();
    result.action?.();
    return true;
}

function renderGlobalSearchPanel(query, results) {
    const panel = getGlobalSearchPanel();
    if (!panel) return;

    if (!query) {
        hideGlobalSearchPanel();
        return;
    }

    if (results.length === 0) {
        AppState.globalSearch.results = [];
        AppState.globalSearch.activeIndex = -1;
        panel.innerHTML = `
            <div class="global-search-empty">
                <i data-lucide="search-x"></i>
                <span>没有找到相关内容</span>
            </div>
        `;
        panel.classList.add('active');
        if (window.lucide) lucide.createIcons();
        return;
    }

    AppState.globalSearch.results = results;
    AppState.globalSearch.activeIndex = 0;

    panel.innerHTML = `
        <div class="global-search-summary">
            <span>${escapeHTML(query)}</span>
            <strong>${results.length} 个结果</strong>
        </div>
        <div class="global-search-results" role="listbox">
            ${results.map((item, index) => `
                <button class="global-search-result${index === 0 ? ' is-active' : ''}" type="button" data-search-index="${index}" role="option" aria-selected="${index === 0}" tabindex="${index === 0 ? '0' : '-1'}">
                    <i data-lucide="${item.icon}"></i>
                    <span>
                        <strong>${highlightSearchText(item.title, query)}</strong>
                        <small>${highlightSearchText(item.desc || '', query)}</small>
                        <em>${escapeHTML(item.type)} · ${escapeHTML(item.meta || '')}</em>
                    </span>
                </button>
            `).join('')}
        </div>
    `;

    panel.querySelectorAll('[data-search-index]').forEach((btn) => {
        btn.addEventListener('click', () => {
            setGlobalSearchActiveIndex(Number(btn.dataset.searchIndex));
            activateGlobalSearchSelection();
        });
    });
    panel.classList.add('active');
    if (window.lucide) lucide.createIcons();
}

function hideGlobalSearchPanel() {
    const panel = document.getElementById('global-search-panel');
    if (panel) {
        panel.classList.remove('active');
        panel.innerHTML = '';
    }
    AppState.globalSearch.results = [];
    AppState.globalSearch.activeIndex = -1;
}

function highlightSearchText(text, query) {
    const raw = String(text || '');
    if (!query) return escapeHTML(raw);
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return escapeHTML(raw).replace(regex, '<mark>$1</mark>');
}

function renderKnowledgeSearchResults(query) {
    const contentContainer = document.getElementById('k-content');
    if (!contentContainer) return;
    contentContainer.innerHTML = '';

    let matchCount = 0;
    const knowledgeSource = typeof knowledgeData !== 'undefined' ? knowledgeData : (window.knowledgeData || []);
    knowledgeSource.forEach((cat) => {
        cat.items.forEach((item) => {
            const textToSearch = getSearchableText([item.term, item.desc, item.details, item.code]);
            if (!textToSearch.includes(query)) return;

            matchCount += 1;
            const card = document.createElement('div');
            card.className = 'glass-card';
            card.style.marginBottom = '20px';
            const detailsHTML = item.details.map((detail) => `<div class="k-text-block">${highlightSearchText(detail, query)}</div>`).join('');
            const codeHTML = item.code ? `<pre class="code-block"><code>${highlightSearchText(item.code, query)}</code></pre>` : '';
            card.innerHTML = `
                <div class="k-card-title">
                    ${highlightSearchText(item.term, query)}
                    <span class="k-card-tag">${escapeHTML(cat.name)}</span>
                </div>
                <div class="k-subtitle" style="color:var(--text-secondary);font-weight:400;margin-bottom:16px;font-style:italic;">
                    ${highlightSearchText(item.desc, query)}
                </div>
                <div class="k-details-body">${detailsHTML}</div>
                ${codeHTML}
            `;
            contentContainer.appendChild(card);
        });
    });

    if (matchCount === 0) {
        contentContainer.innerHTML = `
            <div class="global-search-empty inline-empty">
                <i data-lucide="search-x"></i>
                <span>知识库中没有找到“${escapeHTML(query)}”</span>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
    }
}

function performGlobalSearch(query) {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
        hideGlobalSearchPanel();
        renderKnowledgeContent();
        return;
    }

    const results = collectGlobalSearchResults(normalized);
    renderGlobalSearchPanel(normalized, results);
    if (AppState.currentView === 'knowledge') {
        renderKnowledgeSearchResults(normalized);
    }
}

/* ==========================================================================
   INTERVIEW SIMULATOR 面试模拟器模块
   ========================================================================== */
function initQuizSimulator() {
    const categorySelect = document.getElementById('quiz-category-filter');
    const difficultySelect = document.getElementById('quiz-difficulty-filter');
    if (!categorySelect || !difficultySelect) return;
    
    const filterAndLoad = () => {
        const cat = categorySelect.value;
        const diff = difficultySelect.value;
        
        AppState.filteredQuizList = quizData.filter(q => {
            const catMatch = cat === 'all' || q.category === cat;
            const diffMatch = diff === 'all' || q.difficulty === diff;
            return catMatch && diffMatch;
        });
        
        AppState.currentQuizIndex = 0;
        renderQuizQuestion();
    };
    
    categorySelect.addEventListener('change', filterAndLoad);
    difficultySelect.addEventListener('change', filterAndLoad);
    
    // 初始化首载
    filterAndLoad();
}

function renderQuizQuestion() {
    const list = AppState.filteredQuizList;
    const index = AppState.currentQuizIndex;
    
    const cardBody = document.getElementById('quiz-question-container');
    const feedbackPanel = document.getElementById('quiz-feedback-panel');
    const nextBtn = document.getElementById('quiz-next-btn');
    const prevBtn = document.getElementById('quiz-prev-btn');
    const userAnswerBox = document.getElementById('quiz-user-answer');
    if (!cardBody || !feedbackPanel || !nextBtn || !prevBtn || !userAnswerBox) return;
    
    // 重置面板显隐
    feedbackPanel.style.display = 'none';
    userAnswerBox.value = '';
    
    // 重置评分高亮
    document.querySelectorAll('.score-btn').forEach(btn => btn.classList.remove('selected'));
    
    if (list.length === 0) {
        cardBody.innerHTML = `
            <div style="text-align:center;padding:30px;color:var(--text-muted);">
                <p>在此筛选组合下无对应面试真题，请切换筛选条件。</p>
            </div>
        `;
        document.getElementById('quiz-indicator').textContent = '0 / 0';
        nextBtn.style.opacity = '0.5';
        nextBtn.style.pointerEvents = 'none';
        prevBtn.style.opacity = '0.5';
        prevBtn.style.pointerEvents = 'none';
        return;
    }
    
    const item = list[index];
    
    // 渲染题目信息
    const difficultyLabel = item.difficulty === 'easy' ? '简单' : item.difficulty === 'medium' ? '中等' : '困难';
    const categoryName = (knowledgeData.find(c => c.id === item.category) || {name: '未知'}).name;
    
    cardBody.innerHTML = `
        <div class="question-meta">
            <span class="meta-badge difficulty-${item.difficulty}">${difficultyLabel}</span>
            <span class="badge-tag">${categoryName}</span>
        </div>
        <div class="question-text">${index + 1}. ${formatContent(item.question)}</div>
    `;
    
    // 更新页码指示
    document.getElementById('quiz-indicator').textContent = `${index + 1} / ${list.length}`;
    
    // 控制翻页按钮可用性
    prevBtn.style.opacity = index === 0 ? '0.4' : '1';
    prevBtn.style.pointerEvents = index === 0 ? 'none' : 'auto';
    
    nextBtn.style.opacity = index === list.length - 1 ? '0.4' : '1';
    nextBtn.style.pointerEvents = index === list.length - 1 ? 'none' : 'auto';
    
    // 渲染反馈面板内容
    document.getElementById('q-intent').innerHTML = formatContent(item.intent);
    document.getElementById('q-key-points').innerHTML = formatContent(item.key_points);
    document.getElementById('q-model-answer').innerHTML = formatContent(item.model_answer).replace(/\n/g, '<br>');
    document.getElementById('q-traps').innerHTML = formatContent(item.traps);
    
    // 如果已经打过分，回显分数
    if (AppState.stats.quizScores[item.id] !== undefined) {
        const score = AppState.stats.quizScores[item.id];
        const scoreBtn = document.querySelector(`.score-btn[data-score="${score}"]`);
        if (scoreBtn) scoreBtn.classList.add('selected');
        // 直接展开解析
        feedbackPanel.style.display = 'block';
    }
    
    // 渲染公式
    triggerMathRender(cardBody);
    triggerMathRender(feedbackPanel);
}

window.revealQuizAnswer = function() {
    const list = AppState.filteredQuizList;
    if (list.length === 0) return;
    
    const feedbackPanel = document.getElementById('quiz-feedback-panel');
    if (feedbackPanel) {
        feedbackPanel.style.display = 'block';
        feedbackPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
};

window.rateQuizScore = function(score) {
    const list = AppState.filteredQuizList;
    if (list.length === 0) return;
    
    const item = list[AppState.currentQuizIndex];
    
    // 选中按钮高亮
    document.querySelectorAll('.score-btn').forEach(btn => {
        if (parseInt(btn.getAttribute('data-score')) === score) {
            btn.classList.add('selected');
        } else {
            btn.classList.remove('selected');
        }
    });
    
    // 保存成绩
    AppState.stats.quizScores[item.id] = score;
    saveProgress();
};

window.nextQuiz = function() {
    if (AppState.currentQuizIndex < AppState.filteredQuizList.length - 1) {
        AppState.currentQuizIndex++;
        renderQuizQuestion();
    }
};

window.prevQuiz = function() {
    if (AppState.currentQuizIndex > 0) {
        AppState.currentQuizIndex--;
        renderQuizQuestion();
    }
};

/* ==========================================================================
   FLASHCARDS 卡片记忆模块 (支持精简版/深度面试版自由切换)
   ========================================================================== */
function initFlashcards() {
    AppState.flashcardsPool = [];
    knowledgeData.forEach(cat => {
        let itemIndex = 0;
        cat.items.forEach((item) => {
            const simpleAnswer = item.details[0] || item.desc || '暂无答案概要';
            
            let detailedAnswer = item.details.map(d => `<p style="margin-bottom:10px; line-height:1.6; text-align:justify;">${d}</p>`).join('');
            if (item.code) {
                detailedAnswer += `
                    <div style="margin-top:12px; text-align:left;">
                        <div style="font-size:0.75rem; color:var(--secondary); font-weight:600; margin-bottom:4px; font-family:'Outfit';">💡 代码实践及核心调参：</div>
                        <pre style="background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.06); padding:10px; border-radius:6px; font-family:'Courier New', monospace; font-size:0.8rem; overflow-x:auto; color:#cbd5e1; margin:0;"><code style="white-space:pre;">${escapeHTML(item.code)}</code></pre>
                    </div>
                `;
            }
            
            AppState.flashcardsPool.push({
                id: `${cat.id}_card_${itemIndex}`,
                category: cat.name,
                term: item.term,
                desc: item.desc,
                simpleAnswer: simpleAnswer,
                detailedAnswer: detailedAnswer
            });
            itemIndex++;
        });
    });
    
    if (!AppState.currentFlashcardVersion) {
        AppState.currentFlashcardVersion = 'simple';
    }
    
    AppState.currentFlashcardIndex = 0;
    renderFlashcard();
}

function renderFlashcard() {
    const pool = AppState.flashcardsPool;
    const index = AppState.currentFlashcardIndex;
    
    const cardEl = document.getElementById('flashcard-card');
    if (!cardEl) return;
    
    // 重置翻转
    cardEl.classList.remove('flipped');
    
    if (pool.length === 0) {
        document.getElementById('card-term').textContent = '暂无卡片数据';
        document.getElementById('card-details').textContent = '';
        document.getElementById('card-category-front').textContent = '';
        document.getElementById('card-category-back').textContent = '';
        return;
    }
    
    const item = pool[index];
    
    document.getElementById('card-category-front').innerHTML = formatContent(item.category);
    document.getElementById('card-category-back').innerHTML = formatContent(item.category);
    document.getElementById('card-term').innerHTML = formatContent(item.term);
    document.getElementById('card-desc').innerHTML = formatContent(item.desc);
    
    // 根据状态渲染对应的卡片版本内容
    const ver = AppState.currentFlashcardVersion || 'simple';
    const simpleBtn = document.getElementById('card-ver-simple-btn');
    const detailBtn = document.getElementById('card-ver-detail-btn');
    const detailsContainer = document.getElementById('card-details');
    
    if (ver === 'simple') {
        if (simpleBtn) simpleBtn.classList.add('active');
        if (detailBtn) detailBtn.classList.remove('active');
        if (detailsContainer) detailsContainer.innerHTML = formatContent(item.simpleAnswer).replace(/\n/g, '<br>');
    } else {
        if (simpleBtn) simpleBtn.classList.remove('active');
        if (detailBtn) detailBtn.classList.add('active');
        if (detailsContainer) detailsContainer.innerHTML = formatContent(item.detailedAnswer);
    }
    
    // 更新记忆进度指示
    document.getElementById('card-indicator').textContent = `${index + 1} / ${pool.length}`;
    
    // 按钮高亮与状态重置
    const masteredBtn = document.getElementById('card-mastered-btn');
    if (masteredBtn) {
        if (AppState.stats.masteredCards.includes(item.id)) {
            masteredBtn.classList.add('btn-primary');
            masteredBtn.classList.remove('btn-secondary');
            masteredBtn.innerHTML = `<i data-lucide="check-circle-2"></i> 已掌握`;
        } else {
            masteredBtn.classList.add('btn-secondary');
            masteredBtn.classList.remove('btn-primary');
            masteredBtn.innerHTML = `<i data-lucide="circle"></i> 标记为已掌握`;
        }
    }
    
    // 渲染公式
    triggerMathRender(cardEl);
    
    if (window.lucide) lucide.createIcons();
}

window.toggleFlipCard = function() {
    const cardEl = document.getElementById('flashcard-card');
    if (cardEl) cardEl.classList.toggle('flipped');
};

window.switchCardVersion = function(ver) {
    AppState.currentFlashcardVersion = ver;
    
    const pool = AppState.flashcardsPool;
    const index = AppState.currentFlashcardIndex;
    if (pool.length === 0) return;
    
    const item = pool[index];
    
    const simpleBtn = document.getElementById('card-ver-simple-btn');
    const detailBtn = document.getElementById('card-ver-detail-btn');
    const detailsContainer = document.getElementById('card-details');
    
    if (ver === 'simple') {
        if (simpleBtn) simpleBtn.classList.add('active');
        if (detailBtn) detailBtn.classList.remove('active');
        if (detailsContainer) detailsContainer.innerHTML = formatContent(item.simpleAnswer).replace(/\n/g, '<br>');
    } else {
        if (simpleBtn) simpleBtn.classList.remove('active');
        if (detailBtn) detailBtn.classList.add('active');
        if (detailsContainer) detailsContainer.innerHTML = formatContent(item.detailedAnswer);
    }
    
    // 渲染公式
    triggerMathRender(detailsContainer);
};

window.markCardMastered = function() {
    const pool = AppState.flashcardsPool;
    if (pool.length === 0) return;
    
    const item = pool[AppState.currentFlashcardIndex];
    const indexInMastered = AppState.stats.masteredCards.indexOf(item.id);
    
    if (indexInMastered > -1) {
        AppState.stats.masteredCards.splice(indexInMastered, 1);
        showNotification('已将该词条移出已掌握库');
    } else {
        AppState.stats.masteredCards.push(item.id);
        showNotification('恭喜！又掌握了一个核心考点！');
    }
    
    saveProgress();
    renderFlashcard();
};

window.nextCard = function() {
    if (AppState.flashcardsPool.length === 0) return;
    AppState.currentFlashcardIndex = (AppState.currentFlashcardIndex + 1) % AppState.flashcardsPool.length;
    renderFlashcard();
};

window.prevCard = function() {
    if (AppState.flashcardsPool.length === 0) return;
    AppState.currentFlashcardIndex = (AppState.currentFlashcardIndex - 1 + AppState.flashcardsPool.length) % AppState.flashcardsPool.length;
    renderFlashcard();
};

window.toggleMobileSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    if (!sidebar) return;
    const isOpen = sidebar.classList.toggle('open');
    if (backdrop) backdrop.classList.toggle('active', isOpen);
    document.body.classList.toggle('sidebar-lock', isOpen);
};

window.closeMobileSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    if (sidebar) sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('active');
    document.body.classList.remove('sidebar-lock');
};
