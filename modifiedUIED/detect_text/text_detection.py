import detect_text.ocr as ocr
from detect_text.Text import Text
import numpy as np
import cv2
import json
import os
from os.path import join as pjoin


def save_detection_json(texts, img_shape):
    output = {'img_shape': img_shape, 'texts': []}
    for text in texts:
        c = {'id': text.id, 'content': text.content}
        loc = text.location
        c['column_min'], c['row_min'], c['column_max'], c['row_max'] = loc['left'], loc['top'], loc['right'], loc['bottom']
        c['width'] = text.width
        c['height'] = text.height
        output['texts'].append(c)
    return output

def visualize_texts(org_img, texts, shown_resize_height=None, show=False, write_path=None):
    img = org_img.copy()
    for text in texts:
        text.visualize_element(img, line=2)

    img_resize = img
    if shown_resize_height is not None:
        img_resize = cv2.resize(img, (int(shown_resize_height * (img.shape[1]/img.shape[0])), shown_resize_height))

    if show:
        cv2.imshow('texts', img_resize)
        cv2.waitKey(0)
        cv2.destroyWindow('texts')
    if write_path is not None:
        cv2.imwrite(write_path, img)

def text_sentences_recognition(texts):
    '''
    Merge separate words detected by Google ocr into a sentence
    '''
    changed = True
    while changed:
        changed = False
        temp_set = []
        for text_a in texts:
            merged = False
            for text_b in temp_set:
                if text_a.is_on_same_line(text_b, 'h', bias_justify=0.2 * min(text_a.height, text_b.height), bias_gap=2 * max(text_a.word_width, text_b.word_width)):
                    text_b.merge_text(text_a)
                    merged = True
                    changed = True
                    break
            if not merged:
                temp_set.append(text_a)
        texts = temp_set.copy()

    for i, text in enumerate(texts):
        text.id = i
    return texts


def merge_intersected_texts(texts):
    '''
    Merge intersected texts (sentences or words)
    '''
    changed = True
    while changed:
        changed = False
        temp_set = []
        for text_a in texts:
            merged = False
            for text_b in temp_set:
                if text_a.is_intersected(text_b, bias=2):
                    text_b.merge_text(text_a)
                    merged = True
                    changed = True
                    break
            if not merged:
                temp_set.append(text_a)
        texts = temp_set.copy()
    return texts


def text_cvt_orc_format(ocr_result):
    texts = []
    if ocr_result is not None:
        for i, result in enumerate(ocr_result):
            error = False
            x_coordinates = []
            y_coordinates = []
            text_location = result['boundingPoly']['vertices']
            content = result['description']
            for loc in text_location:
                if 'x' not in loc or 'y' not in loc:
                    error = True
                    break
                x_coordinates.append(loc['x'])
                y_coordinates.append(loc['y'])
            if error: continue
            location = {'left': min(x_coordinates), 'top': min(y_coordinates),
                        'right': max(x_coordinates), 'bottom': max(y_coordinates)}
            texts.append(Text(i, content, location))
    return texts


def text_cvt_orc_format_paddle(paddle_result):
    texts = []
    for i, line in enumerate(paddle_result):
        try:
            for element in line:  # Перебираем каждый элемент строки
                points = np.array(element[0])
                location = {
                    'left': int(min(points[:, 0])),
                    'top': int(min(points[:, 1])),
                    'right': int(max(points[:, 0])),
                    'bottom': int(max(points[:, 1]))
                }
                content = element[1][0]  # Содержание текста
                texts.append(Text(i, content, location))
        except Exception as e:
            print(f"Ошибка при обработке строки {i}: {e}")
    return texts



def text_filter_noise(texts):
    valid_texts = []
    for text in texts:
        if len(text.content) <= 1 and text.content.lower() not in ['a', ',', '.', '!', '?', '$', '%', ':', '&', '+']:
            continue
        valid_texts.append(text)
    return valid_texts
    

def text_detection(input_img='../data/input/30800.jpg', show=False, method='google', paddle_model=None):
    if isinstance(input_img, str):  # Если передан путь к файлу
        img = cv2.imread(input_img)
        name = input_img.split('/')[-1][:-4]
    else:  # Если передано изображение в формате numpy array
        img = input_img
        name = 'captured_image'  # Имя по умолчанию

    if method == 'google':
        print('*** Detect Text through Google OCR ***')
        ocr_result = ocr.ocr_detection_google(img if isinstance(input_img, np.ndarray) else input_img)
        texts = text_cvt_orc_format(ocr_result)
        texts = merge_intersected_texts(texts)
        texts = text_filter_noise(texts)
        texts = text_sentences_recognition(texts)
    elif method == 'paddle':
        from paddleocr import PaddleOCR
        print('*** Detect Text through Paddle OCR ***')
        if paddle_model is None:
            paddle_model = PaddleOCR(use_angle_cls=True, lang="cyrillic")
        result = paddle_model.ocr(img if isinstance(input_img, np.ndarray) else input_img, cls=True)
        texts = text_cvt_orc_format_paddle(result)
    else:
        raise ValueError('Method has to be "google" or "paddle"')

    #visualize_texts(img, texts, shown_resize_height=800, show=show, write_path=pjoin(ocr_root, name + '.png'))
    arr = save_detection_json(texts, img.shape)
    #print("Input: %s Output: %s" % (name, pjoin(ocr_root, name + '.json')))
    return arr
