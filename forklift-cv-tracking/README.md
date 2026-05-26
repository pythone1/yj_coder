# 叉车配比监控算法原型

本项目实现一个“定位优先、视觉辅助”的 Python 项目原型。

最简单的使用方式不是去找脚本，而是：

1. 修改 [project_config.yaml](E:\PY\叉车识别\project_config.yaml)
2. 运行 `python main.py`
3. 打开生成的可视化页面和图片看结果

- 主链路：基于 UWB/TDOA 定位数据进行区域判定、轨迹去抖和 `A -> C` / `B -> C` 完整路径计数
- 辅链路：基于 YOLO + 跟踪进行摄像头检测与计数
- 辅链路：基于 YOLO 检测 + 多目标追踪 + 图像区域状态机进行辅助路径判别
- 融合层：以定位结果为主，视觉结果作为辅助校验和证据留存

## 当前假设

- 现场区域抽象为三个关键功能区：`A`、`B`、`C`
- 一次有效运输定义为：车辆从 `A` 或 `B` 启动，最终进入 `C`，形成一次完整路径
- `A -> C` 和 `B -> C` 分开计数
- 摄像头辅助链路只做辅助统计，不覆盖主计数
- 已根据你提供的规格书补充了对 `PDOA` 上位机结果库的适配入口，优先读取 `data.db` 中的 `location` 表

## 目录

```text
config/
  site_example.yaml        示例站点配置
data/
  sample_uwb_tracks.csv    示例 UWB 轨迹
docs/
  real_data_sources.md     真实数据源与联调建议
scripts/
  demo_uwb_counter.py      UWB 路径计数演示
  demo_camera_counter.py   摄像头辅助计数演示
pyproject.toml             项目配置，可用于 editable install
forklift_monitoring/
  app/                     项目入口
  core/                    公共类型、配置、几何计算
  uwb/                     UWB 主链路
  vision/                  YOLO 辅助链路
  fusion/                  融合接口
```

## 快速开始

最简单运行方式：

```powershell
conda run -n yolov12 python main.py
```

`project_config.yaml` 里最关键的参数有：

- `run.mode`
- `run.site_config`
- `uwb.input_type`
- `uwb.input_path`
- `camera.source`
- `camera.max_frames`
- `realtime_uwb.source_type`
- `realtime_uwb.port`
- `realtime_uwb.db_path`

如果你只是想先看 UWB 结果，保持默认即可。

默认会额外生成：

- [output/visualization/uwb_report.png](E:\PY\叉车识别\output\visualization\uwb_report.png)
- [output/visualization/uwb_report.html](E:\PY\叉车识别\output\visualization\uwb_report.html)

其中 HTML 页面会直接说明：

- 车走了哪条路径
- 为什么这样计数
- 每一步系统在做什么

脚本方式仍然保留，但不是首选：

```powershell
conda run -n yolov12 python scripts/demo_uwb_counter.py --config config/site_example.yaml --input data/sample_uwb_tracks.csv
```

如果按标准项目方式使用，建议在项目根目录执行：

```powershell
conda run -n yolov12 python -m pip install -e .
```

安装后可直接运行：

```powershell
conda run -n yolov12 forklift-demo-uwb
conda run -n yolov12 forklift-demo-camera --source 0
```

如果直接在 PyCharm 里运行脚本，不传参数也可以：

- `scripts/demo_uwb_counter.py` 会默认读取示例配置和示例 UWB 数据
- `scripts/demo_camera_counter.py` 会默认读取示例配置，并尝试打开摄像头 `0`

如果直接读取你提供的 PDOA 上位机数据库：

```powershell
conda run -n yolov12 python scripts/demo_uwb_counter.py --config config/site_example.yaml --input tmp/pdoa_tool/pdoaa/data.db --input-type sqlite
```

如果要运行摄像头辅助链路：

```powershell
conda run -n yolov12 python scripts/demo_camera_counter.py --config config/site_example.yaml --source 0
```

如果要跑实时 UWB：

```powershell
conda run -n yolov12 python scripts/realtime_uwb_counter.py --config config/site_example.yaml --source-type sqlite-tail --db-path <PDOA上位机data.db路径>
```

或串口文本坐标流：

```powershell
conda run -n yolov12 python scripts/realtime_uwb_counter.py --config config/site_example.yaml --source-type serial-line --port COM3 --baudrate 115200
```

## 真实设备接入要求

UWB 链路建议至少提供以下字段：

- `timestamp_ms`
- `tag_id`
- `x`
- `y`
- `z`
- `quality`（可选）

如果直接复用 PDOA 上位机，则当前已兼容的字段为：

- `ts`
- `tagid`
- `x`
- `y`
- `filterX`
- `filterY`
- `dis`
- `degree`

摄像头链路建议提供：

- RTSP/USB 摄像头地址
- 安装视角与像素标定信息
- 需要统计的目标类别（建议先仅统计叉车）

## 当前工程策略

- UWB 主链路：优先使用 PDOA 上位机 `data.db` 或串口坐标流完成实时路径计数
- 视觉辅助链路：使用 `检测 + 追踪`，再按图像区域状态机辅助判定 `A -> C` / `B -> C`
- 视觉结果不覆盖 UWB 主判定，只做辅助校验、录像取证和异常回看

## 当前限制

- 已支持的实时 UWB 入口：
  - PDOA 上位机 `data.db` 实时追踪
  - 串口输出坐标文本流（CSV/JSON）
- 已补了 GNM 二进制协议帧解析器，但由于现有资料里还缺少可直接映射到 `x/y` 的完整 PDOA 载荷定义，暂时没有把厂商二进制串口流直接还原成坐标路径计数
- 如果你后面能抓一段真实串口十六进制日志，我可以继续把“原始 RS485 -> 坐标 -> 路径计数”这一层补全

## 后续可继续扩展

- 将称重传感器和姿态传感器接入主状态机
- 增加多车置信度融合
- 增加告警、报表与可视化界面
