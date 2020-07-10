import cv2
import mss
import numpy as np
import signal
import threading
import time
import keyboard

from .io_control import IoControl
from .keys_detector import KeysDetector
from .perfect_detector import PerfectDetector
from .sct_img import SctImg
from .app_conf import AppConf
from .utils import *


class AuditionCtrl:
    CONF_FILE = r".\app.conf"
    AUAU_SECTION = "AuAu"

    PID = 0
    PLAY_AREA = (330, 510, 700, 585)  # left, top, right, bottom
    KEYS_AREA = (280, 540, 750, 580)
    PERFECT_AREA = (515, 520, 685, 525)
    PERFECT_HEAD = 0
    PERFECT_MIDDLE = 0
    PERFECT_TAIL = 0

    PERFECT_ADJUSTMENT = 0.0
    PERFECT_ADJUSTMENT_UNIT = 0.01
    RUN_SLEEP = 0.2

    def __init__(self):
        self.app_conf = AppConf(AuditionCtrl.CONF_FILE)

        self.running = True
        self.speed = 1.0
        self.io_control = IoControl()
        self.keys_detector = KeysDetector()
        self.perfect_detector = PerfectDetector()

        self.prepare()

    def exit_handler(self, sig, frame):
        self.running = False

    def prepare(self):
        signal.signal(signal.SIGINT, self.exit_handler)

        self.app_conf.read()

        AuditionCtrl.PID = self.app_conf.get(AuditionCtrl.AUAU_SECTION, "pid")
        AuditionCtrl.PERFECT_ADJUSTMENT_UNIT = self.app_conf.get(
            AuditionCtrl.AUAU_SECTION, "perfect_adjustment_unit"
        )

        self.io_control.connect(pid=AuditionCtrl.PID)
        self.io_control.set_key_typing_sleep(
            self.app_conf.get(AuditionCtrl.AUAU_SECTION, "key_typing_sleep")
        )

        perfect_width = AuditionCtrl.PERFECT_AREA[2] - AuditionCtrl.PERFECT_AREA[0]
        AuditionCtrl.PERFECT_HEAD = perfect_width // 4
        AuditionCtrl.PERFECT_TAIL = perfect_width * 3 // 4
        AuditionCtrl.PERFECT_MIDDLE = perfect_width * 3 // 10

        perfect_area = self.get_area_pos(AuditionCtrl.PERFECT_AREA)
        self.perfect_detector.set_perfect_area(perfect_area)

        keyboard.add_hotkey("home", self.measure_speed)
        keyboard.add_hotkey("page up", self.increase_adjustment)
        keyboard.add_hotkey("page down", self.decrease_adjustment)

    def increase_adjustment(self):
        AuditionCtrl.PERFECT_ADJUSTMENT = round(
            AuditionCtrl.PERFECT_ADJUSTMENT + AuditionCtrl.PERFECT_ADJUSTMENT_UNIT, 2
        )
        print(AuditionCtrl.PERFECT_ADJUSTMENT)

    def decrease_adjustment(self):
        AuditionCtrl.PERFECT_ADJUSTMENT = round(
            AuditionCtrl.PERFECT_ADJUSTMENT - AuditionCtrl.PERFECT_ADJUSTMENT_UNIT, 2
        )
        print(AuditionCtrl.PERFECT_ADJUSTMENT)

    def run(self):
        self.io_control.focus()
        self.measure_speed()

        t1 = threading.Thread(target=self.control_keys)
        t1.start()

        if self.app_conf.get(AuditionCtrl.AUAU_SECTION, "auto_perfect"):
            t2 = threading.Thread(target=self.control_perfect)
            t2.start()

        while self.running:
            time.sleep(AuditionCtrl.RUN_SLEEP * 2)

    def measure_speed(self):
        self.speed = self.perfect_detector.measure_speed()
        AuditionCtrl.PERFECT_ADJUSTMENT = 0.0

    def control_keys(self):
        while self.running:
            self.wait_marker_at_head()

            keys = self.get_keys()
            if not keys:
                continue
            self.io_control.send_keys(keys)

            self.wait_marker_at_tail()
            time.sleep(AuditionCtrl.RUN_SLEEP)

    def get_keys(self):
        keys_area = self.get_area_pos(AuditionCtrl.KEYS_AREA)
        sct = capture(keys_area)
        keys = self.keys_detector.detect(sct.img)
        return keys

    def control_perfect(self):
        while self.running:
            self.wait_marker_at_middle()

            perfect_time = self.perfect_detector.get_wait_perfect(self.speed)
            self.hit_perfect(perfect_time)

            self.wait_marker_at_tail()
            time.sleep(AuditionCtrl.RUN_SLEEP)

    def hit_perfect(self, perfect_time):
        def func():
            sleep_time = perfect_time - time.time() + AuditionCtrl.PERFECT_ADJUSTMENT
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.io_control.send_keys(self.perfect_detector.KEY_SPACE)

        t = threading.Thread(target=func)
        t.start()

    def wait_marker_at_head(self):
        while True:
            sct = self.perfect_detector.get_sct_img_with_marker()
            if sct.marker_pos < AuditionCtrl.PERFECT_HEAD:
                return

    def wait_marker_at_middle(self):
        while True:
            sct = self.perfect_detector.get_sct_img_with_marker()
            if sct.marker_pos > AuditionCtrl.PERFECT_MIDDLE:
                return

    def wait_marker_at_tail(self):
        while True:
            sct = self.perfect_detector.get_sct_img_with_marker()
            if sct.marker_pos > AuditionCtrl.PERFECT_TAIL:
                return

    def get_area_pos(self, area) -> dict:
        app_reg = self.io_control.get_app_region()
        region = {
            "top": app_reg[1] + area[1],
            "left": app_reg[0] + area[0],
            "width": area[2] - area[0],
            "height": area[3] - area[1],
        }
        return region
