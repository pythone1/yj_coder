# urban-drainage-source-apportionment (排水管网入流异常溯源系统)

## 📌 项目介绍
本系统主要用于大中型城市排水管网由于破损渗漏、雨污混接或非法工业废水注入而导致的异常流量追踪。通过分布式管网监测数据，解算逆水流溯源。

## 🛠️ 技术栈
- Python
- Storm Water Management Model (SWMM) API
- 遗传算法 (GA) / Adaptive Metropolis MCMC 采样

## 🌟 核心功能
- 对接管网拓扑结构，自动求解排水分区节点深度和流量。
- 基于后验概率采样估算异常注入的发生源头和注入水量强度，精度符合科研及工程要求。
