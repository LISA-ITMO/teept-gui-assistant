import torch
from PyQt5 import QtCore
from dotenv import load_dotenv

load_dotenv('.env')

# Настройки сервера
SERVER_URL = 'https://jgsnapp.ru/gpt'

# Настройки модели CLIP
CLIP_MODEL_NAME = "ViT-B/32"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Настройки оверлея
OVERLAY = {
    'SEARCH_AREA_COLOR': (0, 255, 0),  # Цвет области поиска (RGB)
    'FOUND_ELEMENT_COLOR': (255, 0, 0),  # Цвет найденных элементов (RGB)
    'FONT_SIZE': 12,
    'PADDING': 10,
    'DASH_LINE': QtCore.Qt.DashLine,
    'LINE_WIDTH': {
        'SEARCH': 2,
        'ELEMENT': 3
    }
}

# Настройки сетки и скриншотов
GRID = {
    'COLUMNS': 3,
    'ROWS': 3,
    'LINE_COLOR': 'red',
    'LINE_WIDTH': 2,
    'FONT_SIZE': 36,
    'FONT_NAME': 'arial.ttf'
}

# Настройки мониторинга действий
MONITOR = {
    'TIMER_DURATION': 2.0,  # В секундах
    'GRID_DIVISIONS': 3
}

# Транслитерация
TRANSLIT_DICT = str.maketrans(
    "AЕKМНОРСТУХaеорсух",
    "АЕКМНОРСТУХаеорсух"
)