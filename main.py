import requests  
import pyautogui
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import cv2
import clip
import difflib
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import ctypes
import win32con
import threading
import time
import screeninfo
import os
import json
import torch
from screenshot import take_screenshot, display_sent_image
from gui import Overlay, app
from monitor import monitor_user_action
from config import (
    SERVER_URL,
    CLIP_MODEL_NAME,
    DEVICE,
    TRANSLIT_DICT,
    GRID,
    OVERLAY
)


# Получаем абсолютный путь к папке other
other_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "modifiedUIED"))
# Добавляем его в начало sys.path
sys.path.insert(0, other_dir)

# Импортируем нужную функцию из a.py
from uied_api import run_uied

os.environ['NO_PROXY'] = SERVER_URL

model, preprocess = clip.load(CLIP_MODEL_NAME, device=DEVICE)

# Словарь замен для транслитерации
translit_dict = str.maketrans(
    "AЕKМНОРСТУХaеорсух",
    "АЕКМНОРСТУХаеорсух"
)

def transliterate_text(text):
    return text.translate(translit_dict)

def find_closest_text_match(target, components):
    target_translit = transliterate_text(target)
    best_match, max_similarity = None, -1

    for comp in components['compos']:
        if 'text_content' in comp:
            text_translit = transliterate_text(comp['text_content'])
            similarity = difflib.SequenceMatcher(None, target_translit, text_translit).ratio()
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = comp

    return best_match, max_similarity

def tryTofind(top, left, width, height, sct_img, description, mode, grid_x, grid_y):
    action_completed = False
    user_input = description
    description_features = None
    if mode == "1":
        search_mode = 'text'
    elif mode == "2":
        search_mode = 'image'
        text = clip.tokenize([user_input]).to(device=DEVICE)
        with torch.no_grad():
            description_features = model.encode_text(text)
            description_features /= description_features.norm(dim=-1, keepdim=True)
    else:
        print("Некорректный ввод, попробуйте снова.")
        return

    try:
        # Обрезаем скриншот до области поиска
        sct_img_cropped = sct_img.crop((int(left), int(top), int(left + width), int(top + height)))
        sct_img_np = np.array(sct_img_cropped)
        sct_img_bgr = cv2.cvtColor(sct_img_np, cv2.COLOR_RGB2BGR)  # Конвертируем из RGB в BGR

        # Создаем прямоугольник области поиска
        search_area_rect = QtCore.QRect(int(left), int(top), int(width), int(height))

        res, components, img_resize = run_uied(sct_img_bgr)

        original_width = sct_img_bgr.shape[1]
        original_height = sct_img_bgr.shape[0]
        resize_width = img_resize.shape[1]
        resize_height = img_resize.shape[0]

        scale_x = original_width / resize_width
        scale_y = original_height / resize_height

        if search_mode == 'text':
            best_text_comp, max_similarity = find_closest_text_match(user_input, components)
            if best_text_comp:
                # Преобразование координат компонента в координаты экрана
                if 'position' in best_text_comp:
                    pos = best_text_comp['position']
                    padding = 10
                    comp_left = (pos['column_min'] - padding) * scale_x + left
                    comp_top = (pos['row_min'] - padding) * scale_y + top
                    comp_right = (pos['column_max'] + padding) * scale_x + left
                    comp_bottom = (pos['row_max'] + padding) * scale_y + top
                    rectangle = QtCore.QRect(int(comp_left), int(comp_top),
                                             int(comp_right - comp_left), int(comp_bottom - comp_top))
                    # Создаем словарь элемента
                    element = {
                        'rect': rectangle,
                        'similarity': max_similarity,
                        'text_content': best_text_comp.get('text_content', '')
                    }
                    # Создаем элемент для области поиска
                    search_area_element = {'rect': search_area_rect, 'is_search_area': True}
                    elements = [search_area_element, element]

                    overlay = Overlay(elements)
                    app.processEvents()
                    overlay.show()

                    # Создаем событие и поток для ожидания ввода
                    def wait_for_input(event):
                        nonlocal action_completed
                        action_completed = monitor_user_action(grid_x, grid_y)
                        event.set()

                    input_event = threading.Event()
                    input_thread = threading.Thread(target=wait_for_input, args=(input_event,))
                    input_thread.start()

                    # Цикл обработки событий GUI
                    while not input_event.is_set():
                        app.processEvents()
                        time.sleep(0.1)

                    overlay.close()
                    return action_completed
                else:
                    print("Позиция элемента не найдена.")
            else:
                print("Элемент не найден.")
        elif search_mode == 'image' and description_features is not None:
            max_similarity, best_component = -1, None
            padding = 10  # Отступ для рамок
            for comp in components['compos']:
                if 'position' in comp:
                    pos = comp['position']
                    top_left = (pos['column_min'] - padding, pos['row_min'] - padding)
                    bottom_right = (pos['column_max'] + padding, pos['row_max'] + padding)
                    padded_img = img_resize[max(0, int(top_left[1])):min(img_resize.shape[0], int(bottom_right[1])),
                                            max(0, int(top_left[0])):min(img_resize.shape[1], int(bottom_right[0]))]
                    component_img_pil = Image.fromarray(padded_img)
                    component_img_tensor = preprocess(component_img_pil).unsqueeze(0).to(device=DEVICE)
                    with torch.no_grad():
                        comp_features = model.encode_image(component_img_tensor)
                        comp_features /= comp_features.norm(dim=-1, keepdim=True)
                    similarity = (comp_features @ description_features.T).item()
                    if similarity > max_similarity:
                        max_similarity = similarity
                        best_component = comp

            if best_component:
                # Преобразование координат компонента в координаты экрана
                pos = best_component['position']
                comp_left = (pos['column_min'] - padding) * scale_x + left
                comp_top = (pos['row_min'] - padding) * scale_y + top
                comp_right = (pos['column_max'] + padding) * scale_x + left
                comp_bottom = (pos['row_max'] + padding) * scale_y + top
                rectangle = QtCore.QRect(int(comp_left), int(comp_top),
                                         int(comp_right - comp_left), int(comp_bottom - comp_top))
                # Создаем словарь элемента
                element = {
                    'rect': rectangle,
                    'similarity': max_similarity,
                    'text_content': best_component.get('text_content', '')
                }
                search_area_element = {'rect': search_area_rect, 'is_search_area': True}
                elements = [search_area_element, element]
                overlay = Overlay(elements)
                app.processEvents()
                overlay.show()

                def wait_for_input(event):
                    nonlocal action_completed
                    action_completed = monitor_user_action(grid_x, grid_y)
                    event.set()

                input_event = threading.Event()
                input_thread = threading.Thread(target=wait_for_input, args=(input_event,))
                input_thread.start()

                # Цикл обработки событий GUI
                while not input_event.is_set():
                    app.processEvents()
                    time.sleep(0.1)

                overlay.close()
                return action_completed
            else:
                print("Совпадений с изображением не найдено.")
    except Exception as e:
        print(f"Ошибка при выполнении поиска: {e}")

    return False

