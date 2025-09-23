import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import win32gui
import win32con
import win32api

class OverlayWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Overlay")
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 400, 300)

        # 吹き出しテキスト
        self.text = "こんにちは！"

        # キャラクター画像
        self.image = QtGui.QPixmap("character.png").scaled(100, 100, QtCore.Qt.KeepAspectRatio)

        # タイマーで定期再描画（必要なら）
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

        # ↓ ウィンドウをマウス透過にする（必要なら）
        self.make_window_clickthrough()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        # キャラ描画
        painter.drawPixmap(50, 150, self.image)

        # 吹き出し（背景）
        bubble_rect = QtCore.QRect(160, 50, 200, 100)
        painter.setBrush(QtGui.QColor(255, 255, 255, 230))
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 2))
        painter.drawRoundedRect(bubble_rect, 10, 10)

        # 吹き出しテキスト
        painter.setPen(QtCore.Qt.black)
        painter.setFont(QtGui.QFont("Arial", 12))
        painter.drawText(bubble_rect, QtCore.Qt.AlignCenter, self.text)

    def make_window_clickthrough(self):
        hwnd = self.winId().__int__()
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
        win32gui.SetLayeredWindowAttributes(hwnd, 0x00ffffff, 255, win32con.LWA_COLORKEY)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OverlayWindow()
    window.show()
    sys.exit(app.exec_())
