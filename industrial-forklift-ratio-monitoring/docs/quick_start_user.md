# 怎么看这个项目

如果你现在只想“看结果”，不要先看代码，直接看这三个地方：

## 1. 改参数

文件：

- [project_config.yaml](E:\PY\叉车识别\project_config.yaml)

你主要改这几个参数：

- `run.mode`
- `uwb.input_type`
- `uwb.input_path`
- `camera.source`
- `realtime_uwb.port`
- `realtime_uwb.db_path`

## 2. 跑程序

```powershell
conda run -n yolov12 python main.py
```

## 3. 看结果

优先看：

- [output/visualization/uwb_report.html](E:\PY\叉车识别\output\visualization\uwb_report.html)
- [output/visualization/uwb_report.png](E:\PY\叉车识别\output\visualization\uwb_report.png)

## 4. 系统每一步在干什么

当前 UWB 主流程是：

1. 读取坐标
2. 做轨迹平滑
3. 判断当前点属于 A/B/C 哪个区域
4. 只有完整经过 `A -> C` 或 `B -> C` 才计数
5. 输出事件表和轨迹图

## 5. 当前还没做好的地方

- 摄像头可视化页面还没补齐到和 UWB 同等程度
- 真实 RS485 原始二进制坐标还没完全打通
- 现在最成熟的是 `UWB 样例/坐标流 -> 轨迹图 + 路径计数`
