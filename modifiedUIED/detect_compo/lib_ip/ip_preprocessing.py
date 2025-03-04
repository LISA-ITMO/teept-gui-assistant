import cv2
import numpy as np
from UIED_config.CONFIG_UIED import Config
C = Config()

def resize_img(img, resize_height):
    w_h_ratio = img.shape[1] / img.shape[0]
    resize_w = int(resize_height * w_h_ratio)
    resized_img = cv2.resize(img, (resize_w, resize_height))
    return resized_img

def read_img(input_img, resize_height=None, kernel_size=None):
    """
    Reads and processes an image from a file path or directly from an image array.
    - Resizes image by height if specified.
    - Converts to grayscale.
    """
    def resize_by_height(org):
        return resize_img(org, resize_height)

    try:
        if isinstance(input_img, str):  # Check if input is a file path
            img = cv2.imread(input_img)
            if img is None:
                print("*** Image does not exist ***")
                return None, None
        else:
            img = input_img.copy()

        if kernel_size is not None:
            img = cv2.medianBlur(img, kernel_size)
        
        if resize_height is not None:
            img = resize_by_height(img)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img, gray

    except Exception as e:
        print(e)
        print("*** Image Reading Failed ***\n")
        return None, None



def gray_to_gradient(img):
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_f = np.copy(img)
    img_f = img_f.astype("float")

    kernel_h = np.array([[0,0,0], [0,-1.,1.], [0,0,0]])
    kernel_v = np.array([[0,0,0], [0,-1.,0], [0,1.,0]])
    dst1 = abs(cv2.filter2D(img_f, -1, kernel_h))
    dst2 = abs(cv2.filter2D(img_f, -1, kernel_v))
    gradient = (dst1 + dst2).astype('uint8')
    return gradient


def reverse_binary(bin, show=False):
    """
    Reverse the input binary image
    """
    r, bin = cv2.threshold(bin, 1, 255, cv2.THRESH_BINARY_INV)
    if show:
        cv2.imshow('binary_rev', bin)
        cv2.waitKey()
    return bin


def binarization(org, grad_min, show=False, write_path=None, wait_key=0):
    grey = cv2.cvtColor(org, cv2.COLOR_BGR2GRAY)
    grad = gray_to_gradient(grey)        # get RoI with high gradient
    rec, binary = cv2.threshold(grad, grad_min, 255, cv2.THRESH_BINARY)    # enhance the RoI
    morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, (3, 3))  # remove noises
    if write_path is not None:
        cv2.imwrite(write_path, morph)
    if show:
        cv2.imshow('binary', morph)
        if wait_key is not None:
            cv2.waitKey(wait_key)
    return morph
