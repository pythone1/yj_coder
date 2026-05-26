< !DOCTYPE
html >
< html
lang = "zh-CN" >
< head >
< meta
charset = "UTF-8" >
< meta
name = "viewport"
content = "width=device-width, initial-scale=1.0" >
< title > 城市“生命线” —— AI
在内涝与进排水管网的应用图谱 < / title >
< script
src = "https://cdn.tailwindcss.com" > < / script >
< script
src = "https://cdn.jsdelivr.net/npm/chart.js" > < / script >
< style >
body
{
	font - family: 'Inter',
	-apple - system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans - serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
background - color:  # f8fafc;
color:  # 1e293b;
}

.chart - container
{
	position: relative;
width: 100 %;
margin - left: auto;
margin - right: auto;
height: 300
px;
max - height: 400
px;
}

@media(min - width

: 768
px) {
    .chart - container
{
	height: 350px;
}
}

.flow - arrow::after
{
	content: '▼';
display: block;
text - align: center;
color:  # 94a3b8;
margin: 0.5
rem
0;
}

@media(min - width

: 768
px) {
    .flow - arrow::after
{
	content: '▶';
display: inline - block;
margin: 0
1
rem;
}
}

.card - hover: hover
{
	transform: translateY(-2px);
box - shadow: 0
10
px
15
px - 3
px
rgba(0, 0, 0, 0.1);
}

/ *AI
Loading
Animation * /
.ai - loading
{
	display: inline - block;
width: 20
px;
height: 20
px;
border: 3
px
solid
rgba(59, 130, 246, 0.3);
border - radius: 50 %;
border - top - color:  # 3b82f6;
animation: spin
1
s
ease - in -out
infinite;
}

@keyframes


spin
{
	to
{transform: rotate(360deg);}
}
< / style >
< / head >
< body


class ="bg-slate-50 text-slate-800" >

< !-- Chosen
Palette: Slate / Blue / Teal(Professional, Water - themed, Calm) -->
< !-- Application
Structure
Plan:
1.
Hero
Section: High - level
summary.
2. ✨ Gemini
AI
Workspace: New
interactive
section
for AI generation and analysis.
	3.
	Interactive
	Solutions
	Matrix: Grid
	of
	the
	9
	directions.
4.
Simulation
Sandbox: Interactive
charts
with AI interpretation.
5.
Implementation
Roadmap: Timeline
view.
-->

< !-- Navigation -->
< nav


class ="bg-white border-b border-slate-200 sticky top-0 z-50" >

< div


class ="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" >

< div


class ="flex justify-between h-16" >

< div


class ="flex items-center" >

< span


class ="text-2xl font-bold text-blue-600 mr-2" > 💧 < / span >

< span


class ="font-bold text-xl tracking-tight text-slate-800" > 城市智慧水务 < / span >

< / div >
< div


class ="hidden md:flex items-center space-x-8" >

< button
onclick = "scrollToSection('ai-workspace')"


class ="text-blue-600 font-semibold transition" > ✨ AI 智慧中心 < / button >

< button
onclick = "scrollToSection('solutions')"


class ="text-slate-600 hover:text-blue-600 transition" > 应用场景 < / button >

< button
onclick = "scrollToSection('simulation')"


class ="text-slate-600 hover:text-blue-600 transition" > 价值模拟 < / button >

< button
onclick = "scrollToSection('roadmap')"


class ="text-slate-600 hover:text-blue-600 transition" > 落地路径 < / button >

< / div >
< / div >
< / div >
< / nav >

< !-- Header -->
< header


class ="bg-gradient-to-r from-slate-900 to-slate-800 text-white py-12 md:py-20" >

< div


class ="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center" >

< h1


class ="text-3xl md:text-5xl font-extrabold mb-6" > 城市“生命线”：AI 赋能内涝与管网 < / h1 >

< p


class ="text-lg md:text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed" >


利用 < strong > 实时数据融合 < / strong >、 < strong > 数字孪生 < / strong > 与 < strong > Gemini
大模型 < / strong >，构建具备感知、预警与自愈能力的智慧水务大脑。
< / p >
< / div >
< / header >

< !-- Section: ✨ Gemini
AI
Workspace -->
< section
id = "ai-workspace"


class ="py-16 bg-white border-b border-slate-200" >

