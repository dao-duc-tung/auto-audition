from configparser import ConfigParser
import ast


class AppConf:
    def __init__(self, conf_file: str):
        super().__init__()
        self._conf_file = conf_file
        self._conf = {}
        self._parser = ConfigParser()

    def read(self):
        self._parser.read(self._conf_file)

        for section in self._parser.sections():
            if not section in self._conf:
                self._conf[section] = {}

            for (item, val) in self._parser.items(section):
                self._conf[section][item] = self.__literal_eval(val)

    def get(self, section: str, item: str):
        if section in self._conf:
            if item in self._conf[section]:
                return self._conf[section][item]

    def set(self, section: str, item: str, val):
        self._parser.set(section, item, val)
        with open(self._conf_file, "w") as f:
            self._parser.write(f)

        self._conf[section][item] = self.__literal_eval(val)

    def __literal_eval(self, val):
        try:
            return ast.literal_eval(val)
        except:
            return val
