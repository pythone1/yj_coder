"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: raytune.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

from ultralytics.utils import SETTINGS

try:
    assert SETTINGS["raytune"] is True  # verify integration is enabled
    import ray
    from ray import tune
    from ray.air import session

except (ImportError, AssertionError):
    tune = None


def on_fit_epoch_end(trainer):
    """Sends training metrics to Ray Tune at end of each epoch."""
    if ray.train._internal.session.get_session():  # replacement for deprecated ray.tune.is_session_enabled()
        metrics = trainer.metrics
        session.report({**metrics, **{"epoch": trainer.epoch + 1}})


callbacks = (
    {
        "on_fit_epoch_end": on_fit_epoch_end,
    }
    if tune
    else {}
)
