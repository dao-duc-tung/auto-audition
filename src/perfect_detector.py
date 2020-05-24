from typing import List
import cv2
import statistics

from .sct_img import SctImg
from .utils import *


class PerfectDetector:
    PERFECT_POS = 119  # pixel
    MARKER_IMG = cv2.imread(
        r"D:\zother\auto-audition\data\marker.png", cv2.IMREAD_GRAYSCALE
    )
    MARKER_CENTER_OFFSET = 4
    KEY_SPACE = "{SPACE}"

    def __init__(self):
        pass

    def measure_speed(self, area, it=8):
        """
        Speed: pixel/s
        """
        speeds = []
        while len(speeds) < it:
            sct1 = capture(area)
            gray1 = to_gray(sct1.img)
            marker_pos_1 = self.get_marker_pos(gray1, PerfectDetector.MARKER_IMG)

            sct2 = capture(area)
            gray2 = to_gray(sct2.img)
            marker_pos_2 = self.get_marker_pos(gray2, PerfectDetector.MARKER_IMG)

            if marker_pos_1 >= marker_pos_2:
                continue
            speed = (marker_pos_2 - marker_pos_1) / (sct2.tm - sct1.tm)
            speeds.append(speed)

        avg = statistics.mean(speeds)
        return avg

    def get_marker_pos(self, perfect_area, marker):
        result = cv2.matchTemplate(perfect_area, marker_img, cv2.TM_CCOEFF)
        (minVal, maxVal, minLoc, (x, y)) = cv2.minMaxLoc(result)
        return x + PerfectDetector.MARKER_CENTER_OFFSET

    def get_wait_perfect(self, area, speed):
        sct1 = capture(area)
        gray1 = to_gray(sct1.img)
        marker_pos_1 = self.get_marker_pos(gray1, PerfectDetector.MARKER_IMG)
        t = (PerfectDetector.PERFECT_POS - marker_pos_1) / speed
        return t
