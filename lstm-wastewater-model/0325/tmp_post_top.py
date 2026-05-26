# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
p = Path(r'E:\PY\LSTM\0325\结果')
post = pd.read_csv(p / '0325_后验节点权重.csv', encoding='utf-8-sig')
print(post.head(12).to_string(index=False))
