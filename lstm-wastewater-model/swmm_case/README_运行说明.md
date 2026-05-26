# 运行说明

## 推荐入口

如果你想在 PyCharm 里一键运行当前主线，并自动生成完整成果，请直接运行：

- [`run_final_pipeline.py`](/E:/PY/LSTM/swmm_case/run_final_pipeline.py)

这个入口会自动完成：

1. 中参数验证
2. posterior PPD 与收敛诊断生成
3. 最终汇报与真值对比可视化生成
4. 在控制台打印关键节点和核心指标

当前默认使用：

- 放大后的受控注水工况：`truth_scale_factor = 2.0`
- 小参数验证配置：便于在 PyCharm 中更快跑通

## 运行后的重点查看目录

结果目录：

- [`midscale_ppd`](/E:/PY/LSTM/swmm_case/paper_route_full_dim_results/midscale_ppd)

重点文件：

- [`项目最终汇报.md`](/E:/PY/LSTM/swmm_case/paper_route_full_dim_results/midscale_ppd/项目最终汇报.md)
- [`领导汇报总览.html`](/E:/PY/LSTM/swmm_case/paper_route_full_dim_results/midscale_ppd/领导汇报总览.html)
- [`truth_vs_prediction_map.html`](/E:/PY/LSTM/swmm_case/paper_route_full_dim_results/midscale_ppd/truth_vs_prediction_map.html)
- [`paper_posterior_ppd.html`](/E:/PY/LSTM/swmm_case/paper_route_full_dim_results/midscale_ppd/paper_posterior_ppd.html)
- [`paper_convergence_diagnostics.html`](/E:/PY/LSTM/swmm_case/paper_route_full_dim_results/midscale_ppd/paper_convergence_diagnostics.html)
- [`full_dim_summary.json`](/E:/PY/LSTM/swmm_case/paper_route_full_dim_results/midscale_ppd/full_dim_summary.json)
- [`full_dim_ga_population.csv`](/E:/PY/LSTM/swmm_case/paper_route_full_dim_results/midscale_ppd/full_dim_ga_population.csv)

## 核心脚本分工

- [`paper_route_full_dim.py`](/E:/PY/LSTM/swmm_case/paper_route_full_dim.py)
  当前核心算法实现，包含 `GA -> initial PPD -> AM` 主链路，以及详细中文注释。

- [`run_midscale_validation.py`](/E:/PY/LSTM/swmm_case/run_midscale_validation.py)
  中参数验证入口。

- [`build_posterior_paper_artifacts.py`](/E:/PY/LSTM/swmm_case/build_posterior_paper_artifacts.py)
  生成论文风格的 posterior PPD 和收敛诊断页面。

- [`build_final_leadership_report.py`](/E:/PY/LSTM/swmm_case/build_final_leadership_report.py)
  生成面向领导汇报的总览页、真值对比图和最终汇报文档。

## 输入文件

- [`case_dry.inp`](/E:/PY/LSTM/swmm_case/case_dry.inp)
- [`case_wet.inp`](/E:/PY/LSTM/swmm_case/case_wet.inp)
- [`inflow_templates.xlsx`](/E:/PY/LSTM/swmm_case/inflow_templates.xlsx)

## 目录保留原则

当前目录仅保留：

- 基础输入文件
- 主线算法脚本
- 最终结果目录
- 少量支撑分析结果

这样在 PyCharm 中打开后，结构已经足够清晰，便于查阅、运行和继续迭代。
