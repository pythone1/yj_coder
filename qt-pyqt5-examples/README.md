# 清爽清单

PySide6 实现的本地任务清单工具，支持列表视图、四象限矩阵、分类过滤和 JSON 持久化。

## 运行

```powershell
conda activate yolov12
python main.py
```

或：

```powershell
conda run -n yolov12 python main.py
```

## 数据文件

任务数据保存在：

```text
data/tasks.json
```

## 功能

- 新增任务
- 完成/取消完成
- 删除任务
- 清理已完成任务
- 按状态或分类过滤
- 列表视图和优先级矩阵视图
