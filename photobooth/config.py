
"""
### CONFGIURATION ###
this is the default configuration, some values can be changed using
commandline parameters
 TODO: read out custom configuration from YAML config file
"""

default_config = {
    # display-related consts
    'screen_width': 1280,
    'screen_height': 800,
    'fullscreen': False,
    'idle_fps': 2,
    'working_fps': 30,

    # peripherials-related values
    'thermal_printer': False,
    'dummy_camera': False,
    'lights_default': 512,
    'lights_full': 1024,
    'print_logo': 'assets/nalajcie-logo.png',

    # controller-related vars
    'save_path': '.',
    'flip_preview': True,
    'initial_countdown_secs': 3,
    'midphoto_countdown_secs': 3,
    'image_display_secs': 0,
    'montage_display_secs': 9,
    'idle_secs': 30,
    'montage_fps': 4,
    'idle_previews_cnt': 16,

    # whole screen drawing-related consts
    'font_color': (210, 210, 210),
    'border_color': (0, 0, 0),
    #'border_color': (255, 0, 0),
    'font_size': 72,
    'big_font_size': 144,
    'back_color': (230, 180, 40),
    'back_image': 'assets/pixelbackground_02_by_kara1984.jpg',

    'left_margin': 20,
    'idle_space': 20,
    'left_offset': 42/3,
    'top_offset': 42/3,
    'bottom_margin': 20,
    'top_margin': 20,

    # tumblr uploading
    'upload': False,
    'tumblr_blogname': 'donothavetimeforthis',
    # note: credentials are kept in ~/.tumblr

    # some debug vars
    'fps_update_ms': 2000
}

debug_override = {
    'initial_countdown_secs': 1,
    'midphoto_countdown_secs': 1,
    'image_display_secs': 1,
    'montage_display_secs': 5,
    'idle_secs': 5,
    'montage_fps': 4,
}




class Config(object):
    """Change dictionary to object attributes."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return str(self.__dict__)

    @classmethod
    def default(cls):
        """ returns the default configuration object """
        return cls(**default_config)

    @classmethod
    def debug(cls):
        """ returns the debug configuration object """
        conf = cls(**default_config)
        conf.__dict__.update(**debug_override)
        return conf

    def read_tumblr_config(self):
        """ tries to read tumblr auth config from ~/.tumblr file """
        import yaml
        import os
        yaml_path = os.path.expanduser('~') + '/.tumblr'
        if not os.path.exists(yaml_path):
            raise Exception("Please use interactive_console.py in local_modules/pytumblr to save ~/.tumblr config file with Your OAuth authentication")

        yaml_file = open(yaml_path, "r")
        tokens = yaml.safe_load(yaml_file)
        yaml_file.close()

        for (k, val) in tokens.iteritems():
            self.__dict__['tumblr_' + k] = val
