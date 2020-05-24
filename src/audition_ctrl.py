import cv2
import mss
import numpy as np
import signal
import threading
import time

from .io_control import IoControl
from .keys_detector import KeysDetector
from .perfect_detector import PerfectDetector
from .sct_img import SctImg


class AuditionCtrl:
    PLAY_AREA = (330, 510, 700, 585)  # left, top, right, bottom
    KEYS_AREA = (330, 540, 700, 580)
    PERFECT_AREA = (515, 520, 685, 525)

    PERFECT_DELAY = 0.1

    def __init__(self):
        self.running = True
        self.speed = 1.0
        self.io_control = IoControl()
        self.keys_detector = KeysDetector()
        self.perfect_detector = PerfectDetector()
        signal.signal(signal.SIGINT, self.exit_handler)

    def exit_handler(self, sig, frame):
        self.running = False

    def measure_speed(self):
        self.io_control.focus()
        perfect_area = self.get_area_pos(AuditionCtrl.PERFECT_AREA)
        self.speed = self.perfect_detector.measure_speed(perfect_area)

    def run(self):
        self.measure_speed()

        with mss.mss() as sct:
            self.io_control.focus()

            while self.running:
                keys_area = self.get_area_pos(AuditionCtrl.KEYS_AREA)
                keys_img = numpy.array(sct.grab(keys_area))
                keys = self.keys_detector.detect(keys_img)
                self.io_control.send_keys(keys)

                wait_time = self.get_wait_perfect_time()
                self.hit_perfect(wait_time)

                cv2.imshow("Main Win", play_area_img)

        cv2.destroyAllWindows()

    def hit_perfect(self, sleep_time):
        def func():
            time.sleep(sleep_time)
            self.io_control.send_keys(self.perfect_detector.KEY_SPACE)

        t = threading.Thread(target=func)
        t.start()

    def get_wait_perfect_time(self):
        perfect_area = self.get_area_pos(AuditionCtrl.PERFECT_AREA)
        wait_time = self.perfect_detector.get_wait_perfect(perfect_area, self.speed)
        wait_time -= AuditionCtrl.PERFECT_DELAY
        return wait_time

    def get_area_pos(self, area) -> dict:
        app_reg = self.io_control.get_app_region()
        region = {
            "top": app_reg[1] + area[1],
            "left": app_reg[0] + area[0],
            "width": area[2] - area[0],
            "height": area[3] - area[1],
        }
        return region
