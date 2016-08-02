# encoding: utf-8
""" Controlls the interaction with PiCam (recording + UI """
import os
import io
import subprocess

import logging
logger = logging.getLogger('videobooth.%s' % __name__)

class PiCam(object):
    """ Spawning and Controlling picam by file hooks """
    def __init__(self, config):
        self.conf = config
        self.proc = None

        self.last_text = ""

        # shortcuts
        self.hooks_dir = os.path.join(self.conf['picam']['workdir'], "hooks")
        self.state_dir = os.path.join(self.conf['picam']['workdir'], "state")


    def start(self):
        # setup dirs
        if not os.path.exists(self.conf['picam']['workdir']):
            os.makedirs(self.conf['picam']['workdir'])
        if not os.path.exists(self.conf['picam']['archive_dir']):
            os.makedirs(self.conf['picam']['archive_dir'])

        for dirname in ["rec", "hooks", "state"]:
            realdir = os.path.join(self.conf['picam']['shmdir'], dirname)
            symname = os.path.join(self.conf['picam']['workdir'], dirname)
            if not os.path.exists(realdir):
                os.makedirs(realdir)

            # always regenerate symlinks
            if os.path.lexists(symname):
                os.remove(symname)
            os.symlink(realdir, symname)

        archive_symname = os.path.join(self.conf['picam']['workdir'], "rec/archive")
        if os.path.lexists(archive_symname):
            os.remove(archive_symname)
        os.symlink(self.conf['picam']['archive_dir'], archive_symname)

        # prepare command line
        args = [ self.conf['picam']['binary'] ]
        for (k, v) in self.conf['picam']['params'].iteritems():
            args.append("--" + k)
            if v is not True:
                args.append(str(v))

        # spawn!
        logger.info("spawning PICAM: %s", args)
        self.proc = subprocess.Popen(args, cwd=self.conf['picam']['workdir'])
        logger.info("PICAM HAS BEEN SPAWNED")

    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
            except OSError:
                logger.exception("Failed to stop picam")

    def update(self):
        """ just checking if the underlaying process is alive """
        if self.proc.poll() != None:
            logger.warn("PICAM HAS DIED WITH returncode=%d", self.proc.returncode)
            # TODO: what to do?
            return False

        return True


    def set_text(self, text, **kwargs):
        if self.last_text == text:
            return
        self.last_text = text
        params = {
                "text": text,
                "in_video": 0,
                "duration": 0,
                "pt": 40,
                }
        for (k, v) in kwargs.iteritems():
            params[k] = v
        param_strings = [ u"=".join([unicode(k), unicode(v)]) for (k, v) in params.iteritems() ]
        logger.debug("SUBTITLE: %s", param_strings)

        dest_file = os.path.join(self.hooks_dir, "subtitle")
        with io.open(dest_file, "w", encoding="utf-8") as f:
            f.write(u"\n".join(param_strings))

    def start_recording(self):
        dest_file = os.path.join(self.hooks_dir, "start_record")
        with io.open(dest_file, "w") as f:
            f.write(u"")

    def stop_recording(self):
        dest_file = os.path.join(self.hooks_dir, "stop_record")
        with io.open(dest_file, "w") as f:
            f.write(u"")

    def is_recording(self):
        dest_file = os.path.join(self.state_dir, "record")
        with io.open(dest_file, "r") as f:
            rec_bool = f.read()

        return rec_bool.strip() == "true"


    def last_rec_filename(self):
        dest_file = os.path.join(self.state_dir, "last_rec")
        with io.open(dest_file, "r") as f:
            f_path = f.read()

        return os.path.join(self.conf['picam']['archive_dir'], os.path.split(f_path)[1])
