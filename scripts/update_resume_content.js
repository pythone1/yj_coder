const fs = require('fs');
const vm = require('vm');

const resumeJsPath = 'js/resume.js';
const resumeJsonPath = 'yang_jia_resume.json';
const resumeMdPath = 'yang_jia_resume.md';

const source = fs.readFileSync(resumeJsPath, 'utf8');
const data = vm.runInNewContext(`${source}\nresumeData;`);

const contact = {
  phone: '18115127540',
  email: 'cccccm21@gmail.com',
  targetSalary: '15K'
};

const profileTargets = {
  unicorn: 'AI算法工程师 / 遥感算法工程师',
  ai_llm: 'AI算法工程师 / 大模型应用工程师',
  rs_uav: '遥感算法工程师 / GIS与无人机航测工程师',
  data_engineer: 'AI数据工程师 / 遥感数据工程师'
};

for (const [key, profile] of Object.entries(data.profiles)) {
  if (!profile.personalInfo) continue;
  Object.assign(profile.personalInfo, contact);
  if (profileTargets[key]) profile.personalInfo.targetJob = profileTargets[key];
}

const unicorn = data.profiles.unicorn;
unicorn.title = '复合型AI算法与遥感算法工程师';
unicorn.themeColor = '#0f766e';

unicorn.sections.education = {
  show: true,
  title: '教育背景',
  items: [
    {
      period: '2016.09 - 2020.06',
      school: '南京工程学院',
      major: '车辆工程（本科）',
      gpa: '',
      courses: '主修课程：机械设计、C语言程序设计、单片机、汽车构造与设计。工作后长期围绕 Python、SQL、遥感/GIS、计算机视觉与AI工程化自学并落地项目。'
    }
  ]
};

unicorn.sections.workExperience = {
  show: true,
  title: '工作经历',
  items: [
    {
      period: '2021.07 - 至今',
      company: '南大五维电子科技有限公司',
      role: '研发中心人工智能事业部 · 算法工程师',
      highlights: [
        '**AI工程化与Vibe Coding**：深度使用 Claude Code、Codex、Antigravity、OpenClaw 等 AI 编程工具，将需求拆解、数据处理、模型训练、前后端工具、报告自动化与部署联动起来，能快速独立搭建可运行系统。',
        '**算法与平台栈**：主要使用 Python、SQL；常用 PyTorch、TensorFlow、scikit-learn、pandas/geopandas、OpenCV、GDAL；熟悉 Transformer、Segment Anything、YOLO、R-CNN、UNet、DeepLabv3、LSTM、LightGBM、Random Forest 等算法架构。',
        '**遥感与GIS全流程**：负责从数据采集、天地图/影像数据处理、样本集制备、模型训练调优、图斑后处理、专题图制图到 ArcGIS/QGIS/Omap 交付的完整链路；熟悉 QGIS Qt 工具开发。',
        '**计算机视觉落地**：围绕 SAM 分割、UNet/DeepLabv3 语义分割、YOLO/Roboflow 目标检测开展水体、建筑、养殖池塘、江豚、鸟类、工业尺寸与缺陷等识别任务，持续做精度调优、误检分析与样本迭代。',
        '**水环境与养殖AI**：自研水体 FUI、QA、DBWI（黑臭指数）等水色水质分析算法；搭建企业级大闸蟹养殖应用，用 LSTM 预测水质，并通过 RAG + 大模型建设养殖经验库和日常问答平台。',
        '**无人机与自动化交付**：可独立飞行大疆精灵4 RTK，熟悉 Pix4D 与大疆智图二维/三维拼接建模；熟悉图像膨胀腐蚀、指数计算、专题图版处理，并能通过企业微信推送遥感产品、自动填充报告。'
      ]
    },
    {
      period: '2020.07 - 2021.06',
      company: '好未来（学而思）',
      role: '高中物理辅导老师',
      highlights: [
        '**教学与班课辅导**：负责高中物理课程辅导、课堂答疑、作业讲评和学习计划跟进，能把复杂问题拆成学生能理解、能执行的步骤。',
        '**业绩表现**：教学结果和过程数据表现优秀，数据课程曾取得南京第一、全国第四；后因“双减”政策影响离开教育行业。'
      ]
    }
  ]
};

