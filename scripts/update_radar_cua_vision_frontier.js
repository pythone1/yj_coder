const fs = require('fs');
const vm = require('vm');

const path = 'js/radar.js';
const source = fs.readFileSync(path, 'utf8');
const ctx = { window: {} };
const current = vm.runInNewContext(`${source}\nknowledgeRadar;`, ctx);
const seen = new Set(current.map((item) => item.id));

const additions = [
  {
    id: 'computer_use_agents',
    name: 'Computer Use Agents (CUA)',
    domain: '自动化执行',
    horizon: '立即补',
    maturity: '快速落地',
    relevance: 93,
    summary: '让模型通过截图、坐标、键鼠、浏览器和应用状态来完成真实 GUI 操作任务。',
    why: '求职助手后续要做网页投递、表单填写、简历导出和资料上传，CUA 是从“生成文本”走向“执行任务”的关键能力。',
    actions: ['定义浏览器/本地应用操作边界', '为投递任务加入人工确认', '记录每步截图和动作日志'],
    interview: 'Computer Use Agent 的核心不是能点鼠标，而是把观察、计划、动作、失败恢复和权限确认组织成可审计执行链。',
    sources: [
      { label: 'OpenAI computer use guide', url: 'https://platform.openai.com/docs/guides/tools-computer-use' }
    ]
  },
  {
    id: 'browser_use_workflows',
    name: 'Browser-use / Web Task Agents',
    domain: '浏览器 Agent',
    horizon: '立即补',
    maturity: '快速落地',
    relevance: 91,
    summary: '用浏览器自动化 Agent 完成网页检索、表单填写、页面理解、下载上传和多步骤 Web 工作流。',
    why: '岗位投递、JD 抓取、公司研究和作品集发布都发生在浏览器里，浏览器 Agent 是求职软件商业化关键模块。',
    actions: ['设计 JD 抓取和职位归档流程', '加入域名白名单和外发确认', '保存页面快照和证据链接'],
    interview: '我会把浏览器 Agent 用在可审计的 Web 工作流中：页面解析、表单动作、下载上传和失败恢复都要有日志。',
    sources: [
      { label: 'Browser Use docs', url: 'https://docs.browser-use.com/' }
    ]
  },
  {
    id: 'osworld_gui_benchmark',
    name: 'OSWorld / GUI Agent Benchmark',
    domain: '评测体系',
    horizon: '下一批',
    maturity: '新兴',
    relevance: 86,
    summary: '面向真实操作系统和桌面应用的多模态 Agent 基准，用任务完成率评估 GUI 操作能力。',
    why: '如果后续要做自动化办公和投递，不能只看模型回答，还要评估真实 GUI 任务是否完成。',
    actions: ['建立本地简历导出 GUI 评测任务', '记录成功率和失败原因', '区分网页任务与桌面任务'],
    interview: 'GUI Agent 评测要看任务完成率、动作轨迹、恢复能力和安全边界，而不是只看模型是否描述正确。',
    sources: [
      { label: 'OSWorld benchmark', url: 'https://os-world.github.io/' }
    ]
  },
  {
    id: 'ui_tars_gui_agents',
    name: 'UI-TARS / Native GUI Agents',
    domain: '多模态 Agent',
    horizon: '下一批',
    maturity: '前沿',
    relevance: 84,
    summary: '面向图形界面的视觉-动作模型，把屏幕理解、控件定位、动作生成和任务规划结合起来。',
    why: '你熟悉自动化办公和软件搭建，GUI Agent 能把本地桌面软件、浏览器和 GIS 工具串成更完整的自动化链路。',
    actions: ['补 GUI Agent 架构卡', '设计 QGIS/浏览器低风险演示任务', '把动作日志纳入安全审计'],
    interview: 'GUI Agent 的难点在于屏幕语义理解、控件定位、动作规划和错误恢复，必须和权限策略、沙箱和日志结合。',
    sources: [
      { label: 'UI-TARS GitHub', url: 'https://github.com/bytedance/UI-TARS' }
    ]
  },
  {
    id: 'pangaea_geo_benchmark',
    name: 'PANGAEA / Geospatial FM Benchmark',
    domain: '遥感评测',
    horizon: '立即补',
    maturity: '前沿',
    relevance: 92,
    summary: '面向地球观测基础模型的多任务评测，用统一基准比较分类、分割、变化检测和多源遥感能力。',
    why: '遥感基础模型越来越多，面试中要能讲清楚不只看模型名，还要看任务、数据集、迁移方式和评测指标。',
    actions: ['补遥感基础模型评测卡', '列出分类/分割/变化检测指标', '比较 Prithvi/Clay/AlphaEarth 使用场景'],
    interview: '评价 GeoAI 基础模型要看跨传感器、跨区域、少样本和下游任务表现，而不是只看预训练规模。',
    sources: [
      { label: 'PANGAEA benchmark', url: 'https://github.com/VMarsocci/pangaea-bench' }
    ]
  },
  {
    id: 'terramind_multimodal_eo',
    name: 'TerraMind / Multimodal EO Foundation Model',
    domain: '遥感基础模型',
    horizon: '下一批',
    maturity: '前沿',
    relevance: 90,
    summary: '多模态地球观测基础模型方向，强调跨光学、SAR、时序、文本和多任务遥感表征。',
    why: '你的遥感项目未来不应局限单一光学影像，SAR、DEM、水文、气象和文本报告都可成为模型输入。',
    actions: ['补多模态 EO 输入矩阵', '整理光学/SAR/DEM/气象融合场景', '设计水体和滩涂多源特征实验'],
    interview: '遥感基础模型的下一步是多模态：不同传感器和时序数据要在统一表征空间里服务分类、分割和变化分析。',
    sources: [
      { label: 'TerraMind paper', url: 'https://arxiv.org/abs/2504.11171' }
    ]
  },
  {
    id: 'dinov3_self_supervised_vision',
    name: 'DINOv3 / Self-supervised Vision Backbone',
    domain: '视觉基础模型',
    horizon: '立即补',
    maturity: '前沿',
    relevance: 91,
    summary: '自监督视觉骨干网络方向，通过大规模无标注图像学习通用特征，适合少样本迁移到分割、检测和遥感任务。',
    why: '你做的水体、建筑、池塘、工业缺陷都面临标注少的问题，自监督 backbone 是提升泛化能力的重要路线。',
    actions: ['补自监督视觉骨干卡', '对比 DINO/MAE/CLIP 特征', '设计少样本池塘分类实验'],
    interview: '自监督视觉模型的价值是用无标注数据学通用表征，再用较少标注迁移到遥感分割和目标检测任务。',
    sources: [
      { label: 'Meta DINOv3', url: 'https://github.com/facebookresearch/dinov3' }
    ]
  },
  {
    id: 'grounded_sam_pipeline',
    name: 'Grounded SAM / Open-vocabulary Segmentation',
    domain: '遥感视觉',
    horizon: '立即补',
    maturity: '可实践',
    relevance: 95,
    summary: '把开放词汇检测、文本提示定位和 SAM 分割组合起来，实现“按文字找对象并输出 mask”。',
    why: '这和你的养殖池塘、建筑、水体、排口、鸟类和江豚识别都高度相关，可把固定类别模型升级为文本驱动流程。',
    actions: ['整理 GroundingDINO + SAM 流程', '做水体/建筑/池塘文本提示样例', '记录误检和提示词优化策略'],
    interview: '开放词汇分割通常是先用文本提示定位候选框，再用 SAM 精细分割，最后做 GIS 后处理和人工校核。',
    sources: [
      { label: 'Grounded-SAM GitHub', url: 'https://github.com/IDEA-Research/Grounded-Segment-Anything' },
      { label: 'Grounding DINO GitHub', url: 'https://github.com/IDEA-Research/GroundingDINO' }
    ]
  },
  {
    id: 'sam2_video_geospatial',
    name: 'SAM 2 for Video & Temporal Geospatial',
    domain: '遥感视觉',
    horizon: '下一批',
    maturity: '可实践',
    relevance: 88,
    summary: 'SAM 2 的视频/时序分割能力可迁移到无人机视频、连续巡检和多时相遥感变化分析。',
    why: '你会无人机航测和水域巡查，时序分割能支持持续追踪水体、船只、鸟类、污染带和养殖设施变化。',
    actions: ['补 SAM 2 时序记忆机制卡', '设计无人机视频水体/鸟类分割 demo', '比较单帧 SAM 与时序 SAM'],
    interview: 'SAM 2 的关键是把分割从单张图扩展到有记忆的视频对象追踪，适合无人机巡检和连续变化监测。',
    sources: [
      { label: 'Meta SAM 2 GitHub', url: 'https://github.com/facebookresearch/sam2' }
    ]
  },
  {
    id: 'rf_detr_realtime_detection',
    name: 'RF-DETR / Real-time Transformer Detection',
    domain: '目标检测',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 87,
    summary: '实时 DETR 系列把 Transformer 检测器推向工业可用速度，适合与 YOLO 路线做对比。',
    why: '你的 Roboflow、鸟类、江豚、工业缺陷检测经历需要持续跟进检测器新路线，不只停留在 YOLO。',
    actions: ['补 YOLO vs DETR 对比卡', '记录实时检测指标 FPS/mAP/延迟', '选一个 Roboflow 数据集做路线对比'],
    interview: '目标检测我会按任务约束选模型：YOLO 强在成熟部署，DETR 系列强在端到端匹配和全局关系，最终看 mAP、延迟和误检类型。',
    sources: [
      { label: 'RF-DETR Roboflow', url: 'https://github.com/roboflow/rf-detr' }
    ]
  }
];

let added = 0;
for (const item of additions) {
  if (!seen.has(item.id)) {
    current.push(item);
    seen.add(item.id);
    added += 1;
  }
}

const prefix = 'const knowledgeRadar = ';
const start = source.indexOf(prefix);
const renderMarker = '\nconst radarFilterState =';
const renderStart = source.indexOf(renderMarker, start);
const end = renderStart === -1 ? -1 : source.lastIndexOf('\n]', renderStart);
if (start === -1 || end === -1 || renderStart === -1) {
  throw new Error('Unable to locate knowledgeRadar array boundary');
}

const beforeArray = source.slice(0, start);
const afterArray = source.slice(end + 2);
const nextSource = `${beforeArray}${prefix}${JSON.stringify(current, null, 4)};${afterArray}`;
fs.writeFileSync(path, nextSource, 'utf8');
console.log(JSON.stringify({ added, total: current.length }, null, 2));