< div


class ="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" >

< div


class ="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-3xl p-8 border border-blue-100 shadow-sm" >

< div


class ="flex items-center mb-6" >

< span


class ="text-3xl mr-3" > ✨ < / span >

< h2


class ="text-2xl font-bold text-slate-900" > Gemini AI 智慧中心 < / h2 >

< / div >

< div


class ="grid grid-cols-1 lg:grid-cols-2 gap-8" >

< !-- Diagnostic
Tool -->
< div


class ="space-y-4" >

< label


class ="block text-sm font-bold text-slate-700" > 城市供排水痛点诊断专家 < / label >

< textarea
id = "ai-input"
rows = "4"


class ="w-full p-4 rounded-xl border border-blue-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm" placeholder="描述您的城市遇到的具体问题，例如：某老旧城区排水管网每逢暴雨必涝，且存在不明渗漏..." > < / textarea >

< div


class ="flex gap-2" >

< button
onclick = "generateSolution()"
id = "gen-btn"


class ="flex-1 bg-blue-600 text-white font-bold py-3 rounded-xl hover:bg-blue-700 transition flex items-center justify-center gap-2" >

< span >✨ 生成方案建议 < / span >
< / button >
< button
onclick = "stopSpeech()"
id = "stop-speech-btn"


class ="hidden bg-red-100 text-red-600 p-3 rounded-xl hover:bg-red-200 transition" title="停止播报" >

🔇
< / button >
< / div >
< / div >

< !-- AI
Output
Area -->
< div


class ="bg-white rounded-2xl border border-blue-100 p-6 flex flex-col h-full min-h-[250px] relative overflow-hidden" >

< div
id = "ai-loading-overlay"


class ="hidden absolute inset-0 bg-white/80 z-10 flex flex-col items-center justify-center" >

< div


class ="ai-loading mb-4" > < / div >

< p


class ="text-sm font-medium text-blue-600" > Gemini 正在思考方案...< / p >

< / div >
< div
id = "ai-response-header"


class ="flex justify-between items-center mb-4 hidden border-b border-slate-50 pb-2" >

< span


class ="text-xs font-bold text-blue-600 uppercase tracking-widest" > 诊断报告 < / span >

< button
onclick = "speakOutput()"


class ="text-xs flex items-center gap-1 text-slate-500 hover:text-blue-600 transition" >

🔊 语音播报
< / button >
< / div >
< div
id = "ai-output"


class ="text-sm text-slate-600 leading-relaxed overflow-y-auto max-h-[300px]" >


请输入左侧的问题描述，点击生成方案。AI
将基于传感器融合、数字孪生和机器学习技术为您提供专业见解。
< / div >
< / div >
< / div >
< / div >
< / div >
< / section >

< !-- Section: Core
Logic
Flow -->
< section
id = "core-logic"


class ="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" >

< div


class ="text-center mb-12" >

< h2


class ="text-3xl font-bold text-slate-900" > 核心技术链路 < / h2 >

< p


class ="mt-4 text-lg text-slate-600" > 从数据采集到智能行动的闭环流程 < / p >

< / div >

< div


class ="bg-white rounded-2xl shadow-sm border border-slate-200 p-8" >

< div


class ="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 text-center md:text-left" >

< div


class ="flex-1 p-4 bg-blue-50 rounded-xl border border-blue-100 w-full md:w-auto" >

< div


class ="text-3xl mb-2" > 📡 < / div >

< h3


class ="font-bold text-blue-900 text-lg" > 全域感知 < / h3 >

< p


class ="text-sm text-blue-700 mt-2" > 雷达、传感器、业务数据 < / p >

< / div >
< div


class ="flow-arrow text-2xl" > < / div >

< div


class ="flex-1 p-4 bg-indigo-50 rounded-xl border border-indigo-100 w-full md:w-auto" >

< div


class ="text-3xl mb-2" > 🧠 < / div >

< h3


class ="font-bold text-indigo-900 text-lg" > 融合与孪生 < / h3 >

< p


class ="text-sm text-indigo-700 mt-2" > 数字孪生、LLM 智能分析 < / p >

< / div >
< div


class ="flow-arrow text-2xl" > < / div >

< div


class ="flex-1 p-4 bg-teal-50 rounded-xl border border-teal-100 w-full md:w-auto" >

