from pathlib import Path
import html
import re

PROJECT = Path(__file__).resolve().parent
OUT = PROJECT / "svg_output"
OUT.mkdir(exist_ok=True)
SPEC = PROJECT / "spec_lock.md"

W, H = 1280, 720

C = {
    "bg": "#F7FAFC",
    "bg_dark": "#062E5F",
    "panel": "#FFFFFF",
    "panel_soft": "#EEF6FB",
    "primary": "#0059B3",
    "primary_dark": "#003F7D",
    "accent": "#00A6D6",
    "orange": "#F28C28",
    "green": "#1F9D7A",
    "red": "#D84C4C",
    "text": "#102033",
    "light": "#FFFFFF",
    "secondary": "#5D7186",
    "border": "#B9D9ED",
    "line": "#6FAED7",
}

FONT = 'Microsoft YaHei, Arial, sans-serif'
TITLE_FONT = 'SimHei, Microsoft YaHei, sans-serif'


def esc(s):
    return html.escape(str(s), quote=True)


def tspans(text, x, y, size=22, fill=None, weight="400", width=30, lh=1.42, family=FONT, anchor=None):
    fill = fill or C["text"]
    lines = []
    buf = ""
    count = 0
    for ch in text:
        count += 1.0 if ord(ch) > 127 else 0.55
        if count > width and buf:
            lines.append(buf)
            buf = ch
            count = 1.0 if ord(ch) > 127 else 0.55
        else:
            buf += ch
    if buf:
        lines.append(buf)
    attrs = f'x="{x}" y="{y}" font-family=\'{family}\' font-size="{size}" fill="{fill}" font-weight="{weight}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    out = [f'<text {attrs}>']
    for i, line in enumerate(lines):
        dy = "0" if i == 0 else f"{size * lh:.1f}"
        out.append(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
    out.append("</text>")
    return "\n".join(out)


def text(x, y, s, size=22, fill=None, weight="400", family=FONT, anchor=None):
    fill = fill or C["text"]
    a = f'x="{x}" y="{y}" font-family=\'{family}\' font-size="{size}" fill="{fill}" font-weight="{weight}"'
    if anchor:
        a += f' text-anchor="{anchor}"'
    return f'<text {a}>{esc(s)}</text>'


def rect(x, y, w, h, fill, stroke=None, rx=0, sw=1, op=None):
    a = f'x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
    if stroke:
        a += f' stroke="{stroke}" stroke-width="{sw}"'
    if rx:
        a += f' rx="{rx}"'
    if op is not None:
        a += f' fill-opacity="{op}"'
    return f'<rect {a}/>'


def line(x1, y1, x2, y2, color=None, sw=2, dash=None):
    a = f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color or C["line"]}" stroke-width="{sw}"'
    if dash:
        a += f' stroke-dasharray="{dash}"'
    return f'<line {a}/>'


def image(name, x, y, w, h, mode="meet"):
    par = "xMidYMid meet" if mode == "meet" else "xMidYMid slice"
    return f'<image href="../images/{name}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="{par}"/>'


def arrow_defs(color=C["primary"]):
    return f'''<defs>
  <marker id="arrowHead" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L10,5 L0,10 Z" fill="{color}"/>
  </marker>
</defs>'''


