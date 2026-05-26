# -*- coding: utf-8 -*-
import json
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, r'E:\PY\LSTM\0325\代码')
from 公共配置与数据 import 实验配置, 结果目录
from 模型仿真与评估 import 构造实验数据, 目标函数评估器
from 遗传搜索与后验 import 运行AM, 提取后验结果

config = 实验配置(am_链数=2, am_每链样本=80, am_预热=20, 并行工作进程数=2)
dataset = 构造实验数据(config)
evaluator = 目标函数评估器(dataset, config)
init = pd.read_csv(结果目录 / '0325_initial_PPD.csv', encoding='utf-8-sig')
am_df = 运行AM(evaluator, init, config, seed=20260399)
posterior = 提取后验结果(am_df, config)
print('accept rates')
print(am_df.groupby('链号')['accepted'].mean().to_string())
print('best posterior nse', float(am_df.sort_values('log_posterior', ascending=False).iloc[0]['mean_nse']))
print('best overall nse', float(am_df['mean_nse'].max()))
print('top posterior')
print(posterior.head(8).to_string(index=False))
