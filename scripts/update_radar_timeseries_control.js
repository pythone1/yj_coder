const fs = require('fs');
const vm = require('vm');

const path = 'js/radar.js';
const source = fs.readFileSync(path, 'utf8');
const ctx = { window: {} };
const current = vm.runInNewContext(`${source}\nknowledgeRadar;`, ctx);
const seen = new Set(current.map((item) => item.id));

const additions = [
  {
    id: 'time_series_foundation_models',
    name: 'Time-series Foundation Models',
    domain: '时序基础模型',
    horizon: '立即补',
    maturity: '快速落地',
    relevance: 96,
    summary: 'TimesFM、Chronos、TimeGPT 等把大规模预训练思想迁移到时间序列预测，支持 zero-shot/few-shot forecasting。',
    why: '你做水质 LSTM、污水厂负荷预测、养殖预警和碳源/曝气调优，时序基础模型是必须跟进的新路线。',
    actions: ['补 TimesFM/Chronos/TimeGPT 对比卡', '用水质数据做零样本预测实验', '比较 LSTM 与 foundation model 的 MAE/稳定性'],
    interview: '时序基础模型的价值是把跨行业时序模式预训练成通用表征，再用少量本地数据适配水质、能耗、药剂和负荷预测。',
    sources: [
      { label: 'Google TimesFM GitHub', url: 'https://github.com/google-research/timesfm' },
      { label: 'Amazon Chronos GitHub', url: 'https://github.com/amazon-science/chronos-forecasting' },
      { label: 'Nixtla TimeGPT docs', url: 'https://docs.nixtla.io/' }
    ]
  },
  {
    id: 'chronos_probabilistic_forecasting',
    name: 'Chronos / Probabilistic Forecasting',
    domain: '时序预测',
    horizon: '立即补',
    maturity: '可实践',
    relevance: 92,
    summary: '把时间序列数值 token 化，用语言模型式生成得到分位数和概率预测，而不是只给单点预测。',
    why: '水质预警和污水厂控制需要风险区间，概率预测比单点 LSTM 更适合提前量决策和安全冗余。',
    actions: ['补分位数预测指标 P50/P90', '在水质预警中输出置信区间', '用 pinball loss 评估预测区间'],
    interview: '生产控制场景不能只看点预测，我会输出分位数和置信区间，让运维策略能按风险等级决策。',
    sources: [
      { label: 'Chronos forecasting GitHub', url: 'https://github.com/amazon-science/chronos-forecasting' }
    ]
  },
  {
    id: 'timegpt_anomaly_forecasting',
    name: 'TimeGPT / Forecasting API',
    domain: '时序预测',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 89,
    summary: '面向业务时序的基础模型服务，支持预测、异常识别和外生变量等工程化调用方式。',
    why: '对求职作品集来说，TimeGPT 适合快速做水质、能耗、药剂消耗和传感器异常预测 baseline。',
    actions: ['做一组 TimeGPT baseline', '比较外生变量加入前后效果', '记录 API 成本与本地模型差异'],
    interview: '我会先用 TimeGPT 这类时序 foundation API 建 baseline，再决定是否需要本地 LSTM/Transformer 深度定制。',
    sources: [
      { label: 'Nixtla TimeGPT docs', url: 'https://docs.nixtla.io/' }
    ]
  },
  {
    id: 'tabpfn_tabular_foundation',
    name: 'TabPFN / Tabular Foundation Model',
    domain: '表格基础模型',
    horizon: '立即补',
    maturity: '可实践',
    relevance: 90,
    summary: '面向小中型表格数据的预训练分类/回归模型，常用于少样本 tabular baseline 和快速建模。',
    why: '你有很多水处理、养殖、遥感属性表和报告表格，TabPFN 可作为 LightGBM/RandomForest 之外的新 baseline。',
    actions: ['补 TabPFN vs LightGBM 对比卡', '选水质/药剂表格做回归实验', '记录小样本与大样本适用边界'],
    interview: '表格建模我不会只用 LightGBM，也会关注 TabPFN 这类 tabular foundation model，尤其适合小样本快速 baseline。',
    sources: [
      { label: 'TabPFN GitHub', url: 'https://github.com/PriorLabs/TabPFN' }
    ]
  },
  {
    id: 'causal_ml_intervention_effect',
    name: 'Causal ML for Intervention Effects',
    domain: '因果推断',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 91,
    summary: '用因果图、反事实、DML、因果森林等方法估计投药、曝气、换水、巡检等干预动作的真实效果。',
    why: '水厂和养殖项目不是只预测指标，还要回答“调这个参数会不会真的改善结果”，这需要因果推断。',
    actions: ['梳理曝气/碳源/水质因果图', '区分相关性预测与干预效果', '用 DoWhy/EconML 做小样本验证'],
    interview: '预测模型回答会发生什么，因果模型回答如果我调整曝气或投药会带来什么效果，两者不能混为一谈。',
    sources: [
      { label: 'DoWhy documentation', url: 'https://www.pywhy.org/dowhy/' },
      { label: 'EconML documentation', url: 'https://econml.azurewebsites.net/' }
    ]
  },
  {
    id: 'safe_bayesian_optimization',
    name: 'Safe Bayesian Optimization',
    domain: '安全优化',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 92,
    summary: '在未知或昂贵系统上寻找最优参数，同时显式约束安全边界，适合工艺参数和投加策略调优。',
    why: '污水厂碳源、曝气、药剂和养殖调控都不能试错越界，安全贝叶斯优化适合做保守自动调参。',
    actions: ['定义安全约束和目标函数', '用历史数据离线模拟 BO', '把建议动作设为人工确认'],
    interview: '我会用 Safe Bayesian Optimization 在安全约束内探索更优工艺参数，而不是让模型直接在现场盲目试错。',
    sources: [
      { label: 'BoTorch docs', url: 'https://botorch.org/' },
      { label: 'SafeOpt GitHub', url: 'https://github.com/befelix/SafeOpt' }
    ]
  },
  {
    id: 'digital_twin_mpc',
    name: 'Digital Twin + Model Predictive Control',
    domain: '智能控制',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 94,
    summary: '用机理模型、数据驱动模型和约束优化预测未来状态，在滚动时域内给出可执行控制建议。',
    why: '你已有污水厂、管网、养殖水质预测背景，MPC 是把预测模型变成控制决策的关键工程范式。',
    actions: ['补 MPC 滚动优化卡', '把 LSTM 预测输出接入约束优化', '设计碳源/曝气建议的 shadow-run 流程'],
    interview: 'MPC 的核心是滚动预测和约束优化：每个时刻根据最新状态重新求解未来一段时间的最优控制。',
    sources: [
      { label: 'GEKKO MPC documentation', url: 'https://gekko.readthedocs.io/en/latest/' },
      { label: 'do-mpc documentation', url: 'https://www.do-mpc.com/' }
    ]
  },
  {
    id: 'physics_informed_neural_operators',
    name: 'Physics-informed Neural Operators',
    domain: '科学机器学习',
    horizon: '下一批',
    maturity: '前沿',
    relevance: 88,
    summary: '用神经算子学习从边界条件、初始状态或参数场到解场的映射，服务流体、水文、扩散和污染传播建模。',
    why: '管网水动力、污染扩散和遥感环境过程都可从“纯黑箱预测”升级为结合物理约束的 surrogate model。',
    actions: ['补 FNO/DeepONet 概念卡', '整理水动力 surrogate 场景', '区分机理模型、数据模型和混合模型'],
    interview: '神经算子适合学习函数到函数的映射，可作为水动力或污染扩散模型的快速代理，但需要物理约束和外推验证。',
    sources: [
      { label: 'NeuralOperator docs', url: 'https://neuraloperator.github.io/dev/' },
      { label: 'NVIDIA PhysicsNeMo docs', url: 'https://docs.nvidia.com/physicsnemo/latest/' }
    ]
  },
  {
    id: 'swmm_ai_surrogate_modeling',
    name: 'SWMM + AI Surrogate Modeling',
    domain: '水系统建模',
    horizon: '立即补',
    maturity: '可实践',
    relevance: 93,
    summary: '用 SWMM 等机理模型生成或校准水动力过程，再用机器学习代理模型加速溯源、优化和实时预警。',
    why: '你的管网入流入渗和 SWMM 项目可升级为“机理仿真 + AI 代理 + 在线诊断”的更高阶表达。',
    actions: ['补 SWMM 机理-AI 混合卡', '整理模拟样本生成流程', '用代理模型加速异常入流定位'],
    interview: '我会把 SWMM 作为可信机理底座，用 AI surrogate 加速大量情景模拟，再把结果用于入渗入流诊断和调度优化。',
    sources: [
      { label: 'EPA SWMM', url: 'https://www.epa.gov/water-research/storm-water-management-model-swmm' }
    ]
  },
  {
    id: 'sensor_drift_quality_monitoring',
    name: 'Sensor Drift & Data Quality Monitoring',
    domain: '数据质量',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 90,
    summary: '监控传感器死值、漂移、尖峰、缺失、校准期和分布变化，保证时序预测和控制建议可信。',
    why: '水厂 SCADA、养殖 IoT 和遥感自动化产品都依赖数据质量；没有数据质量监控，模型再先进也会误导决策。',
    actions: ['定义死值/尖峰/漂移规则', '建立传感器健康分数', '把异常数据排除出训练和控制建议'],
    interview: '工业时序模型上线前先要做数据质量监控：死值、漂移、缺失、尖峰和校准期都要被识别并进入特征治理。',
    sources: [
      { label: 'Evidently data drift docs', url: 'https://docs.evidentlyai.com/' },
      { label: 'Great Expectations docs', url: 'https://docs.greatexpectations.io/' }
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