< div


class ="text-3xl mb-2" > ⚡ < / div >

< h3


class ="font-bold text-teal-900 text-lg" > 智能决策 < / h3 >

< p


class ="text-sm text-teal-700 mt-2" > 分级预警、智能泵站控制 < / p >

< / div >
< / div >
< / div >
< / section >

< !-- Section: Interactive
Solutions
Matrix -->
< section
id = "solutions"


class ="py-16 bg-white border-t border-slate-200" >

< div


class ="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" >

< div


class ="mb-10 text-center" >

< h2


class ="text-3xl font-bold text-slate-900" > 9大应用方向深度解析 < / h2 >

< div


class ="flex flex-wrap justify-center gap-2 mt-8" >

< button
onclick = "filterCards('all')"


class ="filter-btn px-4 py-2 rounded-full bg-slate-800 text-white text-sm font-medium transition hover:bg-slate-700 ring-2 ring-offset-2 ring-slate-800 active-filter" > 全部展示 < / button >

< button
onclick = "filterCards('predict')"


class ="filter-btn px-4 py-2 rounded-full bg-slate-100 text-slate-600 text-sm font-medium transition hover:bg-blue-100 hover:text-blue-700" > 感知与预警 < / button >

< button
onclick = "filterCards('control')"


class ="filter-btn px-4 py-2 rounded-full bg-slate-100 text-slate-600 text-sm font-medium transition hover:bg-teal-100 hover:text-teal-700" > 调度与决策 < / button >

< button
onclick = "filterCards('maint')"


class ="filter-btn px-4 py-2 rounded-full bg-slate-100 text-slate-600 text-sm font-medium transition hover:bg-indigo-100 hover:text-indigo-700" > 运维与规划 < / button >

< / div >
< / div >
< div
id = "cards-grid"


class ="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" > < / div >

< / div >
< / section >

< !-- Section: Interactive
Simulations -->
< section
id = "simulation"


class ="py-16 bg-slate-50 border-t border-slate-200" >

< div


class ="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" >

< div


class ="text-center mb-12" >

< h2


class ="text-3xl font-bold text-slate-900" > AI 价值模拟沙盘 < / h2 >

< button
onclick = "analyzeSimulation()"


class ="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-full font-bold shadow-lg hover:bg-indigo-700 transition flex items-center justify-center gap-2 mx-auto" >

< span >✨ AI
深度解读当前数据 < / span >
< / button >
< / div >

< div


class ="grid grid-cols-1 lg:grid-cols-2 gap-8" >

< div


class ="bg-white rounded-xl shadow-lg p-6 border border-slate-100" >

< div


class ="flex justify-between items-center mb-4 border-b border-slate-100 pb-4" >

< h3


class ="text-xl font-bold text-slate-800" > 场景一：短时洪水 / 内涝预报 < / h3 >

< button
id = "toggle-forecast"


class ="bg-blue-600 text-white text-xs px-3 py-1 rounded shadow hover:bg-blue-700 transition" > 开启 AI 修正 < / button >

< / div >
< div


class ="chart-container" >

< canvas
id = "forecastChart" > < / canvas >
< / div >
< / div >

< div


class ="bg-white rounded-xl shadow-lg p-6 border border-slate-100" >

< div


class ="flex justify-between items-center mb-4 border-b border-slate-100 pb-4" >

< h3


class ="text-xl font-bold text-slate-800" > 场景二：智能泵站能效控制 < / h3 >

< input
type = "range"
id = "rain-intensity"
min = "1"
max = "10"
value = "5"


class ="w-24 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer" >

< / div >
< div


class ="chart-container" >

< canvas
id = "pumpChart" > < / canvas >
< / div >
< / div >
< / div >
< / div >
< / section >

< !-- Section: Implementation
Roadmap -->
< section
id = "roadmap"


class ="py-16 bg-white border-t border-slate-200" >

< div


class ="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center" >

< h2


class ="text-3xl font-bold text-slate-900 mb-12" > 落地实施路径 < / h2 >

< div


class ="grid grid-cols-1 md:grid-cols-3 gap-8" >

< div


class ="p-6 bg-slate-50 rounded-xl border border-slate-200" >

< div


class ="text-2xl font-bold text-blue-600 mb-4" > 1. 试点阶段 < / div >

