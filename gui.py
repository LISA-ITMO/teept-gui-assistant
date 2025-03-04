from PyQt5 import QtWidgets, QtGui, QtCore
import ctypes
import win32con
import threading
import time
from pynput import mouse, keyboard
import screeninfo
import sys
from config import OVERLAY

class Overlay(QtWidgets.QWidget):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements  # Список словарей с 'rect', 'text_content', 'similarity', 'is_search_area'
        self.setWindowTitle('Overlay')
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.showFullScreen()

        hwnd = self.winId().__int__()
        extendedStyle = ctypes.windll.user32.GetWindowLongW(hwnd, win32con.GWL_EXSTYLE)
        extendedStyle |= win32con.WS_EX_LAYERED
        ctypes.windll.user32.SetWindowLongW(hwnd, win32con.GWL_EXSTYLE, extendedStyle)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        font = QtGui.QFont()
        font.setPointSize(12)
        painter.setFont(font)
        # Рисование прямоугольников и текста
        for elem in self.elements:
            rect = elem['rect']
            if elem.get('is_search_area', False):
                # Устанавливаем кисть для области поиска
                painter.setPen(QtGui.QPen(QtGui.QColor(*OVERLAY['SEARCH_AREA_COLOR']), 
                         OVERLAY['LINE_WIDTH']['SEARCH'], 
                         OVERLAY['DASH_LINE']))

                painter.drawRect(rect)
            else:
                # Устанавливаем кисть для найденных элементов
                painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 3))
                painter.drawRect(rect)
                # Формируем текст для отображения
                texts = []
                if 'similarity' in elem:
                    texts.append(f"Сходство: {elem['similarity']:.2f}")
                if 'text_content' in elem and elem['text_content']:
                    texts.append(f"Текст: {elem['text_content']}")
                if texts:
                    text_str = '\n'.join(texts)
                    # Отрисовка текста рядом с прямоугольником
                    text_rect = QtCore.QRect(rect.right() + 5, rect.top(), 200, 50)
                    painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, text_str)

app = QtWidgets.QApplication(sys.argv)