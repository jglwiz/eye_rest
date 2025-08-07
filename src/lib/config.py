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
            "allow_password_skip": False,
            "idle_detection_enabled": True,
            "idle_threshold_minutes": 2,
            "temp_pause_enabled": True,
            "temp_pause_duration": 20,
            "temp_pause_hotkey": "ctrl+shift+e"
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
                    self.idle_detection_enabled = config.get("idle_detection_enabled", self.default_config["idle_detection_enabled"])
                    self.idle_threshold_minutes = config.get("idle_threshold_minutes", self.default_config["idle_threshold_minutes"])
                    self.temp_pause_enabled = config.get("temp_pause_enabled", self.default_config["temp_pause_enabled"])
                    self.temp_pause_duration = config.get("temp_pause_duration", self.default_config["temp_pause_duration"])
                    self.temp_pause_hotkey = config.get("temp_pause_hotkey", self.default_config["temp_pause_hotkey"])
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
        self.idle_detection_enabled = self.default_config["idle_detection_enabled"]
        self.idle_threshold_minutes = self.default_config["idle_threshold_minutes"]
        self.temp_pause_enabled = self.default_config["temp_pause_enabled"]
        self.temp_pause_duration = self.default_config["temp_pause_duration"]
        self.temp_pause_hotkey = self.default_config["temp_pause_hotkey"]

    def save(self):
        config = {
            "work_time": self.work_time,
            "rest_time": self.rest_time,
            "hotkey": self.hotkey,
            "play_sound_after_rest": self.play_sound_after_rest,
            "allow_password_skip": self.allow_password_skip,
            "idle_detection_enabled": self.idle_detection_enabled,
            "idle_threshold_minutes": self.idle_threshold_minutes,
            "temp_pause_enabled": self.temp_pause_enabled,
            "temp_pause_duration": self.temp_pause_duration,
            "temp_pause_hotkey": self.temp_pause_hotkey
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f)
