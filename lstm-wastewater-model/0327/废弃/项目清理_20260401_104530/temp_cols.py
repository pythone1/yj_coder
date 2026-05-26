# -*- coding: utf-8 -*-
import pandas as pd
p = r'E:\PY\LSTM\0327\data_ascii\dry_timeseries_detail.csv'
df = pd.read_csv(p, encoding='utf-8-sig')
print(list(df.columns))
print(df.head(3).to_json(force_ascii=False, orient='records'))
