# 0401 Scheme C + J77 正式分析报告

## 1. 项目口径
- 当前网络规模：239 个节点、239 条连接，候选注入井 20 个，监测点 9 个。
- 当前监测点：J74, J77, J78, J123, J126, J141, J139, J145, J231。
- 真值注入点：J76, J124, J140。
- truth replay：Mean NSE = 1.0000，SSE = 4.127e-30。

## 2. 两轮中参数实验
- 上一轮 8 点方案：GA best = 0.8343，posterior median NSE = 0.8255，top3 = J140, J124, J78。
- 当前 9 点方案：GA best = 0.8313，posterior median NSE = 0.7654，posterior best NSE = 0.8111，top3 = J140, J124, J76。

## 3. 代偿分析
- J76→J78：上一轮 0.8536，当前 0.6849。
- J140→J145：上一轮 0.8395，当前 0.8573。
- 单点注入：J76-only = -11.3395，J78-only = -4.2372，J140-only = -0.1614，J145-only = -0.2365。

## 4. 论文对比
- 英文论文：19 pipes, school-scale synthetic UDS；3 monitoring sites (J6, J12, J19), plus 1-site control group G4；GA uses mean NSE across monitoring sites; performance reported by ACC, MCC, MAE。
- 中文论文：95 monitored manholes in the study area, 7 actual misconnected nodes；field water level monitoring at 95 inspection wells; optimization tests on 30/40/50/60/70 monitoring points；model-monitoring error based on water level / inferred flow mismatch, with node inflow optimization under hydraulic balance。
- 当前项目：239 节点大网、20 维份额反演、9 个监测点、总量与总波形固定的受控真值实验。