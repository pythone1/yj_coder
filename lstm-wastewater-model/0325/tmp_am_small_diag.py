# -*- coding: utf-8 -*-
import json
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, r'E:\PY\LSTM\0325\代码')
from 公共配置与数据 import 实验配置, 结果目录
from 模型仿真与评估 import 构造实验数据, 目标函数评估器
from 遗传搜索与后验 import 运行AM, 提取后验结果

config = 实验配置(am_链数=2, am_每链样本=60, am_预热=15, am_自适应起点=15, 并行工作进程数=2)
dataset = 构造实验数据(config)
evaluator = 目标函数评估器(dataset, config)
init = pd.read_csv(结果目录 / '0325_initial_PPD.csv', encoding='utf-8-sig')
am_df = 运行AM(evaluator, init, config, seed=20260401)
posterior = 提取后验结果(am_df, config)
summary = {
    'accept_rate_by_chain': {str(int(k)): float(v) for k, v in am_df.groupby('链号')['accepted'].mean().items()},
    'best_posterior_nse': float(am_df.sort_values('log_posterior', ascending=False).iloc[0]['mean_nse']),
    'best_overall_nse': float(am_df['mean_nse'].max()),
    'posterior_top5': posterior.head(5).to_dict(orient='records'),
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
