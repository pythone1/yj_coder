from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "data" / "tasks.json"

CATEGORIES = ["工作", "生活", "学习", "创意"]

PRIORITIES = {
    1: {
        "label": "重要且紧急",
        "name": "P1",
        "accent": "#f43f5e",
        "bg": "#fff1f2",
        "border": "#fecdd3",
        "text": "#be123c",
    },
    2: {
        "label": "重要不紧急",
        "name": "P2",
        "accent": "#f59e0b",
        "bg": "#fffbeb",
        "border": "#fde68a",
        "text": "#b45309",
    },
    3: {
        "label": "紧急不重要",
        "name": "P3",
        "accent": "#3b82f6",
        "bg": "#eff6ff",
        "border": "#bfdbfe",
        "text": "#1d4ed8",
    },
    4: {
        "label": "不重要不紧急",
        "name": "P4",
        "accent": "#94a3b8",
        "bg": "#f8fafc",
        "border": "#cbd5e1",
        "text": "#475569",
    },
}


@dataclass
class Task:
    id: int
    text: str
    category: str
    priority: int
    completed: bool
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=int(data["id"]),
            text=str(data["text"]),
            category=str(data.get("category", CATEGORIES[0])),
            priority=int(data.get("priority", 2)),
            completed=bool(data.get("completed", False)),
            created_at=str(data.get("created_at", datetime.now().isoformat(timespec="seconds"))),
        )


class TaskStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.tasks: list[Task] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.tasks = []
            return

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.tasks = [Task.from_dict(item) for item in raw if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            backup = self.path.with_suffix(".broken.json")
            try:
                self.path.replace(backup)
            except OSError:
                pass
            self.tasks = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(task) for task in self.tasks]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, text: str, category: str, priority: int) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        task = Task(
            id=int(time.time() * 1000),
            text=text,
            category=category,
            priority=priority,
            completed=False,
            created_at=now,
        )
        self.tasks.insert(0, task)
        self.save()

    def toggle(self, task_id: int) -> None:
        for task in self.tasks:
            if task.id == task_id:
                task.completed = not task.completed
                self.save()
                return

    def delete(self, task_id: int) -> None:
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self.save()

    def clear_completed(self) -> None:
        self.tasks = [task for task in self.tasks if not task.completed]
        self.save()


