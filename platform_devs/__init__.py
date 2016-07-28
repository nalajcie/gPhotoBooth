PI      = "pi"
LINUX   = "linux"
UNKNOWN = "unknown"


def get_platform():
    """ Autodetect platform we're running on. Put Your custom platform detection code here """
    try:
        import RPi.GPIO
        return PI
    except ImportError:
        pass

    if platform.system() == 'Linux':
        return LINUX
    else:
        return UNKNOWN


running_platform = get_platform()
if running_platform == PI:
    from pi import *
elif running_platform == LINUX:
    from linux import *
else:
    raise Exception("Sorry, no implementation fro Your platform")

