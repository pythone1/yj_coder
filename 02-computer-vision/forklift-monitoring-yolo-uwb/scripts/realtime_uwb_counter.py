"""
项目名称: forklift-monitoring-yolo-uwb
技术领域: 02-computer-vision
模块说明: realtime_uwb_counter.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from forklift_monitoring.app.realtime_uwb import main


if __name__ == "__main__":
    main()
