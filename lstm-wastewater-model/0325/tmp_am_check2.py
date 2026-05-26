# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
p = Path(r'E:\PY\LSTM\0325\结果')
am = pd.read_csv(p / '0325_AM样本.csv', encoding='utf-8-sig')
init_df = pd.read_csv(p / '0325_initial_PPD.csv', encoding='utf-8-sig')
print('initial_ppd_size', len(init_df))
print('accept rate by chain')
print(am.groupby('链号')['accepted'].mean().to_string())
print('accept prob stats', am['accept_prob'].describe().to_string())
print('best posterior rows')
print(am.sort_values('log_posterior', ascending=False)[['链号','步号','mean_nse','sse','log_prior','log_like','log_posterior','accept_prob']].head(10).to_string(index=False))
print('best mean_nse overall', am['mean_nse'].max())
print('unique rows in chain1', am[am['链号']==1][['mean_nse','sse','log_posterior']].drop_duplicates().shape[0])