class TaskCard(QFrame):
    toggled = Signal(int)
    deleted = Signal(int)

    def __init__(self, task: Task) -> None:
        super().__init__()
        self.task = task
        self.setObjectName("taskCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(self._style())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 10, 10)
        layout.setSpacing(10)

        check_btn = QToolButton()
        check_btn.setText("✓" if task.completed else "○")
        check_btn.setObjectName("checkButton")
        check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        check_btn.clicked.connect(lambda: self.toggled.emit(task.id))
        layout.addWidget(check_btn)

        text_box = QVBoxLayout()
        text_box.setSpacing(5)

        title = QLabel(task.text)
        title.setObjectName("taskTitle")
        title.setWordWrap(False)
        title.setToolTip(task.text)
        title.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.Medium))
        if task.completed:
            title.setStyleSheet("color: #94a3b8; text-decoration: line-through;")
        else:
            title.setStyleSheet("color: #334155;")
        text_box.addWidget(title)

        meta = QHBoxLayout()
        meta.setSpacing(6)

        priority = PRIORITIES.get(task.priority, PRIORITIES[2])
        tag = QLabel(priority["name"])
        tag.setObjectName("priorityTag")
        tag.setStyleSheet(
            f"background: {priority['bg']}; color: {priority['text']};"
            "border-radius: 5px; padding: 2px 6px; font-size: 10px; font-weight: 700;"
        )
        meta.addWidget(tag)

        category = QLabel(f"⏱ {task.category}")
        category.setStyleSheet("color: #94a3b8; font-size: 10px;")
        meta.addWidget(category)
        meta.addStretch()

        text_box.addLayout(meta)
        layout.addLayout(text_box, stretch=1)

        delete_btn = QToolButton()
        delete_btn.setText("×")
        delete_btn.setObjectName("deleteButton")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.deleted.emit(task.id))
        layout.addWidget(delete_btn)

    def _style(self) -> str:
        background = "#f8fafc" if self.task.completed else "#ffffff"
        border = "#e2e8f0"
        check = "#22c55e" if self.task.completed else "#cbd5e1"
        return f"""
            QFrame#taskCard {{
                background: {background};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QFrame#taskCard:hover {{
                border-color: #cbd5e1;
            }}
            QToolButton#checkButton {{
                color: {check};
                border: none;
                font-size: 22px;
                width: 26px;
            }}
            QToolButton#deleteButton {{
                color: #cbd5e1;
                border: none;
                font-size: 22px;
                width: 24px;
            }}
            QToolButton#deleteButton:hover {{
                color: #e11d48;
            }}
        """


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.store = TaskStore(DATA_FILE)
        self.current_filter = "all"
        self.current_view = "matrix"
        self.filter_buttons: dict[str, QPushButton] = {}

        self.setWindowTitle("清爽清单")
        self.resize(1120, 760)
        self.setMinimumSize(920, 620)
        self.setStyleSheet(APP_STYLE)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(28, 24, 28, 28)
        main_layout.setSpacing(22)

        main_layout.addLayout(self._build_header())

        body = QHBoxLayout()
        body.setSpacing(24)
        body.addWidget(self._build_sidebar(), stretch=0)

        self.content_stack = QStackedWidget()
        body.addWidget(self.content_stack, stretch=1)
        main_layout.addLayout(body, stretch=1)

        self.refresh()

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        title = QLabel("⚡ 清爽清单")
        title.setObjectName("appTitle")
        title_box.addWidget(title)

        subtitle = QLabel("让大脑减负，让执行更有序")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(subtitle)

        header.addLayout(title_box, stretch=1)

        switcher = QFrame()
        switcher.setObjectName("switcher")
        switcher_layout = QHBoxLayout(switcher)
        switcher_layout.setContentsMargins(4, 4, 4, 4)
        switcher_layout.setSpacing(4)

        self.view_group = QButtonGroup(self)
        self.view_group.setExclusive(True)

        matrix_btn = QPushButton("▦ 矩阵图")
        matrix_btn.setCheckable(True)
        matrix_btn.setChecked(True)
        matrix_btn.clicked.connect(lambda: self.set_view("matrix"))
        self.view_group.addButton(matrix_btn)
        switcher_layout.addWidget(matrix_btn)

        list_btn = QPushButton("☰ 列表视图")
        list_btn.setCheckable(True)
        list_btn.clicked.connect(lambda: self.set_view("list"))
        self.view_group.addButton(list_btn)
        switcher_layout.addWidget(list_btn)

        header.addWidget(switcher)
        return header

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(340)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(self._build_form())
        layout.addWidget(self._build_filters())
        layout.addStretch()

        return sidebar

    def _build_form(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("+ 新建任务")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self.input = QLineEdit()
        self.input.setPlaceholderText("你想完成什么？")
        self.input.returnPressed.connect(self.add_task)
        layout.addWidget(self.input)

        row = QHBoxLayout()
        row.setSpacing(12)

        category_box = QVBoxLayout()
        category_label = QLabel("分类")
        category_label.setObjectName("fieldLabel")
        self.category_input = QComboBox()
        self.category_input.addItems(CATEGORIES)
        category_box.addWidget(category_label)
        category_box.addWidget(self.category_input)
        row.addLayout(category_box)

        priority_box = QVBoxLayout()
        priority_label = QLabel("优先级")
        priority_label.setObjectName("fieldLabel")
        self.priority_input = QComboBox()
        for value, config in PRIORITIES.items():
            self.priority_input.addItem(f"{config['name']} {config['label']}", value)
        self.priority_input.setCurrentIndex(1)
        priority_box.addWidget(priority_label)
        priority_box.addWidget(self.priority_input)
        row.addLayout(priority_box)
        layout.addLayout(row)

        add_btn = QPushButton("添加至清单")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self.add_task)
        layout.addWidget(add_btn)

        return panel

    def _build_filters(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("分类过滤")
        title.setObjectName("sectionLabel")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("筛选"))
        layout.addLayout(header)

        self.filter_container = QVBoxLayout()
        self.filter_container.setSpacing(6)
        layout.addLayout(self.filter_container)

        self.clear_button = QPushButton("清理已完成任务")
        self.clear_button.setObjectName("ghostButton")
        self.clear_button.clicked.connect(self.clear_completed)
        layout.addWidget(self.clear_button)

        return panel

    def add_task(self) -> None:
        text = self.input.text().strip()
        if not text:
            self.input.setFocus()
            return

        priority = int(self.priority_input.currentData())
        category = self.category_input.currentText()
        self.store.add(text, category, priority)
        self.input.clear()
        self.refresh()

    def set_view(self, view: str) -> None:
        self.current_view = view
        self.refresh()

    def set_filter(self, filter_id: str) -> None:
        self.current_filter = filter_id
        self.refresh()

    def toggle_task(self, task_id: int) -> None:
        self.store.toggle(task_id)
        self.refresh()

    def delete_task(self, task_id: int) -> None:
        self.store.delete(task_id)
        self.refresh()

    def clear_completed(self) -> None:
        count = sum(1 for task in self.store.tasks if task.completed)
        if count == 0:
            return

        reply = QMessageBox.question(
            self,
            "确认清理",
            f"确定清理 {count} 个已完成任务？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.store.clear_completed()
            self.refresh()

    def filtered_tasks(self) -> list[Task]:
        if self.current_filter == "all":
            return self.store.tasks
        if self.current_filter == "active":
            return [task for task in self.store.tasks if not task.completed]
        if self.current_filter == "completed":
            return [task for task in self.store.tasks if task.completed]
        return [task for task in self.store.tasks if task.category == self.current_filter]

    def refresh(self) -> None:
        self._refresh_filters()
        self._refresh_content()

    def _refresh_filters(self) -> None:
        clear_layout(self.filter_container)
        self.filter_buttons.clear()

        filters = [
            ("all", "📖 所有任务"),
            ("active", "○ 待处理"),
            ("completed", "✓ 已完成"),
            *[(category, f"› {category}") for category in CATEGORIES],
        ]

        for filter_id, label in filters:
            count = self._filter_count(filter_id)
            btn = QPushButton(f"{label}    {count}")
            btn.setObjectName("filterButton")
            btn.setCheckable(True)
            btn.setChecked(self.current_filter == filter_id)
            btn.clicked.connect(lambda checked=False, value=filter_id: self.set_filter(value))
            self.filter_container.addWidget(btn)
            self.filter_buttons[filter_id] = btn

    def _filter_count(self, filter_id: str) -> int:
        if filter_id == "all":
            return len(self.store.tasks)
        if filter_id == "active":
            return sum(1 for task in self.store.tasks if not task.completed)
        if filter_id == "completed":
            return sum(1 for task in self.store.tasks if task.completed)
        return sum(1 for task in self.store.tasks if task.category == filter_id)

    def _refresh_content(self) -> None:
        clear_stacked_widget(self.content_stack)
        if self.current_view == "list":
            self.content_stack.addWidget(self._build_list_view())
        else:
            self.content_stack.addWidget(self._build_matrix_view())

    def _build_list_view(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("任务列表")
        title.setObjectName("contentTitle")
        layout.addWidget(title)

        tasks = self.filtered_tasks()
        if not tasks:
            layout.addWidget(empty_state("没有找到相关任务"), stretch=1)
            return panel

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("scrollArea")
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        for task in tasks:
            content_layout.addWidget(self._task_card(task))
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)
        return panel

    def _build_matrix_view(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        tasks = self.filtered_tasks()
        for index, priority in enumerate([1, 2, 3, 4]):
            row = index // 2
            col = index % 2
            layout.addWidget(self._priority_panel(priority, tasks), row, col)

        return page

    def _priority_panel(self, priority: int, tasks: list[Task]) -> QWidget:
        config = PRIORITIES[priority]
        panel = QFrame()
        panel.setObjectName("priorityPanel")
        panel.setStyleSheet(
            f"""
            QFrame#priorityPanel {{
                background: {config['bg']};
                border: 2px solid {config['border']};
                border-radius: 16px;
            }}
            """
        )

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {config['accent']}; font-size: 12px;")
        header.addWidget(dot)

        title = QLabel(config["label"])
        title.setStyleSheet(f"color: {config['text']}; font-weight: 700; font-size: 15px;")
        header.addWidget(title)
        header.addStretch()

        items = [task for task in tasks if task.priority == priority]
        count = QLabel(str(len(items)))
        count.setStyleSheet("color: rgba(15, 23, 42, 0.45); font-size: 11px; font-weight: 700;")
        header.addWidget(count)
        layout.addLayout(header)

        if not items:
            layout.addWidget(empty_state("暂无任务", compact=True), stretch=1)
            return panel

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("scrollArea")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        for task in items:
            content_layout.addWidget(self._task_card(task))
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)
        return panel

    def _task_card(self, task: Task) -> TaskCard:
        card = TaskCard(task)
        card.toggled.connect(self.toggle_task)
        card.deleted.connect(self.delete_task)
        return card


def empty_state(text: str, compact: bool = False) -> QWidget:
    frame = QFrame()
    frame.setObjectName("emptyState")
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setContentsMargins(14, 14, 14, 14)
    icon = QLabel("□")
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setStyleSheet("color: #cbd5e1; font-size: 34px;" if not compact else "color: #cbd5e1; font-size: 24px;")
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("color: #94a3b8; font-size: 13px;" if not compact else "color: #94a3b8; font-size: 11px;")
    layout.addWidget(icon)
    layout.addWidget(label)
    return frame


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.deleteLater()
        elif child_layout is not None:
            clear_layout(child_layout)


def clear_stacked_widget(stack: QStackedWidget) -> None:
    while stack.count():
        widget = stack.widget(0)
        stack.removeWidget(widget)
        widget.deleteLater()


APP_STYLE = """
    QWidget#root {
        background: #f8fafc;
        color: #0f172a;
        font-family: "Microsoft YaHei UI", "Segoe UI";
    }

    QLabel#appTitle {
        color: #1e293b;
        font-size: 30px;
        font-weight: 800;
    }

    QLabel#subtitle {
        color: #64748b;
        font-size: 13px;
        font-style: italic;
    }

    QFrame#switcher,
    QFrame#panel,
    QFrame#contentPanel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
    }

    QFrame#switcher QPushButton {
        background: transparent;
        border: none;
        border-radius: 9px;
        color: #475569;
        padding: 8px 13px;
        font-size: 13px;
    }

    QFrame#switcher QPushButton:checked {
        background: #6366f1;
        color: #ffffff;
        font-weight: 700;
    }

    QLabel#panelTitle {
        color: #334155;
        font-size: 17px;
        font-weight: 700;
    }

    QLabel#fieldLabel {
        color: #94a3b8;
        font-size: 12px;
    }

    QLabel#sectionLabel {
        color: #94a3b8;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1px;
    }

    QLabel#contentTitle {
        color: #1e293b;
        font-size: 20px;
        font-weight: 800;
    }

    QLineEdit,
    QComboBox {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 11px;
        color: #334155;
        font-size: 13px;
        min-height: 20px;
    }

    QLineEdit:focus,
    QComboBox:focus {
        border: 2px solid #6366f1;
    }

    QPushButton#primaryButton {
        background: #0f172a;
        color: #ffffff;
        border: none;
        border-radius: 12px;
        padding: 12px;
        font-size: 14px;
        font-weight: 700;
    }

    QPushButton#primaryButton:hover {
        background: #4f46e5;
    }

    QPushButton#filterButton {
        background: transparent;
        border: none;
        border-radius: 11px;
        color: #475569;
        padding: 10px 12px;
        text-align: left;
        font-size: 13px;
    }

    QPushButton#filterButton:hover {
        background: #f8fafc;
    }

    QPushButton#filterButton:checked {
        background: #eef2ff;
        color: #4f46e5;
        font-weight: 700;
    }

    QPushButton#ghostButton {
        background: transparent;
        border: 1px dashed #cbd5e1;
        border-radius: 10px;
        color: #94a3b8;
        padding: 9px;
        font-size: 12px;
    }

    QPushButton#ghostButton:hover {
        color: #e11d48;
        border-color: #fecdd3;
        background: #fff1f2;
    }

    QScrollArea#scrollArea {
        background: transparent;
        border: none;
    }

    QScrollArea#scrollArea QWidget {
        background: transparent;
    }

    QFrame#emptyState {
        background: transparent;
        border: 1px dashed #cbd5e1;
        border-radius: 14px;
    }
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(build_palette())

    window = MainWindow()
    window.show()

    return app.exec()


def build_palette():
    palette = QApplication.palette()
    palette.setColor(palette.ColorRole.Highlight, QColor("#6366f1"))
    palette.setColor(palette.ColorRole.HighlightedText, QColor("#ffffff"))
    return palette


if __name__ == "__main__":
    raise SystemExit(main())