< p


class ="text-sm text-slate-600" > 重点易涝点物联部署 + 基础报警闭环 < / p >

< / div >
< div


class ="p-6 bg-slate-50 rounded-xl border border-slate-200" >

< div


class ="text-2xl font-bold text-blue-600 mb-4" > 2. 提质阶段 < / div >

< p


class ="text-sm text-slate-600" > 全域数字孪生 + 强化学习控制策略 < / p >

< / div >
< div


class ="p-6 bg-slate-50 rounded-xl border border-slate-200" >

< div


class ="text-2xl font-bold text-blue-600 mb-4" > 3. 智慧阶段 < / div >

< p


class ="text-sm text-slate-600" > AI 机器人自动巡检 + 生成式 AI 调度辅助 < / p >

< / div >
< / div >
< / div >
< / section >

< footer


class ="bg-slate-900 text-slate-500 py-12 border-t border-slate-800 text-center" >

< p


class ="mb-2" > ✨ Powered by Gemini AI < / p >

< p


class ="text-xs" > 仅供科研与模拟演练使用 < / p >

< / footer >

< !-- JavaScript
Logic -->
< script >
const
apiKey = "";
const
appId = typeof
__app_id != = 'undefined' ? __app_id: 'smart-water-ai';
let
currentAudio = null;

// Gemini
API
with Exponential Backoff
async function
callGemini(prompt, systemInstruction="", type="text")
{
	const
url = `https: // generativelanguage.googleapis.com / v1beta / models / gemini - 2.5 - flash - preview - 0
9 - 2025: generateContent?key =${apiKey}
`;
const
payload = {
	contents: [{parts: [{text: prompt}]}],
	systemInstruction: {parts: [{text: systemInstruction}]}
};

for (let i = 0; i < 5; i++)
{
try {
const response = await fetch(url, {
method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify(payload)
});
if (!response.ok) throw new Error('API Error');
const data = await response.json();
return data.candidates?.[0]?.content?.parts?.[0]?.text;
} catch(e)
{
await new
Promise(r= > setTimeout(r, Math.pow(2, i) * 1000));
}
}
throw
new
Error('All retries failed');
}

// Gemini
TTS
with Exponential Backoff
async function callGeminiTTS(text) {
const url = `https://
	generativelanguage.googleapis.com / v1beta / models / gemini - 2.5 - flash - preview - tts: generateContent?key =${
	apiKey}
`;
const
payload = {
	contents: [{parts: [{text: "Say professionally: " + text}]}],
	generationConfig: {
responseModalities: ["AUDIO"],
speechConfig: {voiceConfig: {prebuiltVoiceConfig: {voiceName: "Aoede"}}}
}
};

for (let i = 0; i < 5; i++) {
	try {
	const response = await fetch(url, {
	method: 'POST',
	headers: {'Content-Type': 'application/json'},
body: JSON.stringify(payload)
});
if (!response.ok) throw new Error('TTS Error');
const data = await response.json();
const pcmData = data.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
return pcmData;
} catch(e)
{
await new
Promise(r= > setTimeout(r, Math.pow(2, i) * 1000));
}
}
return null;
}

// Convert
PCM
to
WAV
for playback
function pcmToWav(base64Pcm, sampleRate = 24000) {
const
binaryString = window.atob(base64Pcm);
const
len = binaryString.length;
const
bytes = new
Uint8Array(len);
for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);

const
buffer = new
ArrayBuffer(44 + len);
const
view = new
DataView(buffer);

const
writeString = (offset, string) = > {
for (let i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
};

writeString(0, 'RIFF');
view.setUint32(4, 32 + len, true);
writeString(8, 'WAVE');
writeString(12, 'fmt ');
view.setUint32(16, 16, true);
view.setUint16(20, 1, true);
view.setUint16(22, 1, true);
view.setUint32(24, sampleRate, true);
view.setUint32(28, sampleRate * 2, true);
view.setUint16(32, 2, true);
view.setUint16(34, 16, true);
writeString(36, 'data');
view.setUint32(40, len, true);

for (let i = 0; i < len; i++) view.setUint8(44 + i, bytes[i]);

return new
Blob([buffer], {type: 'audio/wav'});
}

