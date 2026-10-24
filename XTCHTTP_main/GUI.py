"""小天才请求加密工具的 PySide6 图形界面"""
import contextlib
import datetime
import io
import json
import os
import re
import sys
import threading
import time
import uuid

from PySide6.QtCore import QObject, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QKeySequence, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import XTCHTTPUtils
from XTCHTTPUtils.Get_data import create_data_file
from XTCHTTP_main import XTChttp
from XTCHTTP_main.ui_theme import STYLESHEET, icon

# 用于剥离日志中 colorama 产生的 ANSI 颜色码
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

CONFIG_KEYS = ['watchid', 'bindnumber', 'chipid', 'rsaKey', 'KeyId', 'model']
# 发送请求前必须填写的配置项（与 XTCHTTPUtils/Get_data.py 中的 required_keys 一致）
REQUIRED_KEYS = ['watchid', 'bindnumber', 'chipid', 'KeyId', 'rsaKey']


def mono_font():
    """等宽字体（须在 QApplication 创建后调用）"""
    return QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)


class LogEmitter(QObject):
    """把任意线程产生的日志文本投递回 GUI 线程"""
    message = Signal(str)


class _LogStream(io.TextIOBase):
    """替代 sys.stdout 的流，把 print 输出转发到日志面板"""

    def __init__(self, emit):
        self._emit = emit

    def write(self, s):
        if s:
            self._emit(s)
        return len(s)

    def flush(self):
        pass


