# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
p = Path(r'E:\PY\LSTM\0325\结果')
init_df = pd.read_csv(p / '0325_initial_PPD.csv', encoding='utf-8-sig')
am = pd.read_csv(p / '0325_AM样本.csv', encoding='utf-8-sig')
post = pd.read_csv(p / '0325_后验节点权重.csv', encoding='utf-8-sig')
print('initial_ppd_size', len(init_df))
print('initial_ppd mean_nse min/max', float(init_df['mean_nse'].min()), float(init_df['mean_nse'].max()))
print('roulette weight sum', float(init_df['roulette_weight'].sum()))
print('am accept by chain')
print(am.groupby('链号')['accepted'].mean().to_string())
print('best posterior nse', float(am.sort_values('log_posterior', ascending=False).iloc[0]['mean_nse']))
print('best overall nse in am', float(am['mean_nse'].max()))
print('log stats top posterior rows')
print(am.sort_values('log_posterior', ascending=False)[['链号','步号','mean_nse','sse','log_prior','log_like','log_posterior']].head(8).to_string(index=False))
print('top posterior weights')
print(post.head(10).to_string(index=False))
