import pyautogui
from PIL import Image, ImageDraw, ImageFont
import io
from config import GRID

def take_screenshot():
    # Сделать скриншот
    screenshot = pyautogui.screenshot()

    # Создаем объект для рисования
    draw = ImageDraw.Draw(screenshot)

    # Получаем размеры изображения
    width, height = screenshot.size

    # Вычисляем позиции для линий сетки
    third_width = width // GRID['COLUMNS']
    third_height = height // GRID['ROWS']

    # Рисуем вертикальные линии
    for i in range(1, 3):
        x = i * third_width
        draw.line([(x, 0), (x, height)], fill=GRID['LINE_COLOR'], width=GRID['LINE_WIDTH'])

    # Рисуем горизонтальные линии
    for i in range(1, 3):
        y = i * third_height
        draw.line([(0, y), (width, y)], fill=GRID['LINE_COLOR'], width=GRID['LINE_WIDTH'])

    # Добавляем номера к каждой области
    font_size = 36  # Размер шрифта
    try:
        # Попытка загрузить шрифт Arial
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        # Если не удалось загрузить Arial, используем шрифт по умолчанию
        font = ImageFont.load_default()

    for row in range(3):
        for col in range(3):
            x = col * third_width + third_width // 2
            y = row * third_height + third_height // 2
            text = f"X: {row + 1} Y: {col + 1}"
            text_bbox = font.getbbox(text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = x - text_width // 2
            text_y = y - text_height // 2
            draw.text((text_x, text_y), text, fill='red', font=font)

    # Сохранить измененное изображение в буфер в формате JPEG
    buffered = io.BytesIO()
    screenshot.save(buffered, format="JPEG")
    buffered.seek(0)

    return screenshot, buffered
    
def display_sent_image(screenshot):
    # Отображаем изображение в отдельном окне
    screenshot.show(title="Отправленное изображение")
    