class MainWindow(QMainWindow):

    result_ready = Signal(dict, float)
    request_failed = Signal(str, float)

    def __init__(self):
        super().__init__()
        self.setWindowTitle('小天才请求加密工具')
        self.resize(1160, 840)
        self.setMinimumSize(880, 680)
        screen = self.screen().availableGeometry()
        self.resize(min(self.width(), screen.width()), min(self.height(), screen.height()))
        self._apply_theme()

        self._fields = {}
        self._build_ui()

        self._log_emitter = LogEmitter()
        self._log_emitter.message.connect(self._append_log)
        # 把底层库 Logger 的 print 输出（stdout）重定向到日志面板
        self._stdout_redirect = contextlib.redirect_stdout(
            _LogStream(self._log_emitter.message.emit))
        self._stdout_redirect.__enter__()

        self.result_ready.connect(self._on_result)
        self.request_failed.connect(self._on_error)

        self._load_config()
        self._set_status('就绪')
        self._log('欢迎使用小天才请求加密工具！')

    # ---------- 界面搭建 ----------

    def _apply_theme(self):
        font = QFont()
        font.setFamilies(['Segoe UI', 'PingFang SC', 'Noto Sans CJK SC', 'Microsoft YaHei'])
        self.setFont(font)
        # 明确设置浅色调色板，避免系统深色模式影响文本、占位文字和编辑器。
        palette = self.palette()
        for role, color in [
            (QPalette.ColorRole.Window, '#f3f6f8'),
            (QPalette.ColorRole.WindowText, '#243449'),
            (QPalette.ColorRole.Base, '#f8fafc'),
            (QPalette.ColorRole.Text, '#293b50'),
            (QPalette.ColorRole.Button, '#ffffff'),
            (QPalette.ColorRole.ButtonText, '#465d6d'),
            (QPalette.ColorRole.Highlight, '#cbece3'),
            (QPalette.ColorRole.HighlightedText, '#163e38'),
            (QPalette.ColorRole.PlaceholderText, '#8b9aa9'),
        ]:
            palette.setColor(role, QColor(color))
        self.setPalette(palette)
        self.setStyleSheet(STYLESHEET)

    @staticmethod
    def _label(text, role=None):
        label = QLabel(text)
        if role:
            label.setProperty('role', role)
        return label

    def _card(self):
        card = QFrame()
        card.setProperty('role', 'card')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        return card, layout

    def _section_heading(self, title, subtitle, icon_name):
        row = QHBoxLayout()
        row.setSpacing(11)
        badge = QLabel()
        badge.setProperty('role', 'iconBadge')
        badge.setFixedSize(38, 38)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setPixmap(icon(icon_name, '#278576').pixmap(QSize(22, 22)))
        row.addWidget(badge)
        labels = QVBoxLayout()
        labels.setSpacing(2)
        labels.addWidget(self._label(title, 'sectionTitle'))
        labels.addWidget(self._label(subtitle, 'muted'))
        row.addLayout(labels, 1)
        return row

    def _build_ui(self):
        central = QWidget()
        central.setObjectName('workspace')
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 22, 24, 14)
        root.setSpacing(18)

        header = QHBoxLayout()
        header.setSpacing(14)
        mark = QLabel('xtc')
        mark.setObjectName('brandMark')
        mark.setFixedSize(50, 50)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(mark)
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel('请求工作台')
        title.setObjectName('pageTitle')
        subtitle = QLabel('小天才请求加密工具 · 配置、发送、查看响应')
        subtitle.setObjectName('subtitle')
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch()
        self.status_label = QLabel('就绪')
        self.status_label.setObjectName('statusBadge')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setAccessibleName('请求状态')
        self.status_label.setMinimumWidth(78)
        header.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)

        # 配置固定在左侧，请求和响应的高度可拖动调整。
        columns = QHBoxLayout()
        columns.setSpacing(18)
        config = self._build_config_group()
        config.setFixedWidth(292)
        columns.addWidget(config)
        self.request_splitter = QSplitter(Qt.Orientation.Vertical)
        self.request_splitter.setObjectName('requestWorkspace')
        self.request_splitter.setChildrenCollapsible(False)
        self.request_splitter.setHandleWidth(14)
        self.request_splitter.addWidget(self._build_request_group())
        self.request_splitter.addWidget(self._build_response_group())
        self.request_splitter.setStretchFactor(0, 1)
        self.request_splitter.setStretchFactor(1, 1)
        self.request_splitter.setSizes([360, 320])
        # 当窗口高度不足时滚动整块工作区，避免强行压缩造成控件互相覆盖。
        self.work_scroll = QScrollArea()
        self.work_scroll.setWidgetResizable(True)
        self.work_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.work_scroll.setWidget(self.request_splitter)
        columns.addWidget(self.work_scroll, 1)
        root.addLayout(columns, 1)

        footer = QHBoxLayout()
        footer.addWidget(self._label('XTC  /  请求加密工具', 'muted'))
        footer.addStretch()
        footer.addWidget(self._label('配置文件 · 本地保存', 'muted'))
        root.addLayout(footer)

    def _build_config_group(self):
        card, layout = self._card()
        layout.addLayout(self._section_heading('设备配置', '设置请求使用的设备信息', 'device'))

        # 小屏幕上配置区可以滚动，保存按钮始终可见。
        scroll = QScrollArea()
        self.config_scroll = scroll
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        fields = QWidget()
        fields.setObjectName('configFields')
        form = QVBoxLayout(fields)
        form.setContentsMargins(0, 0, 6, 0)
        form.setSpacing(10)
        names = {
            'watchid': ('手表 ID', 'watchid'),
            'bindnumber': ('绑定号码', 'bindnumber'),
            'chipid': ('芯片 ID', 'chipid'),
            'KeyId': ('密钥 ID', 'KeyId'),
            'model': ('设备型号（选填）', 'model'),
        }
        for key in names:
            title, placeholder = names[key]
            edit = QLineEdit()
            edit.setMinimumWidth(0)
            edit.setPlaceholderText(placeholder)
            edit.setAccessibleName(title)
            edit.setToolTip(f'{title} · {key}')
            self._fields[key] = edit

        def field(key):
            column = QVBoxLayout()
            column.setSpacing(5)
            label = self._label(names[key][0], 'fieldLabel')
            label.setBuddy(self._fields[key])
            column.addWidget(label)
            column.addWidget(self._fields[key])
            return column

        for key in ['watchid', 'bindnumber', 'chipid']:
            form.addLayout(field(key))
        pair = QHBoxLayout()
        pair.setSpacing(10)
        pair.addLayout(field('KeyId'), 1)
        pair.addLayout(field('model'), 1)
        form.addLayout(pair)

        rsa_column = QVBoxLayout()
        rsa_column.setSpacing(5)
        rsa_label = self._label('RSA 公钥', 'fieldLabel')
        rsa_edit = QPlainTextEdit()
        rsa_edit.setFixedHeight(94)
        rsa_edit.setPlaceholderText('粘贴 rsaKey 公钥内容…')
        rsa_edit.setFont(mono_font())
        rsa_edit.setTabChangesFocus(True)
        rsa_edit.setAccessibleName('RSA 公钥')
        rsa_label.setBuddy(rsa_edit)
        self._fields['rsaKey'] = rsa_edit
        rsa_column.addWidget(rsa_label)
        rsa_column.addWidget(rsa_edit)
        form.addLayout(rsa_column)
        form.addStretch()
        scroll.setWidget(fields)
        layout.addWidget(scroll, 1)

        self.save_btn = QPushButton('保存配置')
        self.save_btn.setIcon(icon('save'))
        self.save_btn.setShortcut(QKeySequence.StandardKey.Save)
        self.save_btn.clicked.connect(self._save_config)
        layout.addWidget(self.save_btn)

        note = QFrame()
        note.setObjectName('configFooter')
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(12, 9, 12, 9)
        self.config_hint = self._label('保存在 data.json，下次自动加载', 'muted')
        self.config_hint.setWordWrap(True)
        note_layout.addWidget(self.config_hint)
        layout.addWidget(note)
        return card

    def _build_request_group(self):
        card, layout = self._card()
        layout.addLayout(self._section_heading('编辑请求', '填写接口地址与 JSON 请求内容', 'send'))

        address = QHBoxLayout()
        address.setSpacing(8)
        method = QLabel('POST')
        method.setObjectName('methodBadge')
        method.setAlignment(Qt.AlignmentFlag.AlignCenter)
        address.addWidget(method)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText('https://api.okii.com/…')
        self.url_edit.setAccessibleName('请求 URL')
        self.url_edit.setClearButtonEnabled(True)
        address.addWidget(self.url_edit, 1)
        layout.addLayout(address)

        body_heading = QHBoxLayout()
        body_heading.addWidget(self._label('请求内容（选填）', 'fieldLabel'))
        body_heading.addWidget(self._label('JSON', 'eyebrow'))
        body_heading.addStretch()
        self.format_btn = QPushButton('格式化 JSON')
        self.format_btn.setProperty('role', 'ghost')
        self.format_btn.clicked.connect(self._format_body)
        body_heading.addWidget(self.format_btn)
        layout.addLayout(body_heading)

        self.body_edit = QPlainTextEdit()
        self.body_edit.setFont(mono_font())
        self.body_edit.setMinimumHeight(96)
        self.body_edit.setPlaceholderText('{\n    "key": "value"\n}')
        self.body_edit.setAccessibleName('JSON 请求内容')
        self.body_edit.setTabChangesFocus(True)
        layout.addWidget(self.body_edit, 1)

        self.notice = QFrame()
        self.notice.setObjectName('requestNotice')
        notice_layout = QHBoxLayout(self.notice)
        notice_layout.setContentsMargins(10, 7, 10, 7)
        self.notice_label = QLabel()
        self.notice_label.setWordWrap(True)
        notice_layout.addWidget(self.notice_label, 1)
        self.notice.hide()
        layout.addWidget(self.notice)

        actions = QHBoxLayout()
        shortcut_hint = '⌘ + Enter 发送' if sys.platform == 'darwin' else 'Ctrl + Enter 发送'
        actions.addWidget(self._label(shortcut_hint, 'muted'))
        actions.addStretch()
        self.send_btn = QPushButton('发送请求')
        self.send_btn.setProperty('role', 'primary')
        self.send_btn.setIcon(icon('send', '#ffffff', 18))
        self.send_btn.setShortcut(QKeySequence('Ctrl+Return'))
        self.send_btn.clicked.connect(self._on_send)
        actions.addWidget(self.send_btn)
        layout.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(3)
        # 保留进度条的位置，状态变化时避免布局跳动。
        policy = self.progress.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.progress.setSizePolicy(policy)
        layout.addWidget(self.progress)
        self.progress.hide()
        return card

    def _build_response_group(self):
        card, layout = self._card()
        heading = QHBoxLayout()
        heading.addLayout(self._section_heading('响应结果', '解密后的数据与运行日志', 'response'), 1)
        self.response_meta = self._label('等待请求', 'muted')
        heading.addWidget(self.response_meta)
        layout.addLayout(heading)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setDrawBase(False)
        self.tabs.setMinimumHeight(170)
        self.json_view = self._make_readonly_text()
        self.table_view = self._make_readonly_text()
        self.log_view = self._make_readonly_text()
        self.log_view.setMaximumBlockCount(2000)
        self.log_view.setPlaceholderText('运行日志会显示在这里')
        self.json_view.setAccessibleName('JSON 响应')
        self.table_view.setAccessibleName('表格响应')
        self.log_view.setAccessibleName('运行日志')
        self.response_pages = []
        self.empty_labels = []
        for view, title in [(self.json_view, 'JSON'), (self.table_view, '表格')]:
            stack = QStackedWidget()
            empty = QWidget()
            empty.setObjectName('emptyState')
            empty_layout = QVBoxLayout(empty)
            empty_layout.setSpacing(5)
            empty_layout.addStretch()
            symbol = QLabel()
            symbol.setPixmap(icon('response', '#9cb8b3', 36).pixmap(QSize(36, 36)))
            symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(symbol)
            text = QLabel('等待第一条响应')
            text.setObjectName('emptyTitle')
            text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint = self._label('发送请求后，在这里查看解密结果', 'muted')
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint.setWordWrap(True)
            empty_layout.addWidget(text)
            empty_layout.addWidget(hint)
            empty_layout.addStretch()
            stack.addWidget(empty)
            stack.addWidget(view)
            self.empty_labels.append((text, hint))
            self.response_pages.append(stack)
            self.tabs.addTab(stack, title)
        self.tabs.addTab(self.log_view, '日志')
        layout.addWidget(self.tabs, 1)

        tools = QHBoxLayout()
        tools.setContentsMargins(0, 5, 0, 0)
        self.copy_btn = QPushButton('复制结果')
        self.copy_btn.setProperty('role', 'ghost')
        self.copy_btn.setIcon(icon('copy', '#748595', 16))
        self.copy_btn.clicked.connect(self._copy_result)
        self.copy_btn.setEnabled(False)
        tools.addWidget(self.copy_btn)
        tools.addStretch()
        self.clear_log_btn = QPushButton('清空日志')
        self.clear_log_btn.setProperty('role', 'ghost')
        self.clear_log_btn.clicked.connect(self.log_view.clear)
        self.clear_log_btn.setVisible(False)
        tools.addWidget(self.clear_log_btn)
        layout.addLayout(tools)
        self.tabs.currentChanged.connect(self._update_result_actions)
        for view in (self.json_view, self.table_view, self.log_view):
            view.textChanged.connect(self._update_result_actions)
        return card

    def _make_readonly_text(self):
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(mono_font())
        text.setProperty('role', 'result')
        text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        return text

    def _set_status(self, text, tone='ready'):
        self.status_label.setText(text)
        self.status_label.setProperty('tone', tone)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _show_notice(self, text):
        self.notice_label.setText(text)
        self.notice.show()
        self._set_status('请检查输入', 'warning')
        self._log('提示：' + text)

    def _format_body(self):
        body = self.body_edit.toPlainText().strip()
        if not body:
            return
        try:
            formatted = json.dumps(json.loads(body), indent=4, ensure_ascii=False)
        except json.JSONDecodeError as e:
            self._show_notice(f'JSON 格式有误：第 {e.lineno} 行，第 {e.colno} 列')
            self.body_edit.setFocus()
            return
        # 使用编辑块，使一次撤销即可恢复格式化前的原文。
        cursor = self.body_edit.textCursor()
        cursor.beginEditBlock()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText(formatted)
        cursor.endEditBlock()
        self.notice.hide()
        if self.send_btn.isEnabled():
            self._set_status('JSON 已格式化')

    def _update_result_actions(self, *_):
        index = self.tabs.currentIndex()
        view = (self.json_view, self.table_view, self.log_view)[index]
        self.copy_btn.setText('复制日志' if index == 2 else '复制结果')
        self.copy_btn.setEnabled(bool(view.toPlainText()))
        self.clear_log_btn.setVisible(index == 2)

    def _copy_result(self):
        view = (self.json_view, self.table_view, self.log_view)[self.tabs.currentIndex()]
        if view.toPlainText():
            QApplication.clipboard().setText(view.toPlainText())
            self.copy_btn.setText('已复制')

    # ---------- 配置读写 ----------

    def _load_config(self):
        path = 'data.json'
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.loads(file.read())
        except FileNotFoundError:
            create_data_file()
            self._log('未找到 data.json，已自动创建默认配置文件，请填写配置后点击「保存配置」')
            return
        except (json.JSONDecodeError, ValueError) as e:
            # 文件损坏时先备份再重建，避免直接覆盖用户数据
            try:
                os.replace(path, path + '.bak')
                create_data_file()
                self._log(f'data.json 内容无效（{e}），已将原文件备份为 data.json.bak 并重新生成默认配置')
            except OSError:
                self._log(f'data.json 内容无效（{e}），且自动重建失败，请手动修复')
            return

        if not isinstance(data, dict):
            self._log('data.json 内容无效：顶层必须是 JSON 对象')
            return

        for key in CONFIG_KEYS:
            value = data.get(key, '')
            if not isinstance(value, str):
                value = ''
            if key == 'rsaKey':
                self._fields[key].setPlainText(value)
            else:
                self._fields[key].setText(value)

        missing = [key for key in REQUIRED_KEYS if not data.get(key)]
        if missing:
            self._log('提示：以下配置项为空，请填写后点击「保存配置」：' + ', '.join(missing))

    def _save_config(self):
        data = {}
        for key in CONFIG_KEYS:
            if key == 'rsaKey':
                data[key] = self._fields[key].toPlainText().strip()
            else:
                data[key] = self._fields[key].text().strip()
        try:
            with open('data.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            self.config_hint.setText('已保存 · ' + datetime.datetime.now().strftime('%H:%M') + '\n下次启动自动加载')
            self._log('配置已保存到 data.json')
        except OSError as e:
            self.config_hint.setText('保存失败，请在日志中查看详情')
            self.tabs.setCurrentIndex(2)
            self._log(f'保存配置失败：{e}')

    # ---------- 发送请求 ----------

    def _collect_data(self):
        data = {}
        for key in CONFIG_KEYS:
            if key == 'rsaKey':
                data[key] = self._fields[key].toPlainText().strip()
            else:
                data[key] = self._fields[key].text().strip()

        missing = [key for key in REQUIRED_KEYS if not data[key]]
        if missing:
            self._show_notice('请补全设备配置：' + '、'.join(missing))
            self._fields[missing[0]].setFocus()
            self.config_scroll.ensureWidgetVisible(self._fields[missing[0]])
            return None

        url = self.url_edit.text().strip()
        if not url:
            self._show_notice('请填写要发送请求的 API 地址')
            self.url_edit.setFocus()
            return None

        body = self.body_edit.toPlainText().strip()
        if body:
            try:
                json.loads(body)
            except json.JSONDecodeError as e:
                self._show_notice(f'JSON 格式有误：第 {e.lineno} 行，第 {e.colno} 列')
                self.body_edit.setFocus()
                return None

        data['url'] = url
        data['body'] = body
        return data

    def _on_send(self):
        if not self.send_btn.isEnabled():
            return
        data = self._collect_data()
        if not data:
            return

        # 生成 16 位 AES key（等价于 XTChttp.generate_aes_key，但不走 sys.exit）
        key = str(uuid.uuid4()).replace('-', '')[:16]
        if len(key) != 16:
            self._log('错误：生成请求必须的 AESkey 失败！')
            return

        self.send_btn.setEnabled(False)
        self.send_btn.setText('发送中…')
        self.format_btn.setEnabled(False)
        self.notice.hide()
        self.progress.show()
        self._set_status('正在发送…', 'busy')
        self.response_meta.setText('正在处理…')
        self.json_view.clear()
        self.table_view.clear()
        for page, (title, hint) in zip(self.response_pages, self.empty_labels):
            page.setCurrentIndex(0)
            title.setText('正在等待响应')
            hint.setText('请求处理中，结果将自动显示')
        self._log('开始发送请求…')
        threading.Thread(target=self._worker, args=(data, key), daemon=True).start()

    def _worker(self, data, key):
        """在后台线程执行，禁止直接操作控件，结果统一通过信号投递"""
        start = time.time()
        try:
            http_build = XTCHTTPUtils.Http_Build(data)
            request = http_build.build()
            if not request:
                self.request_failed.emit('请求构建失败！请检查参数和日志', time.time() - start)
                return

            encrypted_request = XTCHTTPUtils.Eebbk.eebbk_Encrypt(
                request, key, data['rsaKey'], data['KeyId'])
            if not encrypted_request:
                self.request_failed.emit('加密请求失败！请检查配置和日志', time.time() - start)
                return

            response = http_build.send(encrypted_request, key)
            if not response:
                self.request_failed.emit('发送请求失败！请检查日志', time.time() - start)
                return

            self.result_ready.emit(response, time.time() - start)
        except Exception as e:
            self.request_failed.emit(f'加密或发送请求时发生错误：{e}', time.time() - start)

    def _on_error(self, message, elapsed):
        """失败回调（GUI 线程）"""
        self._finish_request()
        self._set_status('请求失败', 'error')
        self.response_meta.setText(f'{elapsed * 1000:.0f} ms · 未完成')
        self.notice_label.setText('请求未完成，请在日志中查看详情后重试。')
        self.notice.show()
        for title, hint in self.empty_labels:
            title.setText('暂未收到响应')
            hint.setText('请检查日志，调整后重新发送')
        self._log('错误：' + message)
        self.tabs.setCurrentIndex(2)
        self.work_scroll.ensureWidgetVisible(self.tabs)

    def _finish_request(self):
        self.send_btn.setEnabled(True)
        self.send_btn.setText('发送请求')
        self.format_btn.setEnabled(True)
        self.progress.hide()

    # ---------- 结果展示 ----------

    def _on_result(self, response, elapsed):
        self._finish_request()

        body = response.get('body')
        self.json_view.setPlainText(
            json.dumps(response, indent=4, ensure_ascii=False))
        if isinstance(body, dict):
            self.table_view.setPlainText(XTChttp.display_body_as_table(body))
        else:
            self.table_view.setPlainText(json.dumps(body, indent=4, ensure_ascii=False))

        for page in self.response_pages:
            page.setCurrentIndex(1)
        self.tabs.setCurrentIndex(0)
        self.work_scroll.ensureWidgetVisible(self.tabs)

        code = response.get('code')
        self.response_meta.setText(f'{elapsed * 1000:.0f} ms · {code if code is not None else "无状态码"}')
        if code != '000001':
            self._set_status('响应异常', 'warning')
            self._log(f'警告：状态码 {code}，API 返回结果异常')
        else:
            self._set_status('请求成功', 'success')
            self._log(f'请求成功！状态码 {code}')

    # ---------- 日志 ----------

    def _append_log(self, message):
        text = ANSI_RE.sub('', message).rstrip('\r')
        if text:
            self.log_view.appendPlainText(text)

    def _log(self, message):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._log_emitter.message.emit(f'{timestamp} {message}')

    def closeEvent(self, event):
        # 恢复 stdout，避免关闭后残留重定向
        try:
            self._stdout_redirect.__exit__(None, None, None)
        except Exception:
            pass
        super().closeEvent(event)


def start():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName('XTC-Request-Encrypt')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
