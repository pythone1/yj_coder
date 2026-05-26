# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
p = Path(r'E:\PY\LSTM\0325\结果')
post = pd.read_csv(p / '0325_后验节点权重.csv', encoding='utf-8-sig')
am = pd.read_csv(p / '0325_AM样本.csv', encoding='utf-8-sig')
ga = pd.read_csv(p / '0325_GA每代最佳.csv', encoding='utf-8-sig')
print('ga best max', float(ga['best_mean_nse'].max()))
print('posterior top10')
print(post.head(10).to_string(index=False))
print('top posterior rows')
print(am.sort_values('log_posterior', ascending=False)[['链号','步号','mean_nse','sse','log_prior','log_like','log_posterior']].head(10).to_string(index=False))
print('accept by chain')
print(am.groupby('链号')['accepted'].mean().to_string())
