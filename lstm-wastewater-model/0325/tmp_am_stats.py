# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
p = Path(r'E:\PY\LSTM\0325\结果')
am = pd.read_csv(next(p.glob('0325_AM*.csv')), encoding='utf-8-sig')
print(am[['mean_nse','sse','log_prior','log_like','log_posterior']].describe())
print('best posterior rows')
print(am.sort_values('log_posterior', ascending=False)[['链号','步号','mean_nse','sse','log_prior','log_like','log_posterior']].head(10).to_string(index=False))
