import cv2
import mss
import numpy
import signal

from .io_control import IoControl
from .keys_detector import KeysDetector
from .perfect_detector import PerfectDetector


class AuditionCtrl:
    PLAY_AREA = (330, 510, 700, 585)  # left, top, right, bottom
    KEYS_AREA = (330, 540, 700, 580)
    PERFECT_AREA = (515, 520, 685, 525)

    KEYS_THRESHOLD = 254

    def __init__(self):
        self.running = True
        self.io_control = IoControl()
        self.keys_detector = KeysDetector()
        self.perfect_detector = PerfectDetector()
        signal.signal(signal.SIGINT, self.exit_handler)

    def exit_handler(self, sig, frame):
        self.running = False

    def run(self):
        with mss.mss() as sct:
            self.io_control.focus()
            play_area = self.get_play_area_pos()

            while self.running:
                play_area_img = numpy.array(sct.grab(play_area))

                self.process(play_area_img)

                cv2.imshow("Main Win", play_area_img)

            cv2.destroyAllWindows()

    def get_play_area_pos(self) -> dict:
        app_reg = self.io_control.get_app_region()
        region = {
            "top": app_reg[1] + AuditionCtrl.PLAY_AREA[1],
            "left": app_reg[0] + AuditionCtrl.PLAY_AREA[0],
            "width": AuditionCtrl.PLAY_AREA[2] - AuditionCtrl.PLAY_AREA[0],
            "height": AuditionCtrl.PLAY_AREA[3] - AuditionCtrl.PLAY_AREA[1],
        }
        return region

    def process(self, play_area_img):
        gray = cv2.cvtColor(play_area_img, cv2.COLOR_BGRA2GRAY)

        key_area = gray[
            AuditionCtrl.KEYS_AREA[1] : AuditionCtrl.KEYS_AREA[3],
            AuditionCtrl.KEYS_AREA[0] : AuditionCtrl.KEYS_AREA[2],
        ]
        keys = self.keys_detector.detect(key_area)

        perfect_area = gray[
            AuditionCtrl.PERFECT_AREA[1] : AuditionCtrl.PERFECT_AREA[3],
            AuditionCtrl.PERFECT_AREA[0] : AuditionCtrl.PERFECT_AREA[2],
        ]
        perfect_time = self.perfect_detector.detect(perfect_area)

        # control