unicorn.sections.projects = {
  show: true,
  title: '项目经历',
  items: [
    {
      name: '江苏省养殖池塘上图入库与全省养殖信息数据库项目',
      period: '2021.10 - 2024.12',
      role: '主要开发者 / 遥感算法负责人',
      highlights: [
        '**项目目标**：面向江苏省养殖池塘上图入库，建设养殖图斑数据库与养殖信息底座，为池塘核查、空间管理、滩涂水域规划和后续监管提供统一数据基础。',
        '**核心算法**：使用 Segment Anything 进行养殖图斑精确提取，并结合水域指数、形态学膨胀腐蚀、非水域剔除、去重合并和人工校核流程，解决池塘边界复杂、连片水面误分割和跨图幅重复等问题。',
        '**工程流程**：搭建遥感影像预处理、样本集制备、模型训练、批量推理、矢量后处理、QGIS/ArcGIS 校核和成果入库链路，形成可复用的养殖池塘识别算法和数据生产流程。',
        '**成果价值**：沉淀全省养殖池塘空间数据库及养殖信息数据，支撑投标文件、验收材料和业务部门日常制图、统计、核查。'
      ]
    },
    {
      name: '渔小助企业级AI智慧养殖平台',
      period: '2023.05 - 2025.12',
      role: 'AI算法与平台开发',
      highlights: [
        '**水质预测**：基于大闸蟹养殖物联网数据，使用 LSTM 建立溶解氧、水温、pH、透明度等指标的时序预测模型，服务日常养殖预警和操作建议。',
        '**知识库问答**：基于 RAG + 大模型搭建企业级养殖经验库，覆盖病害排查、投喂建议、水质调控、日常操作指导等问答场景。',
        '**平台能力**：完成数据采集清洗、知识切片入库、检索增强、问答交互和运营资料自动化整理，使养殖经验从“靠人记”转向可检索、可复用。'
      ]
    },
    {
      name: 'AI+市政一厂一网与污水厂精准控制',
      period: '2024.09 - 至今',
      role: '算法方案与系统开发',
      highlights: [
        '**管网诊断**：围绕雨污混接、地下水入渗入流、河水倒灌和异常来水，结合 SCADA、在线水质、泵站、管网监测、降雨气象和工单数据，构建管网异常诊断与溯源分析流程。',
        '**水厂优化**：面向 COD、氨氮、总氮、总磷、水量波动等工况，使用 LSTM/TCN、异常识别、工艺决策模型和智能体，做碳源投加、曝气量、回流和药剂投加的精细调优。',
        '**落地场景**：已围绕八卦洲、射阳等水厂及“一厂一网”场景整理方案与算法链路，本地文档中水处理智能控制方案包含碳源节约、氨水/纯碱投加优化、膜污染预测与清洗决策等模块。'
      ]
    },
    {
      name: '云南楚雄滇中有色AI水处理与膜具清洗优化',
      period: '2024.11 - 2025.06',
      role: '水处理AI算法开发',
      highlights: [
        '**膜污染预测**：基于膜压差、产水通量、水质变量等运行数据，建立膜污染趋势预测与清洗决策逻辑，辅助判断清洗时机和清洗方案。',
        '**药剂与除磷优化**：围绕锅炉给水、深度水处理硬度控制和除磷模块，建立投加量计算与运行建议模型，目标是降低氨水、纯碱等药剂消耗并稳定出水指标。',
        '**工程交付**：将机理理解、时序数据建模和现场工艺约束结合，形成面向生产运行人员的 AI 决策辅助模块。'
      ]
    },
    {
      name: '养殖滩涂水域规划与遥感专题制图',
      period: '2022.06 - 至今',
      role: '遥感算法与GIS制图',
      highlights: [
        '**规划支撑**：基于遥感影像、养殖池塘图斑、岸线与水域空间数据，完成滩涂养殖、水域利用和区域空间分布分析。',
        '**技术方法**：使用 ArcGIS/QGIS 完成投影转换、空间叠加、缓冲分析、面积统计、专题图版处理和报告图件输出。',
        '**业务价值**：为养殖区域摸底、空间管控、投标材料和管理部门汇报提供可视化数据产品。'
      ]
    },
    {
      name: '江苏各地断面水质溯源遥感分析',
      period: '2022.01 - 至今',
      role: '遥感算法工程师',
      highlights: [
        '**遥感反演**：围绕重点断面、水体颜色、水质异常和黑臭风险，使用 FUI、QA、DBWI 等算法生成水色与水质专题产品。',
        '**溯源分析**：结合断面位置、河网、水体指数、排口/养殖/建设用地等空间要素，辅助判断异常水质可能来源和巡查优先级。',
        '**自动化推送**：通过企业微信等渠道推送遥感产品和分析结果，并将图件、统计表和报告片段自动化生成，降低人工制图和日报周报成本。'
      ]
    },
    {
      name: 'Roboflow全栈目标检测与工业视觉应用',
      period: '2023.09 - 至今',
      role: '计算机视觉算法开发',
      highlights: [
        '**生态识别**：基于 Roboflow 完成数据标注、增强、训练、评估和部署链路，开展江豚识别、鸟类识别等生态目标检测任务。',
        '**工业检测**：面向工业尺寸测量和缺陷检测，构建样本集、训练检测模型并进行误检复盘，支持视觉检测从原型验证到业务试用。',
        '**复用能力**：形成“采集-标注-训练-评估-部署-迭代”的通用 CV 流程，可迁移到遥感、水生态、工业质检等场景。'
      ]
    }
  ]
};

