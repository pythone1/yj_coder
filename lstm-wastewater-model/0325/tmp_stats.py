# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'E:\PY\LSTM\0325\代码')
from 公共配置与数据 import 实验配置
from 模型仿真与评估 import 构造实验数据
config = 实验配置()
dataset = 构造实验数据(config)
cols = list(config.监测点)
vals = dataset.观测增量[cols].to_numpy().ravel()
print('n_obs', vals.size)
print('obs_mean', float(vals.mean()))
print('obs_std', float(vals.std()))
print('obs_var', float(vals.var()))
print('obs_abs_max', float(abs(vals).max()))
print('qr', dataset.Qr_m3)
