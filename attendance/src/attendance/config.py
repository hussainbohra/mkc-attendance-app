from configobj import ConfigObj


class Config:
    def __init__(self, config_file):
        self.config_file = config_file

    def get_config(self):
        return ConfigObj(self.config_file)
