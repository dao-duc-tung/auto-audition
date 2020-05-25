from PIL import Image
import cv2
import mss
import numpy as np
import time

from .sct_img import SctImg


def show(cv_img):
    Image.fromarray(cv_img).show()


def line(gray, p1, p2, color=255):
    clone = gray.copy()
    cv2.line(clone, p1, p2, color, 1)
    return clone


def rect(gray, x, y, w, h, color=255):
    clone = gray.copy()
    cv2.rectangle(clone, (x, y), (x + w, y + h), color, 1)
    return clone


def to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)


def capture(area) -> SctImg:
    with mss.mss() as sct:
        capture_time = time.time()
        img = np.array(sct.grab(area))[:, :, :3]
        sct_img = SctImg(img, capture_time)
    return sct_img