async function
speakOutput()
{
const
text = document.getElementById('ai-output').innerText;
if (!text | | text.includes('请输入')) return;

const
pcm = await callGeminiTTS(text);
if (pcm) {
const wavBlob = pcmToWav(pcm);
const audioUrl = URL.createObjectURL(wavBlob);
if (currentAudio) currentAudio.pause();
currentAudio = new Audio(audioUrl);
currentAudio.play();
document.getElementById('stop-speech-btn').classList.remove('hidden');
currentAudio.onended = () = > document.getElementById('stop-speech-btn').classList.add('hidden');
}
}

function
stopSpeech()
{
if (currentAudio) {
currentAudio.pause();
document.getElementById('stop-speech-btn').classList.add('hidden');
}
}

// AI
Features
async function
generateSolution()
{
const
input = document.getElementById('ai-input').value;
if (!input) return;

const
loading = document.getElementById('ai-loading-overlay');
const
output = document.getElementById('ai-output');
const
header = document.getElementById('ai-response-header');

loading.classList.remove('hidden');

const
systemPrompt = `你是一位智慧城市水务专家。请根据用户提供的城市供排水痛点，结合以下九个维度给出专业的诊断和三条核心建议：
1.
短时洪水预报
2.
管网异常检测
3.
数字孪生
4.
泵站优化
5.
机器人巡检
6.
应急调度
7.
遥感识别
8.
社会感知
9.
长期规划。
输出语言为中文，风格专业且富有洞察力。`;

try {
const result = await callGemini(input, systemPrompt);
output.innerText = result;
header.classList.remove('hidden');
} catch (e) {
output.innerText = "生成方案时遇到错误，请稍后再试。";
} finally {
loading.classList.add('hidden');
}
}

async function
analyzeSimulation()
{
const
rainIntensity = document.getElementById('rain-intensity').value;
const
forecastMode = isAiForecast ? "AI 深度学习模式": "传统雷达外推模式";

const
loading = document.getElementById('ai-loading-overlay');
const
output = document.getElementById('ai-output');
const
header = document.getElementById('ai-response-header');

scrollToSection('ai-workspace');
loading.classList.remove('hidden');

const
prompt = `当前模拟沙盘参数：降雨强度 ${rainIntensity} / 10，预报模型：${
	forecastMode}。请分析这种状态下的城市安全风险，并给出一句简短的指挥口令。`;

try {
const result = await callGemini(prompt, "你是一位防汛指挥部首席分析师。");
output.innerText = result;
header.classList.remove('hidden');
} catch (e) {
output.innerText = "分析失败。";
} finally {
loading.classList.add('hidden');
}
}

// --- Original
Logic: Data & Visuals - --
const
directions = [
{id: 1, category: 'predict', icon: '🌦️', title: '短时洪水预报', desc: '利用 LSTM/Transformer 实现路段积水预报。',
 value: '价值：提前分级预警。'},
{id: 2, category: 'predict', icon: '🔍', title: '管网异常检测', desc: 'AI识别漏水、淤堵与溢流征兆。',
 value: '价值：减少环境污染。'},
{id: 3, category: 'control', icon: '🏙️', title: '数字孪生', desc: '构建“在线沙盘”，进行策略演练。',
 value: '价值：决策时间窗口最大化。'},
{id: 4, category: 'control', icon: '⚙️', title: '智能泵站控制', desc: '强化学习 (RL) 自动优化启停策略。',
 value: '价值：能效与安全平衡。'},
{id: 5, category: 'maint', icon: '🤖', title: '机器人巡检', desc: 'CV识别管道裂缝、沉降与侵蚀。',
 value: '价值：预测性维护减少突发事件。'},
{id: 6, category: 'control', icon: '🚑', title: '应急调度', desc: '优化抢险队伍与设备的最佳路径。',
 value: '价值：响应时间缩短。'},
{id: 7, category: 'predict', icon: '🛰️', title: '遥感风险识别', desc: 'LiDAR 识别流域易涝风险点。',
 value: '价值：精准高程数据输入。'},
{id: 8, category: 'predict', icon: '🤳', title: '社会感知', desc: 'NLP 处理市民上报的积水灾情。',
 value: '价值：覆盖传感器盲区。'},
{id: 9, category: 'maint', icon: '🏗️', title: '长期规划评估', desc: '模拟改造方案的成本效益。',
 value: '价值：科学指导基建投资。'}
];

