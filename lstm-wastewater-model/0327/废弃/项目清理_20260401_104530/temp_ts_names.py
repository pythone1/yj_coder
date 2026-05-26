# -*- coding: utf-8 -*-
import pandas as pd
p = r'E:\PY\LSTM\0327\data_ascii\dry_timeseries_detail.csv'
df = pd.read_csv(p, encoding='utf-8-sig')
print(df['时间序列名称'].dropna().unique().tolist())
