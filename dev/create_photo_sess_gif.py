#!/usr/bin/env python
import images2gif
import PIL
import sys


l = [ PIL.Image.open("../tmp/" + sys.argv[1] +"/" + str(i) + "_prev.jpg") for i in xrange(1, 5) ]

images2gif.writeGif("py.gif", l, duration=0.5)

