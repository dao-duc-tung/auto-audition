import cv2
import mss
import numpy
import signal

from .io_control import IoControl


class AuditionCtrl:
    def __init__(self):
        self.running = True
        self.io_control = IoControl()
        signal.signal(signal.SIGINT, self.exit_handler)

    def exit_handler(self, sig, frame):
        self.running = False

    def run(self):
        with mss.mss() as sct:
            self.io_control.focus()
            monitor = self.io_control.get_area_pos()

            while self.running:
                img = numpy.array(sct.grab(monitor))
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

                cv2.imshow("Main Win", img)

            cv2.destroyAllWindows()
