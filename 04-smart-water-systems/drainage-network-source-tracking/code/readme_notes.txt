0520 主链代码说明

一、入口脚本
1. `build_0416_data.py`
构造基线、事件、观测增量、总入流和真值注水数据。

2. `run_small_0416.py`
小参数 GA + AM 运行入口。

3. `run_medium_0416.py`
中参数 GA + AM 运行入口。

4. `run_large_0416.py`
大参数 GA + AM 运行入口。

二、核心模块
1. `config_0416.py`
管理模型路径、候选井、监测井、真值点、排口、时间步长和算法默认参数。

2. `simulation_0416.py`
把候选井份额转换为逐时注水过程，写入运行时 INP，并调用 PySWMM 计算 NSE 和 SSE。

3. `ga_am_0416.py`
执行 GA 搜索、initial PPD 构造、AM 多链采样和后验样本提取。

4. `run_outputs_0416.py`
保存 GA best、posterior best MAP、posterior median summary 等结果。

三、0520 路径规则
`config_0416.py` 按代码所在目录自动识别项目根目录。
模型优先放在：
`models/`

四、运行命令
1. 数据构造
`conda run -n LSTM python code\build_0416_data.py`

2. 小参数
`conda run -n LSTM python code\run_small_0416.py`

3. 中参数
`conda run -n LSTM python code\run_medium_0416.py`

4. 大参数
`conda run -n LSTM python code\run_large_0416.py`

五、需要先改的点
新模型放入后，打开 `config_0416.py`，修改：
1. `CANDIDATE_NODES`
2. `MONITOR_NODES`
3. `TRUTH_INJECTION_NODES`
4. `OUTFALL_NODE`
5. `STEP_MINUTES`

六、输出目录
数据输出：
`data/generated_0520/`

结果输出：
`results_0520/`

运行时文件：
`runtime_ascii/`
