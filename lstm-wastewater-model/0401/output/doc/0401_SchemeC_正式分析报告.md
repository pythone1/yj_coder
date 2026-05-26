# 0401 Scheme C 正式分析报告

## 1. 当前试验对象
当前网络规模为 239 个节点、239 条连接，候选井 20 个，监测点 8 个。
当前监测方案为 J74, J78, J123, J126, J141, J139, J145, J231；真值注入点为 J76, J124, J140。
truth replay = 1.0000，SSE = 3.427e-30。

## 2. 当前结果
GA best mean NSE = 0.8343
posterior median NSE = 0.8255
posterior coverage mean = 0.8236
posterior top3 = J140, J124, J78

## 3. 当前代偿
J76-only mean NSE = -11.0581
J78-only mean NSE = -4.6710
J76 -> J78 替代 mean NSE = 0.8536
J140 -> J145 替代 mean NSE = 0.8395

## 4. 论文适用性
英文论文更偏 synthetic 条件下的 GA + AM 不确定性分析。
中文论文更偏工程应用、多监测点与实地监测。
当前 0401 项目是大网络、20 维份额反演、有限监测点条件下的可行性与代偿分析场景。