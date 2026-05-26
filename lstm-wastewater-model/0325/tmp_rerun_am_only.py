# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, r'E:\PY\LSTM\0325\代码')
from 公共配置与数据 import 实验配置, 结果目录
from 模型仿真与评估 import 构造实验数据, 目标函数评估器
from 遗传搜索与后验 import 运行AM, 提取后验结果

config = 实验配置()
dataset = 构造实验数据(config)
evaluator = 目标函数评估器(dataset, config)
init = pd.read_csv(结果目录 / '0325_initial_PPD.csv', encoding='utf-8-sig')
ga_hist = pd.read_csv(结果目录 / '0325_GA每代最佳.csv', encoding='utf-8-sig')
cols = list(config.候选节点)
ga_best_row = ga_hist.loc[ga_hist['best_mean_nse'].idxmax()]
ga_best = np.array([ga_best_row[c] for c in cols], dtype=float)

am_df = 运行AM(evaluator, init, config, seed=20260326)
posterior = 提取后验结果(am_df, config)
posterior_map = dict(zip(posterior['节点'], posterior['后验均值']))
posterior_mean = np.array([posterior_map[c] for c in cols], dtype=float)
posterior_mean = posterior_mean / posterior_mean.sum()
top_post_row = am_df.sort_values('log_posterior', ascending=False).iloc[0]
posterior_best = np.array([top_post_row[c] for c in cols], dtype=float)
posterior_best = posterior_best / posterior_best.sum()
summary = {
    'ga_best_mean_nse': float(evaluator.评估方案(ga_best)['mean_nse']),
    'posterior_mean_nse': float(evaluator.评估方案(posterior_mean)['mean_nse']),
    'posterior_best_nse': float(evaluator.评估方案(posterior_best)['mean_nse']),
    'accept_rate_by_chain': {str(k): float(v) for k, v in am_df.groupby('链号')['accepted'].mean().items()},
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