const
gridEl = document.getElementById('cards-grid');
function
renderCards(filterType)
{
gridEl.innerHTML = '';
directions.forEach(item= > {
if (filterType === 'all' | | item.category == = filterType)
{
	const
card = document.createElement('div');
card.className = `bg - white
p - 6
rounded - xl
border
border - slate - 200
shadow - sm
card - hover
transition - all
duration - 300
flex
flex - col
`;
card.innerHTML = `
                 < div


class ="flex justify-between items-start mb-4" >

< div


class ="text-4xl bg-slate-50 p-2 rounded-lg" > ${item.icon} < / div >

< / div >
< h3


class ="text-lg font-bold text-slate-800 mb-2" > ${item.title} < / h3 >

< p


class ="text-sm text-slate-600 mb-4 flex-grow" > ${item.desc} < / p >

< div


class ="pt-4 border-t border-slate-100 text-xs font-semibold text-slate-500" > ${item.value} < / div >


`;
gridEl.appendChild(card);
}
});
}

function
filterCards(type)
{
	renderCards(type);
document.querySelectorAll('.filter-btn').forEach(btn= > {
if (btn.getAttribute('onclick').includes(type))
{
btn.classList.add('bg-slate-800', 'text-white');
btn.classList.remove('bg-slate-100', 'text-slate-600');
} else {
btn.classList.remove('bg-slate-800', 'text-white');
btn.classList.add('bg-slate-100', 'text-slate-600');
}
});
}

let
forecastChartInstance = null;
let
pumpChartInstance = null;
let
isAiForecast = false;

function
initCharts()
{
	const
ctxForecast = document.getElementById('forecastChart').getContext('2d');
const
labels = Array.
from

({length: 12}, (_, i) = > `${i * 10}min`);
const
actualRain = [5, 12, 25, 45, 60, 55, 40, 30, 20, 10, 5, 2];
const
tradForecast = [5, 8, 15, 25, 40, 50, 55, 45, 35, 20, 10, 5];
const
aiForecast = [5, 11, 24, 46, 62, 56, 39, 29, 21, 10, 4, 2];

forecastChartInstance = new
Chart(ctxForecast, {
	type: 'line',
	data: {
labels: labels,
datasets: [
	{label: '实际积水深度 (cm)', data: actualRain, borderColor: '#334155', fill: true, tension: 0.4},
	{label: '预测值', data: tradForecast, borderColor: '#94a3b8', borderDash: [5, 5], tension: 0.4}
]
},
options: {responsive: true, maintainAspectRatio: false}
});

document.getElementById('toggle-forecast').addEventListener('click', function()
{
	isAiForecast = !isAiForecast;
forecastChartInstance.data.datasets[1].data = isAiForecast ? aiForecast: tradForecast;
forecastChartInstance.data.datasets[1].label = isAiForecast ? "AI 融合预报": "传统预报";
forecastChartInstance.data.datasets[1].borderColor = isAiForecast ? "#2563eb": "#94a3b8";
this.textContent = isAiForecast ? "切换回传统": "开启 AI 修正";
forecastChartInstance.update();
});

const
ctxPump = document.getElementById('pumpChart').getContext('2d');
pumpChartInstance = new
Chart(ctxPump, {
	type: 'bar',
	data: {
labels: ['人工控制', 'AI 优化控制'],
datasets: [
	{label: '溢流风险', data: [80, 20], backgroundColor: '#ef4444', yAxisID: 'y'},
	{label: '能耗 (kWh)', data: [1200, 950], backgroundColor: '#0f766e', yAxisID: 'y1'}
]
},
options: {responsive: true, maintainAspectRatio: false}
});

document.getElementById('rain-intensity').addEventListener('input', function(e)
{
	const
val = parseInt(e.target.value);
pumpChartInstance.data.datasets[0].data = [val * 15, val * 3];
pumpChartInstance.data.datasets[1].data = [1000 + (val * 50), 800 + (val * 40)];
pumpChartInstance.update();
});
}

function
scrollToSection(id)
{document.getElementById(id).scrollIntoView({behavior: 'smooth'});}

document.addEventListener('DOMContentLoaded', () = > {
	renderCards('all');
initCharts();
});
< / script >
    < / body >
        < / html >