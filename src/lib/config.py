import json
import os

class Config:
    def __init__(self):
        self.config_path = "eye_rest_config.json"
        self.default_config = {
            "work_time": 10,
            "rest_time": 1,
            "hotkey": "ctrl+shift+r",
            "play_sound_after_rest": True,
            "allow_password_skip": False
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
                    self.play_sound_after_rest = config.get("play_sound_after_rest", self.default_config["play_sound_after_rest"])
                    self.allow_password_skip = config.get("allow_password_skip", self.default_config["allow_password_skip"])
            except:
                self._set_defaults()
        else:
            self._set_defaults()

    def _set_defaults(self):
        self.work_time = self.default_config["work_time"]
        self.rest_time = self.default_config["rest_time"]
        self.hotkey = self.default_config["hotkey"]
        self.play_sound_after_rest = self.default_config["play_sound_after_rest"]
        self.allow_password_skip = self.default_config["allow_password_skip"]

    def save(self):
        config = {
            "work_time": self.work_time,
            "rest_time": self.rest_time,
            "hotkey": self.hotkey,
            "play_sound_after_rest": self.play_sound_after_rest,
            "allow_password_skip": self.allow_password_skip
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f)
