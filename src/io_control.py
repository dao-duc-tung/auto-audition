from pywinauto.application import Application, WindowSpecification
import pywinauto.mouse as mouse
import pywinauto.keyboard as keyboard
import time

from .app_conf import AppConf


class IoControl:
    KEY_TYPING_SLEEP = 0.0005

    def __init__(self):
        self.key_typing_sleep = IoControl.KEY_TYPING_SLEEP
        self.app: Application = None
        self.dlg: WindowSpecification = None

    def set_key_typing_sleep(self, key_typing_sleep):
        self.key_typing_sleep = key_typing_sleep

    def connect(self, pid):
        self.app = Application().connect(process=pid)
        self.dlg = self.app["Audition"]

    def focus(self):
        self.dlg.set_focus()

    def get_app_region(self) -> tuple:
        rect = self.dlg.rectangle()
        return (rect.left, rect.top, rect.right, rect.bottom)

    def send_keys(self, keys: list):
        for key in keys:
            # print(key)
            keyboard.send_keys(key)
            time.sleep(self.key_typing_sleep)
