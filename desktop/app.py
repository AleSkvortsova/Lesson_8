import os
import sys
import mimetypes
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def format_list(title: str, items: list[str]) -> str:
    if not items:
        return ""
    rendered = "\n".join(f"- {item}" for item in items)
    return f"{title}:\n{rendered}\n"


def render_text_analysis(analysis: Dict[str, Any]) -> str:
    sections = [
        format_list("Сильные стороны", analysis.get("strengths", [])),
        format_list("Слабые стороны", analysis.get("weaknesses", [])),
        format_list("Уникальные предложения", analysis.get("unique_offers", [])),
        format_list("Целевая аудитория", analysis.get("target_audience", [])),
        format_list("Услуги и удобства", analysis.get("hotel_services", [])),
        format_list("Сигналы доверия", analysis.get("trust_signals", [])),
        format_list("Риски клиентского опыта", analysis.get("guest_experience_risks", [])),
        format_list("Рекомендации", analysis.get("recommendations", [])),
    ]
    summary = analysis.get("summary", "")
    if summary:
        sections.append(f"Резюме:\n{summary}\n")
    return "\n".join(section for section in sections if section).strip()


def render_image_analysis(analysis: Dict[str, Any]) -> str:
    parts = [
        f"Описание:\n{analysis.get('description', '')}",
        f"\nТип сцены:\n{analysis.get('detected_scene_type', '')}",
        format_list("Маркетинговые инсайты", analysis.get("marketing_insights", [])),
        format_list("Элементы гостиничного сервиса", analysis.get("hospitality_elements", [])),
        format_list("Триггеры конверсии", analysis.get("conversion_triggers", [])),
        f"Оценка визуального стиля: {analysis.get('visual_style_score', 0)}/10",
        f"Оценка UX-ясности: {analysis.get('ux_clarity_score', 0)}/10",
        f"Анализ стиля:\n{analysis.get('visual_style_analysis', '')}",
        format_list("Рекомендации", analysis.get("recommendations", [])),
    ]
    return "\n\n".join(part for part in parts if part).strip()


