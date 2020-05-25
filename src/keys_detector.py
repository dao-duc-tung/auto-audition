import cv2
import imutils
import numpy as np

from .utils import *


class KeysDetector:
    KEYS_THRESHOLD = 254
    LEFT = 0
    UP = 1
    RIGHT = 2
    DOWN = 3
    KEY_LEFT = ["{LEFT down}", "{LEFT up}"]
    KEY_UP = ["{UP down}", "{UP up}"]
    KEY_RIGHT = ["{RIGHT down}", "{RIGHT up}"]
    KEY_DOWN = ["{DOWN down}", "{DOWN up}"]

    LOWER_BLUE = np.array([110, 100, 100])
    UPPER_BLUE = np.array([130, 255, 255])
    LOWER_RED = np.array([-10, 100, 100])
    UPPER_RED = np.array([10, 255, 255])

    def __init__(self):
        pass

    def detect(self, orig) -> str:
        keys = []

        try:
            gray = to_gray(orig)
            thres_img = self.threshold_gray(gray)
            cnts = self.find_contours(thres_img)
            (cnts, boundingBoxes) = self.sort_contours(cnts)

            for bb in boundingBoxes:
                key_roi = self.get_key_roi(thres_img, bb)
                color_key_roi = self.get_key_roi(orig, bb)
                direction = self.get_direction(key_roi, color_key_roi)
                key = self.direction_to_key(direction)
                keys.extend(key)

        except Exception as e:
            pass

        return keys

    def threshold_gray(self, gray):
        _, thres = cv2.threshold(
            gray, KeysDetector.KEYS_THRESHOLD, 255, cv2.THRESH_BINARY
        )
        return thres

    def find_contours(self, thres_img):
        cnts = cv2.findContours(
            thres_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cnts = imutils.grab_contours(cnts)
        return cnts

    def sort_contours(self, cnts):
        boundingBoxes = [cv2.boundingRect(c) for c in cnts]
        (cnts, boundingBoxes) = zip(
            *sorted(zip(cnts, boundingBoxes), key=lambda b: b[1][0])
        )

        return (cnts, boundingBoxes)

    def get_key_roi(self, thres_img, boxes):
        res = thres_img[
            boxes[1] : (boxes[1] + boxes[3]), boxes[0] : (boxes[0] + boxes[2])
        ]
        return res

    def get_direction(self, roi, color_key_roi):
        h, w = roi.shape
        reg0 = roi[:, 0 : w // 3]
        reg1 = roi[0 : h // 3, :]
        reg2 = roi[:, 2 * w // 3 : w]
        reg3 = roi[2 * h // 3 : h, :]

        rate0 = cv2.countNonZero(reg0)
        rate1 = cv2.countNonZero(reg1)
        rate2 = cv2.countNonZero(reg2)
        rate3 = cv2.countNonZero(reg3)

        arr = np.array((rate0, rate1, rate2, rate3))
        direction = np.argmax(arr)

        if self.is_reversed(color_key_roi):
            direction = self.reverse_direction(direction)

        return direction

    def is_reversed(self, rgb_key_roi):
        hsv = cv2.cvtColor(rgb_key_roi, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, KeysDetector.LOWER_BLUE, KeysDetector.UPPER_BLUE)
        cnt_blue = cv2.countNonZero(mask)

        mask = cv2.inRange(hsv, KeysDetector.LOWER_RED, KeysDetector.UPPER_RED)
        cnt_red = cv2.countNonZero(mask)

        if cnt_red > cnt_blue:
            return True
        return False

    def reverse_direction(self, direction):
        if direction == KeysDetector.UP:
            return KeysDetector.DOWN
        elif direction == KeysDetector.DOWN:
            return KeysDetector.UP
        elif direction == KeysDetector.LEFT:
            return KeysDetector.RIGHT
        elif direction == KeysDetector.RIGHT:
            return KeysDetector.LEFT

    def direction_to_key(self, direction):
        if direction == KeysDetector.UP:
            return KeysDetector.KEY_UP
        elif direction == KeysDetector.DOWN:
            return KeysDetector.KEY_DOWN
        elif direction == KeysDetector.LEFT:
            return KeysDetector.KEY_LEFT
        elif direction == KeysDetector.RIGHT:
            return KeysDetector.KEY_RIGHT
