# encoding: utf-8
"""
Readout configuration from yaml file.

Firstly the default file is loaded and then the values
are updaded with custom config.
"""
import yaml
import os


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
    # (1) read default config
    cfg = read_yaml(DEFAULT_CONFIG_FILE)

    # (2) read event config
    yaml_path = os.path.join(event_path, CONFIG_FILENAME)
    if not os.path.exists(yaml_path):
        raise Exception("No config file for event_dir provided: at least copy default config to: %s" % yaml_path)

    cfg.update(read_yaml(yaml_path))

    # (3) read translations file
    msg_path = cfg['control']['message_file'] or ""
    msgs = read_yaml(msg_path)
    cfg['m'] = msgs

    return cfg

