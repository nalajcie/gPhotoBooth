import base

def platform_init():
    pass

def platform_deinit():
    pass

class Button(base.Peripherial):
    """
    We're not supporting external button on linux.
    Feel free to implement Your peripherials here.
    """

    def update_state(self):
        pass

class Lights(base.Peripherial):
    """
    We're not supporting external lights on linux.
    Feel free to implement Your peripherials here.
    """
    def __init__(self, external_lights):
        super(Lights, self).__init__()

    def set_brightness(self, b):
        pass


def get_ip():
    """
    One-liner for 2 methods of getting IP: either by gethostname (may return 127.*) or by connecting to remote address
    Taken from: http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/1267524#1267524
    """
    import socket
    try:
        x = [ l for l in (
            [ ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.") ][:1], #try to check locally
            [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]] # try by connecting
            ) if l ] # get first working method
        return x[0][0] #flatten
    except error:
        return "UNKNOWN"
