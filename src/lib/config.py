import json
import os

class Config:
    def __init__(self):
        self.config_path = "eye_rest_config.json"
        self.default_config = {
            "work_time": 10,
            "rest_time": 1,
            "hotkey": "ctrl+shift+r"
        }
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    self.work_time = config.get("work_time", self.default_config["work_time"])
                    self.rest_time = config.get("rest_time", self.default_config["rest_time"])
                    self.hotkey = config.get("hotkey", self.default_config["hotkey"])
            except:
                self._set_defaults()
        else:
            self._set_defaults()

    def _set_defaults(self):
        self.work_time = self.default_config["work_time"]
        self.rest_time = self.default_config["rest_time"]
        self.hotkey = self.default_config["hotkey"]

    def save(self):
        config = {
            "work_time": self.work_time,
            "rest_time": self.rest_time,
            "hotkey": self.hotkey
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f)
