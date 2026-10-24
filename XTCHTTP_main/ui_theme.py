"""桌面工作台的配色与原生矢量图标，无额外资源依赖。"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


STYLESHEET = """
QMainWindow, QWidget#workspace, QSplitter#requestWorkspace { background: #f3f6f8; }
QWidget { color: #243449; font-size: 13px; }
QLabel { background: transparent; }
QLabel#brandMark {
    background: #0d887b; color: white; border-radius: 15px;
    font-size: 17px; font-weight: 700;
}
QLabel#pageTitle { font-size: 23px; font-weight: 700; color: #152d3b; }
QLabel#subtitle, QLabel[role="muted"] { color: #6b7d8e; font-size: 12px; }
QLabel[role="sectionTitle"] { font-size: 16px; font-weight: 700; color: #203749; }
QLabel[role="fieldLabel"] { font-size: 12px; color: #586a7b; }
QLabel[role="eyebrow"] { font-size: 10px; font-weight: 700; color: #81929f; }
QLabel[role="iconBadge"] { background: #edf6f4; border-radius: 12px; }
QLabel#statusBadge {
    background: #e6efed; color: #397368; border: 1px solid #d7e7e2;
    border-radius: 15px; padding: 7px 14px; font-size: 12px; font-weight: 600;
}
QLabel#statusBadge[tone="busy"] { background: #e8f2ff; color: #3268a3; border-color: #d5e6f8; }
QLabel#statusBadge[tone="success"] { background: #e3f5ec; color: #21734f; border-color: #cde9da; }
QLabel#statusBadge[tone="error"] { background: #fff0ed; color: #b35145; border-color: #f3d9d2; }
QLabel#statusBadge[tone="warning"] { background: #fff5df; color: #977030; border-color: #f0e2bd; }
QLabel#methodBadge {
    background: #e8f5f0; color: #16806c; border-radius: 9px;
    padding: 8px 12px; font-size: 11px; font-weight: 700;
}
QFrame[role="card"] { background: #ffffff; border: 1px solid #e2e9ee; border-radius: 20px; }
QFrame#requestNotice {
    background: #fff4ec; border: 1px solid #f3dfce; border-radius: 10px;
}
QFrame#requestNotice QLabel { color: #946137; font-size: 12px; }
QFrame#configFooter { background: #f5f8fa; border: none; border-radius: 12px; }
QScrollArea { background: transparent; border: none; }
QWidget#configFields { background: transparent; }
QLineEdit, QPlainTextEdit {
    background: #f8fafc; color: #293b50; border: 1px solid #e3eaf0;
    border-radius: 10px; padding: 9px 11px;
    selection-background-color: #cbece3; selection-color: #163e38;
}
QLineEdit:hover, QPlainTextEdit:hover { border-color: #c5d6d9; }
QLineEdit:focus, QPlainTextEdit:focus { background: #ffffff; border: 1px solid #26a592; }
QLineEdit:disabled, QPlainTextEdit:disabled { color: #93a1ae; background: #f1f4f7; }
QPlainTextEdit[role="result"] { background: #f8fafc; border: none; border-radius: 12px; padding: 12px; }
QPushButton {
    background: #ffffff; color: #465d6d; border: 1px solid #dce5eb;
    border-radius: 10px; padding: 9px 15px; font-weight: 600;
}
QPushButton:hover { background: #eff7f5; border-color: #b8d8cf; color: #167b6b; }
QPushButton:pressed { background: #e1f0eb; }
QPushButton:focus { border: 1px solid #26a592; }
QPushButton:disabled { background: #f2f5f7; color: #98a6b3; border-color: #e8edf1; }
QPushButton[role="primary"] {
    background: #0d887b; border-color: #0d887b; color: #ffffff;
    border-radius: 11px; padding: 10px 23px;
}
QPushButton[role="primary"]:hover { background: #09776c; border-color: #09776c; }
QPushButton[role="primary"]:pressed { background: #08675e; border-color: #08675e; }
QPushButton[role="primary"]:focus { border: 1px solid #07564f; }
QPushButton[role="primary"]:disabled { background: #8bbdb3; border-color: #8bbdb3; color: #ffffff; }
QPushButton[role="ghost"] {
    background: transparent; border: 1px solid transparent; padding: 6px 10px;
    color: #748595; font-size: 12px; font-weight: 400; border-radius: 8px;
}
QPushButton[role="ghost"]:hover { background: #edf5f2; color: #167b6b; }
QPushButton[role="ghost"]:focus { border-color: #26a592; }
QPushButton[role="ghost"]:disabled { color: #afbac4; }
QTabWidget::pane { border: none; background: transparent; top: 8px; }
QTabBar::tab {
    background: transparent; color: #7c8c9b; border: none;
    border-radius: 9px; padding: 8px 17px; margin-right: 5px;
}
QTabBar::tab:selected { background: #eaf5f1; color: #147d6c; font-weight: 600; }
QTabBar::tab:hover:!selected { background: #f1f5f7; color: #4e6573; }
QTabBar::tab:focus { border: 1px solid #26a592; }
QWidget#emptyState { background: #f8fafc; border-radius: 12px; }
QLabel#emptyTitle { color: #647a89; font-size: 14px; font-weight: 600; }
QProgressBar { background: #e8f1ed; border: none; border-radius: 2px; }
QProgressBar::chunk { background: #2aa58d; border-radius: 2px; }
QSplitter::handle { background: transparent; }
QSplitter::handle:hover { background: #d9e8e3; border-radius: 3px; }
QScrollBar:vertical { background: transparent; width: 6px; margin: 4px 0; }
QScrollBar::handle:vertical { background: #cbd7df; min-height: 28px; border-radius: 3px; }
QScrollBar::handle:vertical:hover { background: #9eb6bb; }
QScrollBar:horizontal { background: transparent; height: 6px; margin: 0 4px; }
QScrollBar::handle:horizontal { background: #cbd7df; min-width: 28px; border-radius: 3px; }
QScrollBar::handle:horizontal:hover { background: #9eb6bb; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QToolTip { background: #243e49; color: #ffffff; border: none; padding: 6px 9px; }
"""


def icon(name, color='#628279', size=20):
    """绘制小型线条图标；使用双倍分辨率，在高 DPI 屏幕上保持清晰。"""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 24, size / 24)
    painter.setPen(QPen(QColor(color), 1.7, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    path = QPainterPath()
    if name == 'device':
        painter.drawRoundedRect(QRectF(6, 5, 12, 14), 3, 3)
        painter.drawLine(QPointF(9, 2), QPointF(15, 2))
        painter.drawLine(QPointF(9, 22), QPointF(15, 22))
        painter.drawLine(QPointF(12, 9), QPointF(12, 12))
        painter.drawLine(QPointF(12, 12), QPointF(14, 13))
    elif name == 'send':
        path.moveTo(3, 10)
        for x, y in [(21, 3), (14, 21), (11, 13), (3, 10)]:
            path.lineTo(x, y)
        path.moveTo(11, 13)
        path.lineTo(21, 3)
    elif name == 'copy':
        painter.drawRoundedRect(QRectF(8, 8, 12, 13), 2, 2)
        path.moveTo(15, 5)
        path.lineTo(15, 3)
        path.lineTo(3, 3)
        path.lineTo(3, 16)
        path.lineTo(5, 16)
    elif name == 'save':
        painter.drawRoundedRect(QRectF(4, 3, 16, 18), 2, 2)
        painter.drawRect(QRectF(8, 3, 8, 6))
        painter.drawRect(QRectF(8, 14, 8, 7))
    elif name == 'response':
        painter.drawRoundedRect(QRectF(3, 4, 18, 16), 3, 3)
        path.moveTo(7, 9)
        path.lineTo(10, 12)
        path.lineTo(7, 15)
        path.moveTo(13, 15)
        path.lineTo(17, 15)
    painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)
