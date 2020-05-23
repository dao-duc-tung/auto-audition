from pywinauto.application import Application, WindowSpecification
import pywinauto.mouse as mouse
import pywinauto.keyboard as keyboard


class IoControl:

    PLAY_AREA_START_POS = (330, 510)  # start left, start top
    PLAY_AREA_SIZE = (375, 75)  # width, height

    def __init__(self):
        self.app: Application = None
        self.dlg: WindowSpecification = None

    def connect(self, path: str):
        self.app = Application().connect(path=path)
        self.dlg = self.app["Audition"]

    def focus(self):
        self.dlg.set_focus()

    def get_area_pos(self) -> dict:
        rect = self.dlg.rectangle()
        region = {
            "top": rect.top + 510,
            "left": rect.left + 330,
            "width": 375,
            "height": 75,
        }
        return region
