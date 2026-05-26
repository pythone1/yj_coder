# -*- coding: utf-8 -*-
import time, sys, numpy as np, shutil
from pathlib import Path
sys.path.insert(0, r'E:\PY\LSTM\0327\代码')
from 公共配置与数据 import load_generated_data
from 模型仿真与评估 import build_dataset, evaluate_shares
src = Path(r'E:\PY\LSTM\0327\data_ascii\dry_base_core.inp')
dst_dir = Path(r'E:\PY\LSTM\0327\runtime_data\worker_9')
dst_dir.mkdir(parents=True, exist_ok=True)
dst = dst_dir / 'model.inp'
shutil.copyfile(src, dst)
g = load_generated_data()
d = build_dataset(g)
shares = np.zeros(20)
shares[4] = 18000/76000
shares[11] = 26000/76000
shares[17] = 32000/76000
start = time.time()
for i in range(3):
    shutil.copyfile(src, dst)
    t = time.time()
    r = evaluate_shares(shares, d, str(dst))
    print(i, round(time.time()-t, 3), r['mean_nse'])
print('total', round(time.time()-start, 3))
