"""
项目名称: pypoo-reactor-simulation
技术领域: 04-smart-water-systems
模块说明: base_model.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

class BaseReactionModel:
    """Base class for reaction models."""
    def compute(self, state, parameters):
        raise NotImplementedError