unicorn.sections.skills = {
  show: true,
  title: '核心技能',
  items: [
    {
      category: 'AI开发与工程化',
      list: 'Claude Code、Codex、Antigravity、OpenClaw、Vibe Coding、RAG、智能体工作流、需求拆解、自动化报告、企业微信推送。'
    },
    {
      category: '编程语言与数据处理',
      list: 'Python、SQL、pandas、geopandas、NumPy、OpenCV、GDAL、矢量/栅格处理、时序数据清洗、样本集制备。'
    },
    {
      category: '深度学习与机器学习',
      list: 'PyTorch、TensorFlow、scikit-learn、Transformer、SAM、YOLO、R-CNN、UNet、DeepLabv3、LSTM、LightGBM、Random Forest。'
    },
    {
      category: '遥感/GIS/无人机',
      list: 'AI Earth、ArcGIS、QGIS、Omap、QGIS Qt工具开发、Pix4D、大疆智图、精灵4 RTK、遥感预处理、专题制图、空间数据库。'
    },
    {
      category: '水环境与养殖算法',
      list: 'FUI、QA、DBWI黑臭指数、水色水质分析、养殖池塘提取、断面溯源、水质LSTM预测、污水厂碳源/曝气/药剂优化。'
    }
  ]
};

unicorn.sections.awards = {
  show: false,
  title: '专业资格',
  items: []
};

unicorn.sections.selfEvaluation = {
  show: true,
  title: '自我评价',
  text: '做事可靠，能把不清晰的业务需求拆成数据、算法、工具和交付物，持续推进到可运行、可复盘。长期深度使用 Claude Code、Codex、Antigravity 等 AI 开发工具，保持高强度学习和快速试错能力；在 AI 技术每天变化的环境里，会主动跟进新模型、新平台和新工程范式，并把它们落到遥感、养殖、水处理和工业视觉的真实项目中。'
};

function cleanMarkdown(text) {
  return String(text || '').replace(/\*\*/g, '');
}

function renderMarkdown(profile) {
  const info = profile.personalInfo;
  const sections = profile.sections;
  const lines = [];

  lines.push(`# ${info.name}`);
  lines.push('');
  lines.push(`- **求职岗位**：${info.targetJob}`);
  lines.push(`- **目标薪资**：${info.targetSalary}`);
  lines.push(`- **联系电话**：${info.phone}`);
  lines.push(`- **电子邮箱**：${info.email}`);
  lines.push(`- **基本信息**：${info.age}｜${info.gender}｜${info.hometown}｜${info.experience}`);
  lines.push('');

  for (const key of ['education', 'workExperience', 'projects', 'skills', 'selfEvaluation']) {
    const section = sections[key];
    if (!section || section.show === false) continue;
    lines.push(`## ${section.title}`);
    lines.push('');

    if (key === 'education') {
      for (const item of section.items) {
        lines.push(`### ${item.school}（${item.period}）`);
        lines.push(`- ${item.major}`);
        if (item.courses) lines.push(`- ${item.courses}`);
        lines.push('');
      }
    } else if (key === 'workExperience') {
      for (const item of section.items) {
        lines.push(`### ${item.company}（${item.period}）`);
        lines.push(`**${item.role}**`);
        for (const h of item.highlights) lines.push(`- ${cleanMarkdown(h)}`);
        lines.push('');
      }
    } else if (key === 'projects') {
      for (const item of section.items) {
        lines.push(`### ${item.name}（${item.period}）`);
        lines.push(`**${item.role}**`);
        for (const h of item.highlights) lines.push(`- ${cleanMarkdown(h)}`);
        lines.push('');
      }
    } else if (key === 'skills') {
      for (const item of section.items) {
        lines.push(`- **${item.category}**：${item.list}`);
      }
      lines.push('');
    } else if (key === 'selfEvaluation') {
      lines.push(section.text);
      lines.push('');
    }
  }

  return `${lines.join('\n').replace(/\n{3,}/g, '\n\n').trim()}\n`;
}

fs.writeFileSync(resumeJsPath, `const resumeData = ${JSON.stringify(data, null, 4)};\n`, 'utf8');
fs.writeFileSync(resumeJsonPath, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
fs.writeFileSync(resumeMdPath, renderMarkdown(unicorn), 'utf8');

console.log('Updated resume content:', {
  profile: unicorn.title,
  projects: unicorn.sections.projects.items.length,
  workItems: unicorn.sections.workExperience.items.length,
  skills: unicorn.sections.skills.items.length
});
