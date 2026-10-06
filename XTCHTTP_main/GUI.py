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

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import XTCHTTPUtils
from XTCHTTPUtils.Get_data import create_data_file
from XTCHTTP_main import XTChttp

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
        self.resize(920, 760)

        self._log_emitter = LogEmitter()
        self._log_emitter.message.connect(self._append_log)
        # 把底层库 Logger 的 print 输出（stdout）重定向到日志面板
        self._stdout_redirect = contextlib.redirect_stdout(
            _LogStream(self._log_emitter.message.emit))
        self._stdout_redirect.__enter__()

        self._fields = {}
        self._build_ui()
        self.result_ready.connect(self._on_result)
        self.request_failed.connect(self._on_error)

        self._load_config()
        self.status_label.setText('就绪')
        self._log('欢迎使用小天才请求加密工具！')

    # ---------- 界面搭建 ----------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # 先创建响应/日志视图（请求区的「清空日志」按钮需要引用 log_view）
        self.tabs = QTabWidget()
        self.json_view = self._make_readonly_text()
        self.table_view = self._make_readonly_text()
        self.log_view = self._make_readonly_text()
        self.tabs.addTab(self.json_view, '响应 JSON')
        self.tabs.addTab(self.table_view, '响应 表格')
        self.tabs.addTab(self.log_view, '日志')

        splitter = QSplitter(Qt.Orientation.Vertical)

        # 上半部分：配置区 + 请求区
        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)

        top_layout.addWidget(self._build_config_group())
        top_layout.addWidget(self._build_request_group())
        splitter.addWidget(top)

        splitter.addWidget(self.tabs)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter)

        # 状态栏
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)

    def _build_config_group(self):
        group = QGroupBox('设备配置（与 data.json 对应）')
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        for key in ['watchid', 'bindnumber', 'chipid', 'KeyId', 'model']:
            edit = QLineEdit()
            edit.setPlaceholderText('请输入 ' + key)
            self._fields[key] = edit
            form.addRow(key + '：', edit)

        rsa_edit = QPlainTextEdit()
        rsa_edit.setFixedHeight(64)
        rsa_edit.setPlaceholderText('请输入 rsaKey（RSA 公钥）')
        self._fields['rsaKey'] = rsa_edit
        form.addRow('rsaKey：', rsa_edit)

        save_btn = QPushButton('保存配置')
        save_btn.clicked.connect(self._save_config)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        form.addRow('', btn_row)
        return group

    def _build_request_group(self):
        group = QGroupBox('请求')
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText('例如：https://api.okii.com/...')
        form.addRow('URL：', self.url_edit)

        self.body_edit = QPlainTextEdit()
        self.body_edit.setFont(mono_font())
        self.body_edit.setFixedHeight(110)
        self.body_edit.setPlaceholderText('请求 body（JSON 格式，可为空）')
        form.addRow('Body：', self.body_edit)

        self.send_btn = QPushButton('发送请求')
        self.send_btn.clicked.connect(self._on_send)
        clear_btn = QPushButton('清空日志')
        clear_btn.clicked.connect(self.log_view.clear)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(self.send_btn)
        form.addRow('', btn_row)
        return group

    def _make_readonly_text(self):
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(mono_font())
        return text

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
            self._log('配置已保存到 data.json')
        except OSError as e:
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
            self._log('错误：以下配置项为空，请先填写并保存配置：' + ', '.join(missing))
            return None

        url = self.url_edit.text().strip()
        if not url:
            self._log('错误：URL 不能为空')
            return None

        body = self.body_edit.toPlainText().strip()
        if body:
            try:
                json.loads(body)
            except json.JSONDecodeError as e:
                self._log(f'错误：body 不是合法的 JSON —— {e}')
                return None

        data['url'] = url
        data['body'] = body
        return data

    def _on_send(self):
        data = self._collect_data()
        if not data:
            return

        # 生成 16 位 AES key（等价于 XTChttp.generate_aes_key，但不走 sys.exit）
        key = str(uuid.uuid4()).replace('-', '')[:16]
        if len(key) != 16:
            self._log('错误：生成请求必须的 AESkey 失败！')
            return

        self.send_btn.setEnabled(False)
        self.status_label.setText('发送中…')
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
        self.send_btn.setEnabled(True)
        self.status_label.setText(f'失败（{elapsed * 1000:.0f} ms）')
        self._log('错误：' + message)

    # ---------- 结果展示 ----------

    def _on_result(self, response, elapsed):
        self.send_btn.setEnabled(True)
        self.status_label.setText(f'完成（{elapsed * 1000:.0f} ms）')

        body = response.get('body')
        self.json_view.setPlainText(
            json.dumps(response, indent=4, ensure_ascii=False))
        if isinstance(body, dict):
            self.table_view.setPlainText(XTChttp.display_body_as_table(body))
        else:
            self.table_view.setPlainText(json.dumps(body, indent=4, ensure_ascii=False))

        code = response.get('code')
        if code != '000001':
            self._log(f'警告：状态码 {code}，API 返回结果异常')
        else:
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
    app.setApplicationName('XTC-Request-Encrypt')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
