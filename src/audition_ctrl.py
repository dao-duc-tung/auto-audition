import signal
import threading
import time

import keyboard

from .app_conf import AppConf
from .io_control import IoControl
from .keyboard_ctrl import KeyDef
from .keys_detector import KeysDetector
from .perfect_detector import PerfectDetector
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

        self.keys_detector.set_two_hands_mode(bool(self.app_conf.get(
            AuditionCtrl.AUAU_SECTION, "two_hands_mode"
        )))

        perfect_width = AuditionCtrl.PERFECT_AREA[2] - AuditionCtrl.PERFECT_AREA[0]
        AuditionCtrl.PERFECT_HEAD = perfect_width // 4
        AuditionCtrl.PERFECT_TAIL = perfect_width * 3 // 4
        AuditionCtrl.PERFECT_MIDDLE = perfect_width * 3 // 10

        perfect_area = self.get_area_pos(AuditionCtrl.PERFECT_AREA)
        self.perfect_detector.set_perfect_area(perfect_area)

        keyboard.add_hotkey("f5", self.measure_speed)
        keyboard.add_hotkey("f6", self.increase_speed)
        keyboard.add_hotkey("f7", self.decrease_speed)
        keyboard.add_hotkey("f9", lambda : self.exit_handler(None, None))

        self.control_keys_thread = threading.Thread(target=self.control_keys)
        self.control_perfect_thread = threading.Thread(target=self.control_perfect)
        self.hit_perfect_thread = threading.Thread(target=self.hit_perfect)

    def increase_speed(self):
        self.speed += AuditionCtrl.PERFECT_ADJUSTMENT_UNIT
        print(self.speed)

    def decrease_speed(self):
        self.speed -= AuditionCtrl.PERFECT_ADJUSTMENT_UNIT
        print(self.speed)

    def run(self):
        self.io_control.focus()
        self.speed = self.app_conf.get(AuditionCtrl.AUAU_SECTION, "speed")
        if self.speed == None:
            self.measure_speed()

        print(self.speed)
        self.control_keys_thread.start()

        if self.app_conf.get(AuditionCtrl.AUAU_SECTION, "auto_perfect"):
            self.control_perfect_thread.start()

        while self.running:
            time.sleep(AuditionCtrl.RUN_SLEEP * 2)

    def measure_speed(self):
        self.speed = self.perfect_detector.measure_speed()
        AuditionCtrl.PERFECT_ADJUSTMENT = 0.0

    def control_keys(self):
        while self.running:
            # self.wait_marker_at_head()

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
        # from PIL import Image
        # img = Image.fromarray(sct.img)
        # img.save(f"k8.png")
        # print(keys)
        return keys

    def control_perfect(self):
        while self.running:
            self.wait_marker_at_middle()

            perfect_time = self.perfect_detector.get_wait_perfect(self.speed)
            self.hit_perfect(perfect_time)

            # self.wait_marker_at_tail()
            time.sleep(AuditionCtrl.RUN_SLEEP)

    def hit_perfect(self, perfect_time):
        sleep_time = perfect_time - time.time() + AuditionCtrl.PERFECT_ADJUSTMENT
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.io_control.send_keys(KeyDef.VK_SPACE)

    def wait_marker_at_head(self):
        while True and self.running:
            sct = self.perfect_detector.get_sct_img_with_marker()
            if sct.marker_pos < AuditionCtrl.PERFECT_HEAD:
                return

    def wait_marker_at_middle(self):
        while True and self.running:
            sct = self.perfect_detector.get_sct_img_with_marker()
            if sct.marker_pos > AuditionCtrl.PERFECT_MIDDLE:
                return

    def wait_marker_at_tail(self):
        while True and self.running:
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
