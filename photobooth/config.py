

### CONFGIURATION ###
# this is the default configuration, some values can be changed using commandline parameters
default_config = {
    # display-related consts
    'screen_width': 1280,
    'screen_height': 800,
    'fullscreen': 0,
    'idle_fps': 4,
    'working_fps': 30,

    # controller-related vars
    'save_path': '.',
    'flip_preview': True,
    'initial_countdown_secs': 3,
    'midphoto_countdown_secs': 3,
    'image_display_secs': 2,
    'montage_display_secs': 5,
    'idle_secs': 30,
    'montage_fps': 4,

    # whole screen drawing-related consts
    'font_color': (210, 210, 210),
    'font_size': 142,
    'back_color': (230, 180, 40),
    'back_image': 'assets/pixelbackground_02_by_kara1984.jpg',

    'left_margin': 20,
    'left_offset': 48/3,
    'bottom_margin': 20,
    'top_margin': 20,
}

debug_override = {
    'initial_countdown_secs': 1,
    'midphoto_countdown_secs': 1,
    'image_display_secs': 1,
    'montage_display_secs': 5,
    'idle_secs': 30,
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
        return cls(**default_config)

    @classmethod
    def debug(cls):
        conf = cls(**default_config)
        conf.__dict__.update(**debug_override)
        return conf