def arrow(x1, y1, x2, y2, color=None, sw=3):
    color = color or C["primary"]
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}" marker-end="url(#arrowHead)"/>'


def header(title, page, subtitle=None):
    out = ['<g id="header">']
    out.append(rect(0, 0, W, 8, C["primary"]))
    out.append(rect(54, 42, 8, 42, C["primary"]))
    out.append(text(78, 74, title, 36, C["text"], "700", TITLE_FONT))
    if subtitle:
        out.append(text(78, 100, subtitle, 16, C["secondary"], "400"))
    out.append(text(1214, 74, f"{page:02d}", 18, C["primary_dark"], "700", FONT, "end"))
    out.append(line(78, 112, 1214, 112, C["border"], 1))
    out.append("</g>")
    return "\n".join(out)


def footer():
    return f'''<g id="footer">
  {text(54, 694, "AI供水管网DMA漏损检测｜杨佳负责部分", 12, C["secondary"])}
</g>'''


def slide(bg=C["bg"], body="", defs=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
{defs}
<g id="background">{rect(0,0,W,H,bg)}</g>
{body}
</svg>'''


def tag(x, y, label, color):
    return f'''<g id="tag-{re.sub("[^a-zA-Z0-9]+", "-", label)}">
  {rect(x, y, 156, 32, "#E8F5FB", C["border"], 8)}
  {text(x+78, y+22, label, 16, color, "700", FONT, "middle")}
</g>'''


def page01():
    body = ['<g id="cover-left">']
    body.append(rect(0, 0, W, H, C["bg_dark"]))
    body.append(rect(84, 130, 10, 430, C["accent"]))
    body.append(tspans("AI模型在供水管网DMA系统漏损检测中的应用", 122, 168, 48, C["light"], "700", 12, 1.18, TITLE_FONT))
    body.append(text(122, 340, "模型机理 · 算法选型 · 场景落地 · 持续运营", 23, C["accent"], "700"))
    body.append(text(122, 486, "聚焦杨佳负责内容：AI模型发展、核心算法与业务价值、实施路径。", 18, C["light"], "400"))
    body.append(text(122, 610, "对外汇报版", 16, C["accent"], "700"))
    body.append("</g>")
    body.append('<g id="cover-visual">')
    body.append(rect(710, 70, 500, 430, "#FFFFFF", None, 18))
    body.append(image("dma_ai_positioning_full.png", 730, 90, 460, 260, "meet"))
    body.append(text(760, 405, "DMA宏观锁定", 18, C["primary"], "700"))
    body.append(text(925, 405, "AI微观溯源", 18, C["green"], "700"))
    body.append(text(1085, 405, "工单闭环", 18, C["orange"], "700"))
    body.append(rect(760, 426, 120, 8, C["primary"]))
    body.append(rect(925, 426, 120, 8, C["green"]))
    body.append(rect(1085, 426, 100, 8, C["orange"]))
    body.append("</g>")
    return slide(C["bg_dark"], "\n".join(body))


def page02():
    items = [
        ("01", "供水AI模型发展", "从阈值规则、统计模型、机器学习到深度学习与智能体协同，解释技术演进与水务场景的结合逻辑。", C["primary"]),
        ("02", "核心算法与价值", "围绕时序预测、异常检测、水力融合与智能决策，说明算法解决的业务问题与输出结果。", C["green"]),
        ("03", "工程实施路径", "从规划、数据治理、模型建设、系统集成到长效运营，形成可复制的落地方法。", C["orange"]),
    ]
    body = [header("本部分解决三个问题", 2, "范围限定在 1.3、2.2 与第四部分实施路径")]
    xs = [70, 470, 870]
    for i, (num, title_s, desc, color) in enumerate(items):
        x = xs[i]
        body.append(f'<g id="scope-{i+1}">')
        body.append(rect(x, 166, 340, 360, C["panel"], C["border"], 14))
        body.append(rect(x, 166, 340, 58, color, None, 14))
        body.append(text(x+28, 204, num, 24, C["light"], "700"))
        body.append(text(x+82, 204, title_s, 24, C["light"], "700", TITLE_FONT))
        body.append(tspans(desc, x+30, 278, 22, C["text"], "400", 22))
        body.append(rect(x+30, 452, 280, 46, C["panel_soft"], C["border"], 8))
        body.append(text(x+170, 482, ["技术脉络", "算法映射", "落地闭环"][i], 20, color, "700", FONT, "middle"))
        body.append("</g>")
    body.append('<g id="bottom-line">')
    body.append(rect(104, 574, 1072, 54, "#EAF6FD", C["border"], 10))
    body.append(text(640, 609, "发展逻辑 → 算法能力 → 业务动作 → 运营机制", 25, C["primary_dark"], "700", TITLE_FONT, "middle"))
    body.append("</g>")
    body.append(footer())
    return slide(body="\n".join(body))


def page03():
    stages = [
        ("规则阈值", "夜间最小流量、上下限报警", "解释简单，但误报漏报高"),
        ("统计模型", "回归、ARIMA、控制图", "适合平稳数据，难应对非线性"),
        ("机器学习", "RF、GBT、孤立森林", "适合多变量特征与候选排序"),
        ("深度学习", "LSTM/GRU、自编码器", "适合高频时序与复杂模式"),
        ("智能体协同", "模型+知识+工具+工单", "把判断转为可执行流程"),
    ]
    body = [header("AI应用从规则判别走向闭环智能", 3, "1.3 供水管网AI模型应用的发展")]
    body.append('<g id="timeline">')
    body.append(line(112, 285, 1168, 285, C["line"], 3))
    for i, (a, b, c) in enumerate(stages):
        x = 120 + i * 260
        color = [C["primary"], C["accent"], C["green"], C["orange"], C["red"]][i]
        body.append(f'<g id="stage-{i+1}">')
        body.append(f'<circle cx="{x}" cy="285" r="34" fill="{color}"/>')
        body.append(text(x, 294, str(i+1), 24, C["light"], "700", FONT, "middle"))
        body.append(text(x-64, 365, a, 25, C["text"], "700", TITLE_FONT))
        body.append(tspans(b, x-88, 405, 18, C["text"], "400", 11))
        body.append(tspans(c, x-88, 486, 17, C["secondary"], "400", 12))
        body.append("</g>")
    body.append("</g>")
    body.append(rect(78, 600, 1124, 50, "#EAF6FD", C["border"], 8))
    body.append(text(640, 632, "演进主线：从“发现异常”提升到“解释原因、定位对象、推动处置”。", 22, C["primary_dark"], "700", FONT, "middle"))
    body.append(footer())
    return slide(body="\n".join(body))


def page04():
    body = [header("智能体组织算法与业务动作", 4, "智能体承担调度、调用和反馈，不替代底层算法")]
    body.append('<g id="left-visual">')
    body.append(rect(60, 150, 520, 420, C["panel"], C["border"], 16))
    body.append(image("ai_clean.png", 90, 178, 460, 345, "meet"))
    body.append("</g>")
    layers = [
        ("数据感知", "DMA流量、压力、SCADA、GIS、工单、管网属性"),
        ("模型推理", "预测残差、异常评分、候选管段概率、风险等级"),
        ("工具调用", "水力仿真、拓扑查询、巡检路径、派单系统"),
        ("反馈迭代", "现场核查、维修结果、误报标签、模型再训练"),
    ]
    body.append('<g id="agent-stack">')
    y = 150
    for i, (a, b) in enumerate(layers):
        color = [C["primary"], C["green"], C["orange"], C["accent"]][i]
        body.append(rect(640, y, 560, 78, C["panel"], C["border"], 12))
        body.append(rect(640, y, 10, 78, color, None, 12))
        body.append(text(674, y+32, a, 25, color, "700", TITLE_FONT))
        body.append(text(674, y+60, b, 18, C["text"], "400"))
        if i < 3:
            body.append(line(920, y+82, 920, y+105, C["line"], 2))
        y += 104
    body.append("</g>")
    body.append(rect(640, 590, 560, 52, "#EAF6FD", C["border"], 8))
    body.append(text(920, 624, "价值重点：把模型输出嵌入巡检、抢修与资产管理流程。", 21, C["primary_dark"], "700", FONT, "middle"))
    body.append(footer())
    return slide(body="\n".join(body))


def page05():
    cols = ["业务任务", "主要数据", "适配算法", "输出结果"]
    rows = [
        ("动态基线预测", "流量、压力时序", "LSTM / GRU", "预期值与残差"),
        ("异常识别", "高频传感器数据", "孤立森林 / DBSCAN / 自编码器", "异常评分与事件时间"),
        ("漏点定位", "拓扑、压力、仿真样本", "GA / RF / GBT", "候选管段与概率"),
        ("决策排序", "工单、管龄、材质、历史漏损", "知识图谱 / 集成学习", "巡检路径与改造优先级"),
    ]
    body = [header("算法选型取决于数据形态与业务动作", 5, "避免只按算法名称堆叠，按任务选择模型")]
    body.append('<g id="table">')
    x0, y0 = 72, 155
    widths = [250, 260, 330, 290]
    h = 70
    x = x0
    for i, col in enumerate(cols):
        body.append(rect(x, y0, widths[i], 54, [C["primary"], C["accent"], C["green"], C["orange"]][i], None, 0))
        body.append(text(x+18, y0+36, col, 21, C["light"], "700", TITLE_FONT))
        x += widths[i]
    for r, row in enumerate(rows):
        y = y0 + 54 + r*h
        x = x0
        for i, cell in enumerate(row):
            fill = C["panel"] if r % 2 == 0 else "#F1F7FB"
            body.append(rect(x, y, widths[i], h, fill, C["border"], 0))
            body.append(tspans(cell, x+18, y+29, 18 if i != 2 else 17, C["text"], "700" if i == 0 else "400", 15 if i != 2 else 20))
            x += widths[i]
    body.append("</g>")
    body.append(rect(72, 520, 1130, 76, "#EAF6FD", C["border"], 8))
    body.append(tspans("选型原则：先判断数据是否连续、标签是否充分、是否需要物理约束，再决定使用时序模型、无监督模型或机理融合模型。", 104, 552, 22, C["primary_dark"], "700", 46))
    body.append(footer())
    return slide(body="\n".join(body))


def page06():
    body = [header("DMA宏观锁定与AI微观溯源形成定位闭环", 6, "DMA指出高风险片区，AI将范围收敛到候选管段")]
    steps = [
        ("1 DMA分区计量", "夜间最小流量升高，先锁定疑似DMA片区"),
        ("2 多源数据融合", "流量、压力、拓扑、管龄、土壤、历史工单共同进入分析"),
        ("3 AI溯源分析", "水力模型与学习模型反向推演压力波动和流量重分布"),
        ("4 精准定位处置", "输出TopN候选管段、节点坐标、巡检与派单建议"),
    ]
    body.append('<g id="visual-main">')
    body.append(rect(60, 145, 570, 365, C["panel"], C["border"], 14))
    body.append(image("dma_ai_positioning_full.png", 76, 163, 538, 302, "meet"))
    body.append("</g>")
    body.append(arrow_defs())
    y = 150
    for i, (a, b) in enumerate(steps):
        color = [C["primary"], C["accent"], C["green"], C["orange"]][i]
        body.append(f'<g id="step-{i+1}">')
        body.append(rect(690, y, 500, 78, C["panel"], C["border"], 12))
        body.append(rect(690, y, 78, 78, color, None, 12))
        body.append(text(729, y+49, str(i+1), 27, C["light"], "700", FONT, "middle"))
        body.append(text(790, y+30, a[2:], 24, color, "700", TITLE_FONT))
        body.append(text(790, y+58, b, 17, C["text"], "400"))
        if i < 3:
            body.append(arrow(940, y+83, 940, y+101, C["primary"], 2))
        body.append("</g>")
        y += 108
    body.append(rect(96, 565, 1088, 50, "#EAF6FD", C["border"], 8))
    body.append(text(640, 598, "组合价值：把“哪个区可能漏”转化为“哪段管优先查、谁去查、结果如何回填”。", 22, C["primary_dark"], "700", FONT, "middle"))
    body.append(footer())
    return slide(body="\n".join(body), defs=arrow_defs())


def page07():
    body = ['<g id="section-bg">', rect(0, 0, W, H, C["bg_dark"]), '</g>']
    body.append('<g id="section-title">')
    body.append(text(78, 144, "PART 02", 22, C["accent"], "700"))
    body.append(tspans("适配管网漏损检测的核心AI技术及业务价值", 78, 220, 48, C["light"], "700", 17, 1.22, TITLE_FONT))
    body.append(text(78, 356, "时序异常检测 · 机理融合定位 · 多源决策闭环", 24, "#BFEAFF", "700"))
    body.append("</g>")
    xs = [118, 470, 822]
    labels = [("时序数据分析", "从流量压力中识别异常"), ("水力模型融合", "从异常收敛到候选管段"), ("智能决策技术", "从模型输出进入工单闭环")]
    for i, (a, b) in enumerate(labels):
        body.append(f'<g id="pillar-{i+1}">')
        body.append(rect(xs[i], 468, 300, 112, "#0B3B75", "#2C77AA", 14))
        body.append(text(xs[i]+24, 510, a, 25, C["light"], "700", TITLE_FONT))
        body.append(text(xs[i]+24, 546, b, 18, "#BFEAFF", "400"))
        body.append("</g>")
    body.append(text(1194, 640, "07", 16, "#BFEAFF", "700", FONT, "end"))
    return slide(C["bg_dark"], "\n".join(body))


def page08():
    body = [header("LSTM/GRU建立动态基线，识别夜间流量异常", 8, "2.2.1 时序数据分析与异常检测技术")]
    body.append('<g id="visual">')
    body.append(rect(58, 145, 680, 382, C["panel"], C["border"], 14))
    body.append(image("dynamic_baseline_full.png", 78, 168, 640, 320, "meet"))
    body.append("</g>")
    items = [
        ("输入", "DMA入口流量、压力、阀门状态、天气与节假日等外生变量"),
        ("学习", "捕捉昼夜周期、季节波动和短时突变，形成动态预测基线"),
        ("判别", "用实际值与预测值的残差识别异常，并设置分级阈值"),
        ("输出", "预警时间、异常强度、涉及DMA、后续排查优先级"),
    ]
    y = 150
    for i, (a, b) in enumerate(items):
        color = [C["primary"], C["accent"], C["green"], C["orange"]][i]
        body.append(f'<g id="point-{i+1}">')
        body.append(rect(780, y, 420, 76, C["panel"], C["border"], 10))
        body.append(text(804, y+31, a, 23, color, "700", TITLE_FONT))
        body.append(tspans(b, 866, y+30, 17, C["text"], "400", 25))
        body.append("</g>")
        y += 96
    body.append(rect(82, 580, 1118, 48, "#EAF6FD", C["border"], 8))
    body.append(text(640, 611, "业务价值：把固定阈值报警升级为随工况变化的动态预警。", 22, C["primary_dark"], "700", FONT, "middle"))
    body.append(footer())
    return slide(body="\n".join(body))


def page09():
    algs = [
        ("孤立森林", "随机切分数据空间，异常点更容易被快速隔离。", "适合高维SCADA流式异常初筛"),
        ("DBSCAN聚类", "用密度边界刻画正常运行簇，低密度点视为异常。", "适合识别局部运行状态漂移"),
        ("自编码器", "只学习正常模式，异常样本会产生更高重构误差。", "适合多变量联合异常识别"),
    ]
    body = [header("无监督异常检测适合低标签漏损场景", 9, "漏损样本少、人工标注难，先用无监督模型建立异常发现能力")]
    xs = [72, 462, 852]
    for i, (a, b, c) in enumerate(algs):
        color = [C["primary"], C["green"], C["orange"]][i]
        body.append(f'<g id="alg-{i+1}">')
        body.append(rect(xs[i], 150, 330, 392, C["panel"], C["border"], 14))
        body.append(rect(xs[i], 150, 330, 58, color, None, 14))
        body.append(text(xs[i]+24, 188, a, 26, C["light"], "700", TITLE_FONT))
        # mini visual
        cx, cy = xs[i]+165, 290
        if i == 0:
            for k in range(8):
                body.append(line(cx-90+k*22, cy-70, cx-45+k*20, cy+70, C["line"], 1))
            body.append(f'<circle cx="{cx+78}" cy="{cy+48}" r="12" fill="{C["red"]}"/>')
        elif i == 1:
            for dx, dy in [(-55,-20),(-30,-34),(-10,-10),(18,-25),(40,-8),(-42,28),(-15,35),(20,25),(72,50)]:
                body.append(f'<circle cx="{cx+dx}" cy="{cy+dy}" r="8" fill="{color}" fill-opacity="0.75"/>')
            body.append(f'<circle cx="{cx+98}" cy="{cy-60}" r="10" fill="{C["red"]}"/>')
        else:
            body.append(rect(cx-92, cy-54, 70, 108, "#EAF6FD", C["border"], 8))
            body.append(rect(cx+22, cy-54, 70, 108, "#EAF6FD", C["border"], 8))
            body.append(line(cx-22, cy, cx+22, cy, color, 4))
            body.append(f'<circle cx="{cx}" cy="{cy}" r="28" fill="{color}" fill-opacity="0.18" stroke="{color}" stroke-width="2"/>')
        body.append(tspans(b, xs[i]+28, 402, 20, C["text"], "400", 20))
        body.append(rect(xs[i]+28, 480, 274, 36, "#EAF6FD", C["border"], 8))
        body.append(text(xs[i]+165, 504, c, 16, color, "700", FONT, "middle"))
        body.append("</g>")
    body.append(footer())
    return slide(body="\n".join(body))


def page10():
    body = [header("水力模型融合把异常信号转化为候选管段", 10, "2.2.2 机器学习与水力模型融合技术")]
    body.append(arrow_defs())
    stages = [
        ("DMA异常", "流量、压力偏离"),
        ("水力校核", "GA校核水力参数"),
        ("仿真样本", "生成漏点压力特征"),
        ("学习匹配", "RF/GBT候选排序"),
        ("现场核查", "派单与复核回填"),
    ]
    x = 70
    for i, (a, b) in enumerate(stages):
        color = [C["primary"], C["accent"], C["green"], C["orange"], C["red"]][i]
        body.append(f'<g id="flow-{i+1}">')
        body.append(rect(x, 176, 188, 126, C["panel"], C["border"], 12))
        body.append(f'<circle cx="{x+34}" cy="216" r="22" fill="{color}"/>')
        body.append(text(x+34, 224, str(i+1), 20, C["light"], "700", FONT, "middle"))
        body.append(text(x+68, 212, a, 22, color, "700", TITLE_FONT))
        body.append(text(x+24, 260, b, 18, C["text"], "400"))
        if i < 4:
            body.append(arrow(x+194, 239, x+234, 239, C["primary"], 2))
        body.append("</g>")
        x += 236
    body.append('<g id="fusion-details">')
    details = [
        ("水力约束", "保持管网拓扑、节点压力与流向逻辑"),
        ("样本构造", "用仿真覆盖不同漏点位置和漏点面积"),
        ("概率排序", "用模型输出候选管段TopN，替代经验判断"),
    ]
    for j, (aa, bb) in enumerate(details):
        xx = 170 + j * 315
        body.append(rect(xx, 365, 290, 150, C["panel"], C["border"], 10))
        body.append(text(xx+24, 410, aa, 25, [C["primary"], C["green"], C["orange"]][j], "700", TITLE_FONT))
        body.append(tspans(bb, xx+24, 455, 19, C["text"], "400", 15))
    body.append("</g>")
    body.append(rect(80, 588, 1120, 48, "#EAF6FD", C["border"], 8))
    body.append(text(640, 619, "关键转化：从“发现异常”进入“候选管段排序”，减少无效开挖与盲查。", 22, C["primary_dark"], "700", FONT, "middle"))
    body.append(footer())
    return slide(body="\n".join(body), defs=arrow_defs())


def page11():
    cols = [("GA", "参数反演", C["primary"]), ("RF", "鲁棒分类", C["green"]), ("GBT/HGB", "高噪声排序", C["orange"])]
    rows = [
        ("适用输入", ["节点压力、管段粗糙度、背景漏失量", "仿真样本、压力降幅、流量方向", "高维节点压力、噪声样本、残差特征"]),
        ("核心输出", ["校核后的水力模型参数", "漏点管段概率分布", "候选节点搜索空间压缩"]),
        ("优势", ["全局寻优，适合非线性参数校核", "抗过拟合，部署解释性较强", "对复杂残差和噪声更敏感"]),
        ("注意点", ["收敛速度与约束设置影响结果", "依赖样本覆盖度和传感器布局", "需控制过拟合并持续验证漂移"]),
    ]
    body = [header("GA、RF、GBT分别解决校核、分类与高噪声排序", 11, "机理模型负责物理约束，机器学习负责快速匹配与排序")]
    x0, y0 = 190, 150
    for i, (a, b, color) in enumerate(cols):
        x = x0 + i*330
        body.append(rect(x, y0, 300, 66, color, None, 12))
        body.append(text(x+24, y0+32, a, 28, C["light"], "700"))
        body.append(text(x+88, y0+32, b, 22, C["light"], "700", TITLE_FONT))
    y = y0 + 82
    for r, (label, values) in enumerate(rows):
        body.append(text(72, y+35, label, 22, C["primary_dark"], "700", TITLE_FONT))
        for i, val in enumerate(values):
            x = x0 + i*330
            body.append(rect(x, y, 300, 70, C["panel"] if r%2==0 else "#F1F7FB", C["border"], 8))
            body.append(tspans(val, x+18, y+29, 17, C["text"], "400", 18))
        y += 84
    body.append(rect(190, 595, 960, 44, "#EAF6FD", C["border"], 8))
    body.append(text(670, 624, "落地原则：先可解释校核，再逐步叠加高精度模型。", 22, C["primary_dark"], "700", FONT, "middle"))
    body.append(footer())
    return slide(body="\n".join(body))


def page12():
    body = [header("多源数据融合支撑从预警到决策的业务闭环", 12, "2.2.3 大数据融合与智能决策技术")]
    body.append('<g id="visual">')
    body.append(rect(58, 144, 660, 380, C["panel"], C["border"], 14))
    body.append(image("data_training_full.png", 78, 164, 620, 330, "meet"))
    body.append("</g>")
    data = [
        ("SCADA", "流量、压力、水质、阀门状态"),
        ("GIS", "拓扑、管径、材质、标高"),
        ("运维工单", "报修、处置、回填、误报标签"),
        ("资产信息", "管龄、维修史、周边环境"),
        ("外部变量", "天气、节假日、施工扰动"),
    ]
    y = 146
    for i, (a, b) in enumerate(data):
        color = [C["primary"], C["accent"], C["green"], C["orange"], C["red"]][i]
        body.append(f'<g id="data-{i+1}">')
        body.append(rect(760, y, 420, 54, C["panel"], C["border"], 8))
        body.append(rect(760, y, 10, 54, color))
        body.append(text(786, y+34, a, 22, color, "700"))
        body.append(text(882, y+34, b, 17, C["text"], "400"))
        body.append("</g>")
        y += 68
    body.append(rect(760, 520, 420, 78, "#EAF6FD", C["border"], 8))
    body.append(tspans("知识图谱把管段、节点、事件、工单和资产关系串联起来，支撑巡检路径与改造优先级排序。", 786, 552, 19, C["primary_dark"], "700", 25))
    body.append(footer())
    return slide(body="\n".join(body))


def page13():
    body = [header("业务价值落在四类可执行动作", 13, "模型输出应进入运维动作并形成反馈闭环")]
    cx, cy = 640, 340
    body.append('<g id="cycle">')
    body.append(f'<circle cx="{cx}" cy="{cy}" r="92" fill="#EAF6FD" stroke="{C["border"]}" stroke-width="2"/>')
    body.append(tspans("漏损管控闭环", cx-58, cy-10, 25, C["primary_dark"], "700", 7, 1.25, TITLE_FONT))
    nodes = [
        (350, 200, "预警分级", "按异常强度和持续时间分级"),
        (850, 200, "定位优先级", "输出TopN候选管段和节点"),
        (850, 475, "巡检路径", "结合距离、风险和人员排班"),
        (350, 475, "改造排序", "按管龄、漏损频次和影响范围排序"),
    ]
    for i, (x, y, a, b) in enumerate(nodes):
        color = [C["primary"], C["green"], C["orange"], C["red"]][i]
        body.append(rect(x-140, y-48, 280, 96, C["panel"], C["border"], 12))
        body.append(text(x, y-10, a, 26, color, "700", TITLE_FONT, "middle"))
        body.append(text(x, y+24, b, 17, C["text"], "400", FONT, "middle"))
    body.append(line(490, 200, 548, 288, C["line"], 3))
    body.append(line(790, 200, 732, 288, C["line"], 3))
    body.append(line(790, 475, 732, 392, C["line"], 3))
    body.append(line(490, 475, 548, 392, C["line"], 3))
    body.append("</g>")
    body.append(rect(150, 606, 980, 42, "#EAF6FD", C["border"], 8))
    body.append(text(640, 634, "判断标准：每一个模型输出都要对应责任人、任务单、反馈字段和复盘机制。", 21, C["primary_dark"], "700", FONT, "middle"))
    body.append(footer())
    return slide(body="\n".join(body))


def page14():
    body = ['<g id="section-bg">', rect(0, 0, W, H, C["bg_dark"]), '</g>']
    body.append(text(78, 134, "PART 04", 22, C["accent"], "700"))
    body.append(tspans("实施路径：从试点验证到长效运营", 78, 210, 48, C["light"], "700", 17, 1.22, TITLE_FONT))
    body.append(text(78, 340, "规划边界 · 数据治理 · 模型建设 · 工程集成 · 运营保障", 24, "#BFEAFF", "700"))
    body.append(rect(626, 126, 540, 342, "#FFFFFF", None, 14))
    body.append(image("implementation_path.png", 646, 146, 500, 300, "meet"))
    body.append(text(1194, 640, "14", 16, "#BFEAFF", "700", FONT, "end"))
    return slide(C["bg_dark"], "\n".join(body))


def page15():
    body = [header("前期规划先明确目标与边界", 15, "4.1 前期规划：明确建设目标与实施边界")]
    items = [
        ("现状诊断", "盘点数据资产、硬件设备、SCADA/GIS/运维系统、漏损管控成效、DMA分区现状。"),
        ("目标设定", "短期降本增效，中期闭环管控，长期全生命周期管理。"),
        ("边界划定", "明确试点片区、设备范围、数据接口、验收指标和责任分工。"),
        ("推进策略", "试点先行、分步推广、持续迭代，形成可复制实施模板。"),
    ]
    body.append(arrow_defs())
    for i, (a, b) in enumerate(items):
        x = 80 + i*300
        color = [C["primary"], C["accent"], C["green"], C["orange"]][i]
        body.append(f'<g id="plan-{i+1}">')
        body.append(f'<circle cx="{x+80}" cy="205" r="42" fill="{color}"/>')
        body.append(text(x+80, 216, str(i+1), 30, C["light"], "700", FONT, "middle"))
        body.append(rect(x, 278, 240, 230, C["panel"], C["border"], 12))
        body.append(text(x+24, 326, a, 25, color, "700", TITLE_FONT))
        body.append(tspans(b, x+24, 374, 19, C["text"], "400", 14))
        if i < 3:
            body.append(arrow(x+206, 205, x+282, 205, C["line"], 2))
        body.append("</g>")
    body.append(rect(96, 570, 1088, 48, "#EAF6FD", C["border"], 8))
    body.append(text(640, 601, "规划输出的核心是试点边界、评价指标和推广路径。", 22, C["primary_dark"], "700", FONT, "middle"))
    body.append(footer())
    return slide(body="\n".join(body), defs=arrow_defs())


def page16():
    body = [header("数据治理决定模型上限", 16, "4.2 核心底座：多源数据融合与数据治理体系建设")]
    body.append('<g id="data-map">')
    body.append(rect(70, 150, 330, 360, C["panel"], C["border"], 14))
    for i, s in enumerate(["流量/压力/水质", "GIS拓扑/管网属性", "SCADA/运维工单", "巡检/维修/客服", "天气/施工/节假日"]):
        body.append(rect(102, 182+i*58, 266, 38, "#EAF6FD", C["border"], 8))
        body.append(text(235, 207+i*58, s, 18, C["primary_dark"], "700", FONT, "middle"))
    body.append("</g>")
    body.append('<g id="governance-pipeline">')
    phases = [("归集", "统一接入协议"), ("清洗", "缺失与异常处理"), ("标准", "编码与字段口径"), ("标签", "事件样本与回填"), ("服务", "API与模型特征库")]
    for i, (a, b) in enumerate(phases):
        x = 470 + i*140
        color = [C["primary"], C["accent"], C["green"], C["orange"], C["red"]][i]
        body.append(f'<circle cx="{x}" cy="260" r="42" fill="{color}"/>')
        body.append(text(x, 268, a, 22, C["light"], "700", TITLE_FONT, "middle"))
        body.append(tspans(b, x-48, 338, 17, C["text"], "400", 7, 1.2))
        if i < 4:
            body.append(line(x+46, 260, x+94, 260, C["line"], 3))
    body.append("</g>")
    body.append(rect(470, 430, 640, 90, C["panel"], C["border"], 12))
    body.append(tspans("数据中台的作用是打通数据孤岛，形成统一数据字典、共享机制与模型特征服务，减少重复建设。", 500, 466, 22, C["primary_dark"], "700", 34))
    body.append(footer())
    return slide(body="\n".join(body))


def page17():
    body = [header("模型建设采用“选型-训练-验证-上线-迭代”", 17, "4.3 AI算法模型的选型、训练与优化")]
    steps = [
        ("场景拆解", "预警、定位、排序、巡检分别定义输入与输出"),
        ("模型选型", "轻量模型优先，核心片区再叠加深度模型"),
        ("训练验证", "历史数据+仿真样本，加入噪声与丢包测试"),
        ("上线监控", "看准确率、误报率、响应时延与模型漂移"),
        ("反馈迭代", "维修结果与误报标签回流训练集"),
    ]
    body.append(arrow_defs())
    for i, (a, b) in enumerate(steps):
        x = 70 + i*236
        color = [C["primary"], C["accent"], C["green"], C["orange"], C["red"]][i]
        body.append(f'<g id="model-{i+1}">')
        body.append(rect(x, 170, 190, 250, C["panel"], C["border"], 12))
        body.append(rect(x, 170, 190, 54, color, None, 12))
        body.append(text(x+95, 205, a, 23, C["light"], "700", TITLE_FONT, "middle"))
        body.append(tspans(b, x+20, 270, 18, C["text"], "400", 12))
        body.append(text(x+95, 390, ["输入", "算法", "样本", "指标", "闭环"][i], 18, color, "700", FONT, "middle"))
        if i < 4:
            body.append(arrow(x+196, 292, x+228, 292, C["line"], 2))
        body.append("</g>")
    body.append(rect(110, 515, 1060, 70, "#EAF6FD", C["border"], 8))
    body.append(tspans("模型上线前必须验证真实工况：传感器噪声、通信丢包、拓扑误差和用水模式变化都会影响泛化能力。", 140, 548, 22, C["primary_dark"], "700", 46))
    body.append(footer())
    return slide(body="\n".join(body), defs=arrow_defs())


def page18():
    body = [header("工程落地以端边云协同承接实时性与算力", 18, "4.4 系统集成与场景化落地")]
    body.append('<g id="edge-cloud">')
    zones = [
        (70, 170, 300, 300, "端侧设备", "流量计、压力传感器、水听器、阀门、巡检设备", C["primary"]),
        (490, 170, 300, 300, "边缘节点", "实时采集、轻量AI识别、异常压缩上报、断点续传", C["green"]),
        (910, 170, 300, 300, "云端平台", "模型训练、融合分析、全局决策、工单集成", C["orange"]),
    ]
    body.append(arrow_defs())
    for i, (x, y, w, h, a, b, color) in enumerate(zones):
        body.append(f'<g id="zone-{i+1}">')
        body.append(rect(x, y, w, h, C["panel"], C["border"], 14))
        body.append(rect(x, y, w, 62, color, None, 14))
        body.append(text(x+24, y+40, a, 27, C["light"], "700", TITLE_FONT))
        if a == "云端平台":
            body.append(text(x+28, y+112, "模型训练、融合分析", 21, C["text"], "400"))
            body.append(text(x+28, y+148, "全局决策、工单集成", 21, C["text"], "400"))
        else:
            body.append(tspans(b, x+28, y+112, 21, C["text"], "400", 14))
        body.append("</g>")
    body.append(arrow(380, 320, 480, 320, C["line"], 3))
    body.append(arrow(800, 320, 900, 320, C["line"], 3))
    body.append(rect(138, 540, 1004, 56, "#EAF6FD", C["border"], 8))
    body.append(text(640, 575, "集成重点：兼容现有设备与SCADA/运维系统，避免新增数据孤岛。", 22, C["primary_dark"], "700", FONT, "middle"))
    body.append("</g>")
    body.append(footer())
    return slide(body="\n".join(body), defs=arrow_defs())


def page19():
    body = [header("长效运营把模型纳入常态运维", 19, "4.5 人员能力建设与运维保障体系")]
    body.append('<g id="visual">')
    body.append(rect(60, 150, 500, 320, C["panel"], C["border"], 14))
    body.append(image("workorder_no_person.png", 80, 170, 460, 270, "meet"))
    body.append("</g>")
    rows = [
        ("管理人员", "看目标、投资回报、指标闭环与风险责任"),
        ("技术人员", "看数据质量、模型参数、接口稳定与漂移监测"),
        ("运维人员", "看报警核查、现场处置、结果回填与标准动作"),
    ]
    y = 155
    for i, (a, b) in enumerate(rows):
        color = [C["primary"], C["green"], C["orange"]][i]
        body.append(f'<g id="role-{i+1}">')
        body.append(rect(620, y, 560, 78, C["panel"], C["border"], 12))
        body.append(rect(620, y, 10, 78, color))
        body.append(text(646, y+32, a, 24, color, "700", TITLE_FONT))
        body.append(text(770, y+32, b, 18, C["text"], "400"))
        body.append("</g>")
        y += 100
    body.append(rect(620, 482, 560, 86, "#EAF6FD", C["border"], 8))
    body.append(tspans("运维保障范围包括感知硬件校准、边缘网关维护、平台升级、模型版本管理、数据安全与权限控制。", 650, 518, 20, C["primary_dark"], "700", 33))
    body.append(footer())
    return slide(body="\n".join(body))


def page20():
    body = [header("收束：AI漏损检测的落地判断标准", 20, "最终判断不看模型名称，而看业务闭环是否成立")]
    body.append('<g id="conclusions">')
    items = [
        ("数据可信", "传感器在线、口径统一、标签可追溯，是模型准确的前提。", C["primary"]),
        ("模型可解释", "预警原因、候选管段、置信度和约束条件必须能够被运维人员理解。", C["green"]),
        ("闭环可执行", "报警要进入工单、现场核查要回填、模型要持续迭代。", C["orange"]),
    ]
    for i, (a, b, color) in enumerate(items):
        x = 95 + i*380
        body.append(f'<g id="conclusion-{i+1}">')
        body.append(rect(x, 180, 330, 240, C["panel"], C["border"], 14))
        body.append(f'<circle cx="{x+165}" cy="250" r="45" fill="{color}"/>')
        body.append(text(x+165, 260, str(i+1), 34, C["light"], "700", FONT, "middle"))
        body.append(text(x+165, 340, a, 30, color, "700", TITLE_FONT, "middle"))
        body.append(tspans(b, x+42, 382, 20, C["text"], "400", 18))
        body.append("</g>")
    body.append("</g>")
    body.append(rect(124, 514, 1032, 70, "#EAF6FD", C["border"], 8))
    body.append(tspans("核心结论：DMA提供宏观分区能力，AI提供动态识别、微观定位和闭环决策能力，两者结合才能形成可持续的漏损管控体系。", 160, 548, 22, C["primary_dark"], "700", 45))
    body.append(footer())
    return slide(body="\n".join(body))


PAGES = [
    ("01_cover.svg", page01),
    ("02_scope.svg", page02),
    ("03_ai_evolution.svg", page03),
    ("04_agent_stack.svg", page04),
    ("05_algorithm_selection.svg", page05),
    ("06_dma_ai_positioning.svg", page06),
    ("07_section_core_tech.svg", page07),
    ("08_lstm_gru_baseline.svg", page08),
    ("09_unsupervised_detection.svg", page09),
    ("10_hydraulic_fusion.svg", page10),
    ("11_ga_rf_gbt.svg", page11),
    ("12_data_decision.svg", page12),
    ("13_business_actions.svg", page13),
    ("14_section_implementation.svg", page14),
    ("15_planning_boundary.svg", page15),
    ("16_data_governance.svg", page16),
    ("17_model_building.svg", page17),
    ("18_edge_cloud_landing.svg", page18),
    ("19_operations.svg", page19),
    ("20_summary.svg", page20),
]


def main():
    for idx, (name, fn) in enumerate(PAGES, 1):
        SPEC.read_text(encoding="utf-8")
        svg = fn()
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote P{idx:02d} {name}")


if __name__ == "__main__":
    main()
