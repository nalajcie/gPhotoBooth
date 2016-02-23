#!/usr/bin/env python
""" Experimenting with creating GIFs """
import images2gif
import PIL
import sys
import time
import subprocess

def main():
    """ main func """
    img_list = [("../tmp/" + sys.argv[1] +"/" + str(i) + "_medium.jpg") for i in xrange(1, 5)]

    start = time.time()
    opened_imgs = [PIL.Image.open(f) for f in img_list]
    images2gif.writeGif("py.gif", opened_imgs, duration=0.2)
    print "PYTHON GIF time = %f" % (time.time() - start)

    start = time.time()
    cmd = ["convert", "-delay", "20", "-loop", "0"]
    cmd.extend(img_list)
    cmd.append("out.gif")
    print cmd
    subprocess.call(cmd)
    print "SUBSHELL GIF time = %f" % (time.time() - start)

if __name__ == '__main__':
    main()
