import cv2
import imutils
import numpy as np

from .keyboard_ctrl import KeyDef
from .utils import *


class KeysDetector:
    KEYS_THRESHOLD = 254
    K4_8_THRESHOLD = 0.63
    LEFT_HAND_RED_CHANNEL_THRESHOLD = 110965

    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UP_LEFT = "UP_LEFT"
    DOWN_LEFT = "DOWN_LEFT"
    UP_RIGHT = "UP_RIGHT"
    DOWN_RIGHT = "DOWN_RIGHT"

    LEFT_HAND_UP = "LEFT_HAND_UP"
    LEFT_HAND_DOWN = "LEFT_HAND_DOWN"
    LEFT_HAND_LEFT = "LEFT_HAND_LEFT"
    LEFT_HAND_RIGHT = "LEFT_HAND_RIGHT"

    LOWER_BLUE = np.array([110, 100, 100])
    UPPER_BLUE = np.array([130, 255, 255])
    LOWER_RED = np.array([-10, 100, 100])
    UPPER_RED = np.array([10, 255, 255])

    def __init__(self):
        self.is_two_hands_mode = False
        self.is_eight_keys_mode = False

    def set_two_hands_mode(self, val):
        self.is_two_hands_mode = val

    def set_eight_keys_mode(self, val):
        self.is_eight_keys_mode = val

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
                keys.append(key)

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

    def get_key_roi(self, img, boxes):
        res = img[
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
        sorted_idx = arr.argsort()[::-1]
        max_idx1 = sorted_idx[0]
        max_idx2 = sorted_idx[1]
        max1 = arr[max_idx1]
        max2 = arr[max_idx2]
        if max2 / max1 < KeysDetector.K4_8_THRESHOLD:
            if max_idx1 == 0: direction = KeysDetector.LEFT
            elif max_idx1 == 1: direction = KeysDetector.UP
            elif max_idx1 == 2: direction = KeysDetector.RIGHT
            elif max_idx1 == 3: direction = KeysDetector.DOWN
        else:
            if max_idx1 == 0 and max_idx2 == 1: direction = KeysDetector.UP_LEFT
            elif max_idx2 == 0 and max_idx1 == 1: direction = KeysDetector.UP_LEFT

            elif max_idx1 == 0 and max_idx2 == 3: direction = KeysDetector.DOWN_LEFT
            elif max_idx2 == 0 and max_idx1 == 3: direction = KeysDetector.DOWN_LEFT

            elif max_idx1 == 2 and max_idx2 == 1: direction = KeysDetector.UP_RIGHT
            elif max_idx2 == 2 and max_idx1 == 1: direction = KeysDetector.UP_RIGHT

            elif max_idx1 == 2 and max_idx2 == 3: direction = KeysDetector.DOWN_RIGHT
            elif max_idx2 == 2 and max_idx1 == 3: direction = KeysDetector.DOWN_RIGHT

            # else: direction = KeysDetector.UP

        if not self.is_two_hands_mode:
            if self.is_reversed(color_key_roi):
                direction = self.reverse_direction(direction)
        else:
            if self.is_left_hand(color_key_roi):
                direction = self.right_to_left_hand(direction)

        return direction

    def is_reversed(self, bgr_key_roi):
        hsv = cv2.cvtColor(bgr_key_roi, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, KeysDetector.LOWER_BLUE, KeysDetector.UPPER_BLUE)
        cnt_blue = cv2.countNonZero(mask)

        mask = cv2.inRange(hsv, KeysDetector.LOWER_RED, KeysDetector.UPPER_RED)
        cnt_red = cv2.countNonZero(mask)

        if cnt_red > cnt_blue:
            return True
        return False

    def is_left_hand(self, bgr_key_roi):
        b, g, r = cv2.split(bgr_key_roi)
        r_sum = np.sum(r)
        if r_sum > KeysDetector.LEFT_HAND_RED_CHANNEL_THRESHOLD:
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
        elif direction == KeysDetector.UP_LEFT:
            return KeysDetector.DOWN_RIGHT
        elif direction == KeysDetector.UP_RIGHT:
            return KeysDetector.DOWN_LEFT
        elif direction == KeysDetector.DOWN_LEFT:
            return KeysDetector.UP_RIGHT
        elif direction == KeysDetector.DOWN_RIGHT:
            return KeysDetector.UP_LEFT

    def direction_to_key(self, direction):
        if direction == KeysDetector.UP:
            return KeyDef.VK_UP
        elif direction == KeysDetector.DOWN:
            return KeyDef.VK_DOWN
        elif direction == KeysDetector.LEFT:
            return KeyDef.VK_LEFT
        elif direction == KeysDetector.RIGHT:
            return KeyDef.VK_RIGHT
        elif direction == KeysDetector.UP_LEFT:
            return KeyDef.VK_NUMPAD7
        elif direction == KeysDetector.DOWN_LEFT:
            return KeyDef.VK_NUMPAD1
        elif direction == KeysDetector.UP_RIGHT:
            return KeyDef.VK_NUMPAD9
        elif direction == KeysDetector.DOWN_RIGHT:
            return KeyDef.VK_NUMPAD3
        elif direction == KeysDetector.LEFT_HAND_UP:
            return KeyDef.W_KEY
        elif direction == KeysDetector.LEFT_HAND_DOWN:
            return KeyDef.S_KEY
        elif direction == KeysDetector.LEFT_HAND_LEFT:
            return KeyDef.A_KEY
        elif direction == KeysDetector.LEFT_HAND_RIGHT:
            return KeyDef.D_KEY

    def right_to_left_hand(self, direction):
        if direction == KeysDetector.UP:
            return KeysDetector.LEFT_HAND_UP
        elif direction == KeysDetector.DOWN:
            return KeysDetector.LEFT_HAND_DOWN
        elif direction == KeysDetector.LEFT:
            return KeysDetector.LEFT_HAND_LEFT
        elif direction == KeysDetector.RIGHT:
            return KeysDetector.LEFT_HAND_RIGHT
