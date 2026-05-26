# 0401 工作目录说明

这个目录用于在干净底板上继续开展新工作。

## 目录结构

- `code`
  - 从 `0327/clean_code` 复制过来的当前可用代码
  - 包含：
    - `config_clean.py`
    - `simulation_clean.py`
    - `ga_am_clean.py`
    - `run_small_clean.py`
    - `run_medium_clean.py`
    - `export_key_nodes_visualization.py`

- `models/current_confirmed_models`
  - 当前确认可用的主模型目录
  - 重点文件：
    - `0327_旱天基线模型_10分钟_泵站0.5开0.2关.inp/.out/.rpt`
    - `0327_由旱天基线重建_三点注水模型_0.3倍.inp/.out/.rpt`
    - `0327_排口与关键节点可视化.html`
    - `0327_排口与关键节点信息.csv`
    - `0327_排口与关键节点连接关系.csv`

- `models/current_confirmed_models_2`
  - 补充目录，对应之前 `(2)` 子目录
  - 重点文件：
    - `0327_旱天基线模型_10分钟_泵站0.5开0.2关.inp/.out/.rpt`
    - `0327_由旱天基线重建_三点注水模型_0.3倍.rpt/.thm`

## 当前建议使用的底板

优先使用：

- `E:\\PY\\LSTM\\0401\\models\\current_confirmed_models\\0327_旱天基线模型_10分钟_泵站0.5开0.2关.inp`

配套事件模型：

- `E:\\PY\\LSTM\\0401\\models\\current_confirmed_models\\0327_由旱天基线重建_三点注水模型_0.3倍.inp`

## 当前已知状态

- 旱天基线：无节点溢流
- 0.3 倍事件：当前确认目录里仍有 `J41` 溢流
- 连续性误差仍需后续重点排查