@dataclass
class ApiClient:
    base_url: str
    timeout: int = 180

    def analyze_text(self, text: str) -> Dict[str, Any]:
        return self._post_json("/analyze_text", {"text": text})

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        with open(image_path, "rb") as image_file:
            files = {"file": (os.path.basename(image_path), image_file, mime_type)}
            response = requests.post(f"{self.base_url}/analyze_image", files=files, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def parse_demo(self, url: str) -> Dict[str, Any]:
        return self._post_json("/parse_demo", {"url": url})

    def collect_competitors(self) -> Dict[str, Any]:
        response = requests.post(f"{self.base_url}/collect_competitors", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_history(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/history", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def clear_history(self) -> Dict[str, Any]:
        response = requests.delete(f"{self.base_url}/history", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _post_json(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()


class WorkerSignals(QObject):
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)


class ApiTask(QRunnable):
    def __init__(self, fn, *args):
        super().__init__()
        self.fn = fn
        self.args = args
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args)
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.failed.emit(str(exc))


class DesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Competitor Monitor Desktop")
        self.resize(1280, 820)

        api_base_url = os.getenv("DESKTOP_API_BASE_URL", "http://127.0.0.1:8000")
        self.api = ApiClient(base_url=api_base_url.rstrip("/"))
        self.pool = QThreadPool.globalInstance()
        self.selected_image_path: Optional[str] = None

        self.setStyleSheet(self._build_stylesheet())

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(14)

        logo = QLabel("CompetitorAI")
        logo.setObjectName("logo")
        sidebar_layout.addWidget(logo)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        for label in [
            "Анализ текста",
            "Анализ изображений",
            "Парсинг сайта",
            "Сбор конкурентов",
            "История",
        ]:
            self.nav_list.addItem(label)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._switch_page)
        sidebar_layout.addWidget(self.nav_list, 1)

        self.status_label = QLabel("Система активна")
        self.status_label.setObjectName("statusLabel")
        sidebar_layout.addWidget(self.status_label)
        root_layout.addWidget(sidebar, 0)

        main = QFrame()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(18)

        title = QLabel("Мониторинг конкурентов")
        title.setObjectName("pageTitle")
        subtitle = QLabel(f"Desktop AI-ассистент | API: {self.api.base_url}")
        subtitle.setObjectName("pageSubtitle")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_text_tab())
        self.stack.addWidget(self._build_image_tab())
        self.stack.addWidget(self._build_parse_tab())
        self.stack.addWidget(self._build_collect_tab())
        self.stack.addWidget(self._build_history_tab())
        main_layout.addWidget(self.stack, 1)
        root_layout.addWidget(main, 1)

        self.setCentralWidget(root)

    def _build_text_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        header = QLabel("Анализ текста конкурента")
        header.setObjectName("cardHeader")
        layout.addWidget(header)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Вставьте текст конкурента (минимум 10 символов)...")
        self.text_input.setMinimumHeight(180)
        layout.addWidget(self.text_input)

        self.text_btn = QPushButton("Анализировать текст")
        self.text_btn.clicked.connect(self.on_analyze_text)
        layout.addWidget(self.text_btn)

        self.text_result = QPlainTextEdit()
        self.text_result.setReadOnly(True)
        layout.addWidget(self.text_result)
        return tab

    def _build_image_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        header = QLabel("Анализ изображений")
        header.setObjectName("cardHeader")
        layout.addWidget(header)

        top_bar = QHBoxLayout()
        self.pick_image_btn = QPushButton("Выбрать изображение")
        self.pick_image_btn.clicked.connect(self.on_pick_image)
        top_bar.addWidget(self.pick_image_btn)

        self.image_path_input = QLineEdit()
        self.image_path_input.setReadOnly(True)
        top_bar.addWidget(self.image_path_input)
        layout.addLayout(top_bar)

        self.image_preview = QLabel("Превью изображения")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(220)
        self.image_preview.setStyleSheet("border: 1px solid #ddd; color: #666;")
        layout.addWidget(self.image_preview)

        self.image_btn = QPushButton("Анализировать изображение")
        self.image_btn.clicked.connect(self.on_analyze_image)
        layout.addWidget(self.image_btn)

        self.image_result = QPlainTextEdit()
        self.image_result.setReadOnly(True)
        layout.addWidget(self.image_result)
        return tab

    def _build_parse_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        header = QLabel("Парсинг и анализ сайта")
        header.setObjectName("cardHeader")
        layout.addWidget(header)

        form = QFormLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("example.com или https://example.com")
        form.addRow("URL сайта:", self.url_input)
        layout.addLayout(form)

        self.parse_btn = QPushButton("Парсить и анализировать сайт")
        self.parse_btn.clicked.connect(self.on_parse_site)
        layout.addWidget(self.parse_btn)

        self.parse_result = QPlainTextEdit()
        self.parse_result.setReadOnly(True)
        layout.addWidget(self.parse_result)
        return tab

    def _build_collect_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        header = QLabel("Сбор конкурентов")
        header.setObjectName("cardHeader")
        layout.addWidget(header)

        self.collect_btn = QPushButton("Запустить сбор конкурентов")
        self.collect_btn.clicked.connect(self.on_collect_competitors)
        layout.addWidget(self.collect_btn)

        self.collect_result = QPlainTextEdit()
        self.collect_result.setReadOnly(True)
        layout.addWidget(self.collect_result)
        return tab

    def _build_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        header = QLabel("История запросов")
        header.setObjectName("cardHeader")
        layout.addWidget(header)

        btns = QHBoxLayout()
        self.refresh_history_btn = QPushButton("Обновить историю")
        self.refresh_history_btn.clicked.connect(self.on_refresh_history)
        btns.addWidget(self.refresh_history_btn)

        self.clear_history_btn = QPushButton("Очистить историю")
        self.clear_history_btn.clicked.connect(self.on_clear_history)
        btns.addWidget(self.clear_history_btn)
        layout.addLayout(btns)

        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        layout.addWidget(self.history_list)
        return tab

    def _switch_page(self, index: int):
        if index >= 0:
            self.stack.setCurrentIndex(index)
            if index == 4:
                self.on_refresh_history()

    def _build_stylesheet(self) -> str:
        return """
        QMainWindow, QWidget {
            background-color: #0a0f1c;
            color: #f1f5f9;
            font-family: 'Outfit', 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        #sidebar {
            background-color: #111827;
            border-right: 1px solid #1e293b;
            min-width: 260px;
            max-width: 260px;
        }
        #logo {
            font-size: 22px;
            font-weight: 700;
            color: #22d3ee;
            padding: 6px 4px 12px 4px;
        }
        #statusLabel {
            color: #94a3b8;
            padding: 8px;
            border-top: 1px solid #1e293b;
        }
        #pageTitle {
            font-size: 32px;
            font-weight: 700;
            color: #f1f5f9;
        }
        #pageSubtitle {
            color: #94a3b8;
            margin-bottom: 6px;
        }
        #cardHeader {
            font-size: 20px;
            font-weight: 600;
            color: #22d3ee;
            padding: 2px 0;
        }
        QListWidget#navList {
            background-color: transparent;
            border: none;
            outline: none;
        }
        QListWidget#navList::item {
            padding: 12px 14px;
            margin: 2px 0;
            border-radius: 10px;
            color: #94a3b8;
        }
        QListWidget#navList::item:selected {
            background-color: rgba(6, 182, 212, 0.2);
            color: #22d3ee;
            border: 1px solid rgba(6, 182, 212, 0.4);
        }
        QListWidget#navList::item:hover:!selected {
            background-color: #243049;
            color: #f1f5f9;
        }
        QTextEdit, QPlainTextEdit, QLineEdit, QListWidget#historyList {
            background-color: #0d1320;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 10px;
            color: #f1f5f9;
            selection-background-color: #06b6d4;
        }
        QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {
            border: 1px solid #06b6d4;
        }
        QPushButton {
            background-color: #243049;
            border: 1px solid #334155;
            border-radius: 12px;
            color: #f1f5f9;
            padding: 11px 18px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #2c3a57;
        }
        QPushButton:pressed {
            background-color: #1f2b43;
        }
        QLabel {
            color: #f1f5f9;
        }
        """

    def _run_task(self, fn, success_cb, fail_cb, *args):
        task = ApiTask(fn, *args)
        task.signals.finished.connect(success_cb)
        task.signals.failed.connect(fail_cb)
        self.pool.start(task)

    def _set_busy(self, widget: QWidget, busy: bool):
        widget.setDisabled(busy)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor if busy else Qt.CursorShape.ArrowCursor)

    def _show_error(self, message: str):
        QMessageBox.critical(self, "Ошибка", message)

    def on_analyze_text(self):
        text = self.text_input.toPlainText().strip()
        if len(text) < 10:
            self._show_error("Введите минимум 10 символов.")
            return
        self._set_busy(self.text_btn, True)
        self.text_result.setPlainText("Выполняется анализ...")
        self._run_task(self.api.analyze_text, self._on_text_done, self._on_text_fail, text)

    def _on_text_done(self, result: dict):
        self._set_busy(self.text_btn, False)
        if result.get("success") and result.get("analysis"):
            self.text_result.setPlainText(render_text_analysis(result["analysis"]))
            return
        self.text_result.setPlainText(result.get("error", "Ошибка анализа текста."))

    def _on_text_fail(self, error: str):
        self._set_busy(self.text_btn, False)
        self._show_error(error)

    def on_pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.webp)",
        )
        if not path:
            return
        self.selected_image_path = path
        self.image_path_input.setText(path)
        pix = QPixmap(path)
        if not pix.isNull():
            self.image_preview.setPixmap(
                pix.scaled(
                    self.image_preview.width(),
                    self.image_preview.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def on_analyze_image(self):
        if not self.selected_image_path:
            self._show_error("Сначала выберите изображение.")
            return
        self._set_busy(self.image_btn, True)
        self.image_result.setPlainText("Выполняется анализ...")
        self._run_task(self.api.analyze_image, self._on_image_done, self._on_image_fail, self.selected_image_path)

    def _on_image_done(self, result: dict):
        self._set_busy(self.image_btn, False)
        if result.get("success") and result.get("analysis"):
            self.image_result.setPlainText(render_image_analysis(result["analysis"]))
            return
        self.image_result.setPlainText(result.get("error", "Ошибка анализа изображения."))

    def _on_image_fail(self, error: str):
        self._set_busy(self.image_btn, False)
        self._show_error(error)

    def on_parse_site(self):
        url = self.url_input.text().strip()
        if not url:
            self._show_error("Введите URL сайта.")
            return
        self._set_busy(self.parse_btn, True)
        self.parse_result.setPlainText("Выполняется парсинг...")
        self._run_task(self.api.parse_demo, self._on_parse_done, self._on_parse_fail, url)

    def _on_parse_done(self, result: dict):
        self._set_busy(self.parse_btn, False)
        if not result.get("success"):
            self.parse_result.setPlainText(result.get("error", "Ошибка парсинга сайта."))
            return

        data = result.get("data", {})
        parsed = [
            f"URL: {data.get('url', '')}",
            f"Title: {data.get('title') or 'Не найден'}",
            f"H1: {data.get('h1') or 'Не найден'}",
            f"Первый абзац: {data.get('first_paragraph') or 'Не найден'}",
        ]
        analysis = data.get("analysis")
        if analysis:
            parsed.append("")
            parsed.append(render_text_analysis(analysis))
        self.parse_result.setPlainText("\n".join(parsed))

    def _on_parse_fail(self, error: str):
        self._set_busy(self.parse_btn, False)
        self._show_error(error)

    def on_collect_competitors(self):
        self._set_busy(self.collect_btn, True)
        self.collect_result.setPlainText("Запущен сбор конкурентов...")
        self._run_task(self.api.collect_competitors, self._on_collect_done, self._on_collect_fail)

    def _on_collect_done(self, result: dict):
        self._set_busy(self.collect_btn, False)
        if not result.get("success"):
            self.collect_result.setPlainText(result.get("error", "Ошибка автосбора конкурентов."))
            return

        lines = [
            f"Всего: {result.get('total', 0)}",
            f"Успешно: {result.get('successful', 0)}",
            f"Ошибок: {result.get('failed', 0)}",
            "",
        ]
        for item in result.get("items", []):
            url = item.get("url", "")
            title = item.get("title") or "N/A"
            error = item.get("error")
            status = "OK" if not error else f"Ошибка: {error}"
            lines.append(f"- {url}")
            lines.append(f"  Title: {title}")
            lines.append(f"  Статус: {status}")
        self.collect_result.setPlainText("\n".join(lines))

    def _on_collect_fail(self, error: str):
        self._set_busy(self.collect_btn, False)
        self._show_error(error)

    def on_refresh_history(self):
        self._set_busy(self.refresh_history_btn, True)
        self._run_task(self.api.get_history, self._on_history_done, self._on_history_fail)

    def _on_history_done(self, result: dict):
        self._set_busy(self.refresh_history_btn, False)
        self.history_list.clear()
        for item in result.get("items", []):
            timestamp = item.get("timestamp", "")
            request_type = item.get("request_type", "")
            request_summary = item.get("request_summary", "")
            text = f"[{timestamp}] {request_type} | {request_summary}"
            widget_item = QListWidgetItem(text)
            widget_item.setToolTip(item.get("response_summary", ""))
            self.history_list.addItem(widget_item)

    def _on_history_fail(self, error: str):
        self._set_busy(self.refresh_history_btn, False)
        self._show_error(error)

    def on_clear_history(self):
        confirmation = QMessageBox.question(
            self,
            "Подтверждение",
            "Очистить историю запросов?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        self._set_busy(self.clear_history_btn, True)
        self._run_task(self.api.clear_history, self._on_clear_done, self._on_clear_fail)

    def _on_clear_done(self, _: dict):
        self._set_busy(self.clear_history_btn, False)
        self.history_list.clear()
        QMessageBox.information(self, "Готово", "История очищена.")

    def _on_clear_fail(self, error: str):
        self._set_busy(self.clear_history_btn, False)
        self._show_error(error)


def main():
    app = QApplication(sys.argv)
    window = DesktopWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