def main():
    server_url = SERVER_URL

    # Инициализируем историю сообщений
    conversation_history = []

    # Получить задачу от пользователя
    user_task = input("Введите запрос: ")
    conversation_history.append({'role': 'user', 'content': user_task})

    # Получить размеры экрана
    screen_size = pyautogui.size()
    width, height = screen_size.width, screen_size.height

    # Получаем размеры экрана для мониторинга событий
    screen = screeninfo.get_monitors()[0]
    SCREEN_WIDTH = screen.width
    SCREEN_HEIGHT = screen.height

    # Отправить первый запрос на сервер для получения плана и первого шага
    screenshot, screenshot_buffer = take_screenshot()

    files = {
        'screenshot': ('screenshot.jpg', screenshot_buffer, 'image/jpeg')
    }
    data = {
        'conversation_history': conversation_history
    }

    response = requests.post(f"{server_url}/get_plan", data=data, files=files, verify=False)
    if response.status_code == 200:
        # Отображаем изображение после отправки на сервер
        display_sent_image(screenshot)

        result = response.json()
        plan = result.get('plan')
        conversation_history.append({'role': 'assistant', 'content': plan})
        isTaskCompleted = result.get('isTaskCompleted')
        answer = result.get('answer')
        conversation_history.append({'role': 'assistant', 'content': answer})
        action = result.get('action')
        grid_x = result.get('grid_x')
        grid_y = result.get('grid_y')
        mode = result.get('mode')
        description = result.get('description')

        if plan:
            print(f"План действий:\n{plan}\n")
            print(f"Инструкция: {answer}")
            print(f"Действие: {action}")
            print(f"Описание: {description}")
            print(f"Расположение на экране - по ширине: {grid_x}, по высоте: {grid_y} (сетка 3x3)")
        else:
            print("Не удалось получить план действий.")
            return
    else:
        print("Ошибка при соединении с сервером.")
        print("Код состояния:", response.status_code)
        print("Ответ сервера:", response.text)
        return

    while not isTaskCompleted:
        # Проверяем и преобразуем grid_x и grid_y в числа
        grid_x = int(grid_x) if grid_x is not None else 2
        grid_y = int(grid_y) if grid_y is not None else 2

        # Вывести инструкции
        print(f"Инструкция: {answer}")
        print(f"Действие: {action}")
        print(f"Описание: {description}")
        print(f"Расположение на экране - по ширине: {grid_x}, по высоте: {grid_y} (сетка 3x3)")

        # Вычисляем координаты области
        area_width = width / GRID['COLUMNS']
        area_height = height / GRID['ROWS']
        left = (grid_x - 1) * area_width
        top = (grid_y - 1) * area_height

        # Показываем оверлей с подсказкой
        action_completed = tryTofind(top, left, area_width, area_height, screenshot, description, mode, grid_x, grid_y)

        if action_completed:
            # Пользователь выполнил действие, переходим к следующему шагу
            screenshot, screenshot_buffer = take_screenshot()

            files = {
                'screenshot': ('screenshot.jpg', screenshot_buffer, 'image/jpeg')
            }

            data = {
                'conversation_history': json.dumps(conversation_history)
            }

            response = requests.post(f"{server_url}/get_plan", data=data, files=files, verify=False)
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer')
                conversation_history.append({'role': 'assistant', 'content': answer})
                action = result.get('action')
                grid_x = result.get('grid_x')  # 1, 2 или 3
                grid_y = result.get('grid_y')  # 1, 2 или 3
                isTaskCompleted = result.get('isTaskCompleted')
                mode = result.get('mode')
                description = result.get('description')
                plan = result.get('plan', plan)  # Обновляем план, если он изменился

                # Если задача выполнена, сообщаем и выходим
                if isTaskCompleted:
                    print("Задача выполнена!")
                    break
            else:
                print("Ошибка при соединении с сервером.")
                print("Код состояния:", response.status_code)
                print("Ответ сервера:", response.text)
                break
        else:
            print("Действие не выполнено, повторите попытку.")

# Запуск программы
if __name__ == '__main__':
    main()
