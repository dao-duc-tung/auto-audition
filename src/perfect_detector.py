from typing import List
import cv2
import statistics

from .sct_img import SctImg
from .utils import *


class PerfectSct(SctImg):
    def __init__(self, img, tm):
        super().__init__(img, tm)
        self.marker_pos = 0

    @classmethod
    def clone(cls, sct: SctImg, marker_pos=0):
        sct = cls(sct.img, sct.tm)
        sct.marker_pos = marker_pos
        return sct


class PerfectDetector:
    PERFECT_POS = 119  # pixel
    MARKER_IMG = cv2.imread(r".\data\marker.png", cv2.IMREAD_GRAYSCALE)
    MARKER_CENTER_OFFSET = 4
    KEY_SPACE = ["{VK_CONTROL down}", "{VK_CONTROL up}"]

    def __init__(self):
        self.perfect_area = {}

    def set_perfect_area(self, perfect_area):
        self.perfect_area = perfect_area

    def measure_speed(self, it=8):
        """
        Speed: pixel/s
        """
        speeds = []
        while len(speeds) < it:
            sct1 = self.get_sct_img_with_marker()
            sct2 = self.get_sct_img_with_marker()

            if sct1.marker_pos >= sct2.marker_pos:
                continue
            speed = (sct2.marker_pos - sct1.marker_pos) / (sct2.tm - sct1.tm)
            speeds.append(speed)

        avg = statistics.mean(speeds)
        print(f"Speed: {avg} pixel/s")
        return avg

    def get_sct_img_with_marker(self) -> PerfectSct:
        sct = capture(self.perfect_area)
        gray = to_gray(sct.img)
        marker_pos = self.get_marker_pos(gray, PerfectDetector.MARKER_IMG)

        sct = PerfectSct.clone(sct, marker_pos)
        sct.marker_pos = marker_pos
        return sct

    def get_marker_pos(self, perfect_area_img, marker_img):
        result = cv2.matchTemplate(perfect_area_img, marker_img, cv2.TM_CCOEFF)
        (minVal, maxVal, minLoc, (x, y)) = cv2.minMaxLoc(result)
        return x + PerfectDetector.MARKER_CENTER_OFFSET

    def get_wait_perfect(self, speed):
        """
        Return next time to hit perfect
        """
        sct = self.get_sct_img_with_marker()
        t = (PerfectDetector.PERFECT_POS - sct.marker_pos) / speed
        return t + sct.tm
