# encoding: utf-8
"""
Readout configuration from yaml file.

Firstly the default file is loaded and then the values
are updaded with custom config.
"""
import yaml
import os


## TODO: what with these:
#debug_override = {
#    'initial_countdown_secs': 1,
#    'midphoto_countdown_secs': 1,
#    'image_display_secs': 1,
#    'montage_display_secs': 5,
#    'idle_secs': 5,
#    'montage_fps': 4,
#}

DEFAULT_CONFIG_FILE = "events/template/config.yaml"
CONFIG_FILENAME = "config.yaml"

def read_yaml(yaml_path):
    if not os.path.exists(yaml_path):
        raise Exception("Config file not found: %s" % yaml_path)
    with open(yaml_path, "r") as yaml_file:
        tokens = yaml.load(yaml_file)

    return tokens

def read_config(event_path):
    """ try to read config file """
    cfg = read_yaml(DEFAULT_CONFIG_FILE)

    yaml_path = os.path.join(event_path, CONFIG_FILENAME)
    if not os.path.exists(yaml_path):
        raise Exception("No config file for event_dir provided: at least copy default config to: %s" % yaml_path)

    cfg.update(read_yaml(yaml_path))
    return cfg

