from os.path import join as pjoin
import cv2
import os
import numpy as np


def resize_height_by_longest_edge(image, resize_length=800):
    if isinstance(image, str):  # Если передан путь к файлу
        image = cv2.imread(image)
    height, width = image.shape[:2]
    if height > width:
        return resize_length
    else:
        return int(resize_length * (height / width))


def color_tips():
    color_map = {'Text': (0, 0, 255), 'Compo': (0, 255, 0), 'Block': (0, 255, 255), 'Text Content': (255, 0, 255)}
    board = np.zeros((200, 200, 3), dtype=np.uint8)

    board[:50, :, :] = (0, 0, 255)
    board[50:100, :, :] = (0, 255, 0)
    board[100:150, :, :] = (255, 0, 255)
    board[150:200, :, :] = (0, 255, 255)
    cv2.putText(board, 'Text', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.putText(board, 'Non-text Compo', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.putText(board, "Compo's Text Content", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.putText(board, "Block", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.imshow('colors', board)


def run_uied(input_img, output_root='data/output'):
    # Define or import the classifier here
    classifier = None  # Initialize or load your classifier
    if isinstance(input_img, str):  # Check if the input is a file path or image
        image = cv2.imread(input_img)
    else:
        image = input_img  # If an image object is passed

    key_params = {
        'min-grad': 10,
        'ffl-block': 5,
        'min-ele-area': 50,
        'merge-contained-ele': True,
        'merge-line-to-paragraph': False,
        'remove-bar': True
    }
    
    resized_height = resize_height_by_longest_edge(image, resize_length=800)
    #color_tips()

    import detect_text.text_detection as text
    text_json = text.text_detection(image, show=False, method='paddle')

    import detect_compo.ip_region_proposal as ip
    compo_json = ip.compo_detection(image, key_params,
                                    classifier=classifier, resize_by_height=resized_height, show=False)

    import detect_merge.merge as merge
    res, components, img_resize = merge.merge(image, compo_json, text_json,
                                  is_remove_bar=key_params['remove-bar'], 
                                  is_paragraph=key_params['merge-line-to-paragraph'], 
                                  show=False)

    return res, components, img_resize
