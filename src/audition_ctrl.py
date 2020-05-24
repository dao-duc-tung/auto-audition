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
from .app_conf import AppConf
from .utils import *


class AuditionCtrl:
    CONF_FILE = r"D:\zother\auto-audition\app.conf"
    AUAU_SECTION = "AuAu"

    PID = 15928
    PLAY_AREA = (330, 510, 700, 585)  # left, top, right, bottom
    KEYS_AREA = (330, 540, 700, 580)
    PERFECT_AREA = (515, 520, 685, 525)
    PERFECT_HEAD = 0
    PERFECT_TAIL = 0

    PERFECT_ADJUSTMENT = 0.01
    RUN_SLEEP = 0.2

    def __init__(self):
        self.running = True
        self.speed = 1.0
        self.io_control = IoControl()
        self.keys_detector = KeysDetector()
        self.perfect_detector = PerfectDetector()

        self.prepare()

    def prepare(self):
        signal.signal(signal.SIGINT, self.exit_handler)

        self.app_conf = AppConf(AuditionCtrl.CONF_FILE)
        self.app_conf.read()

        self.io_control.connect(pid=AuditionCtrl.PID)

        perfect_width = AuditionCtrl.PERFECT_AREA[2] - AuditionCtrl.PERFECT_AREA[0]
        AuditionCtrl.PERFECT_HEAD = perfect_width // 4
        AuditionCtrl.PERFECT_TAIL = perfect_width * 3 // 4

        perfect_area = self.get_area_pos(AuditionCtrl.PERFECT_AREA)
        self.perfect_detector.set_perfect_area(perfect_area)

    def exit_handler(self, sig, frame):
        self.running = False

    def run(self):
        self.measure_speed()

        self.io_control.focus()
        while self.running:
            self.app_conf.read()
            AuditionCtrl.PERFECT_ADJUSTMENT = self.app_conf.get(
                AuditionCtrl.AUAU_SECTION, "perfect_adjustment"
            )

            if not self.is_marker_at_head():
                time.sleep(AuditionCtrl.RUN_SLEEP)
                continue

            keys = self.get_keys()
            if not keys:
                time.sleep(AuditionCtrl.RUN_SLEEP)
                continue
            self.io_control.send_keys(keys)
            perfect_time = self.get_wait_perfect_time()
            self.hit_perfect(perfect_time)

            while not self.is_marker_at_tail():
                continue

        cv2.destroyAllWindows()

    def measure_speed(self):
        self.io_control.focus()
        self.speed = self.perfect_detector.measure_speed()

    def is_marker_at_head(self):
        sct = self.perfect_detector.get_sct_img_with_marker()
        if sct.marker_pos < AuditionCtrl.PERFECT_HEAD:
            return True
        return False

    def is_marker_at_tail(self):
        sct = self.perfect_detector.get_sct_img_with_marker()
        if sct.marker_pos > AuditionCtrl.PERFECT_TAIL:
            return True
        return False

    def get_keys(self):
        keys_area = self.get_area_pos(AuditionCtrl.KEYS_AREA)
        sct = capture(keys_area)
        keys_img = to_gray(sct.img)
        keys = self.keys_detector.detect(keys_img)
        return keys

    def get_wait_perfect_time(self):
        perfect_time = self.perfect_detector.get_wait_perfect(self.speed)
        return perfect_time

    def hit_perfect(self, perfect_time):
        def func():
            sleep_time = perfect_time - time.time() + AuditionCtrl.PERFECT_ADJUSTMENT
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.io_control.send_keys(self.perfect_detector.KEY_SPACE)

        t = threading.Thread(target=func)
        t.start()

    def get_area_pos(self, area) -> dict:
        app_reg = self.io_control.get_app_region()
        region = {
            "top": app_reg[1] + area[1],
            "left": app_reg[0] + area[0],
            "width": area[2] - area[0],
            "height": area[3] - area[1],
        }
        return region
