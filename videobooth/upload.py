# encoding: utf-8
import json
import requests
import time
import os
import subprocess

from threading import Thread
from Queue import Queue, Empty

import logging
logger = logging.getLogger('videobooth.%s' % __name__)

URL_SUFFIX = ".url"
DONE_SUFFIX = ".done"

class UploadProxy(object):
    def __init__(self, config):
        self.conf = config
        self.is_running = False

        # file encoding + upload file thread
        self.process_req = Queue(maxsize=0)
        self.thread_process = Thread(target=self.process_worker)
        self.thread_process.setDaemon(True)

        if not self.conf['upload']['enabled']:
            return

        if self.conf['upload']['debug']:
            self.enable_debug()

        # create post thread
        self.create_req = Queue(maxsize=8)
        self.create_resp = Queue(maxsize=8)
        self.thread_create = Thread(target=self.create_worker)
        self.thread_create.setDaemon(True)


    def enable_debug(self):
        import httplib as http_client
        http_client.HTTPConnection.debuglevel = 1
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True


    def upload_pending_movies(self):
        """ searches for unuploaded movies and tries to upload them """
        files = os.listdir(self.conf['picam']['archive_dir'])
        for f in files:
            if os.path.splitext(f)[1] == ".mp4" and (f + DONE_SUFFIX) not in files:
                filepath = os.path.join(self.conf['picam']['archive_dir'], f)
                upload_url = None
                if os.path.exists(filepath + URL_SUFFIX):
                    with open(filepath + URL_SUFFIX) as f_url:
                        upload_url = f_url.read()

                logging.info("scheduling for upload: '%s' -> '%s'", filepath, upload_url)
                self.async_process(upload_url, filepath)


    def start(self):
        self.is_running = True
        self.thread_process.start()
        if self.conf['upload']['enabled']:
            self.thread_create.start()

            if self.conf['upload']['retrying']:
                self.upload_pending_movies()

    def async_create_post(self, mov_suffix):
        if not self.conf['upload']['enabled']:
            return

        self.create_req.put(mov_suffix)

    def async_create_post_result(self):
        if not self.conf['upload']['enabled']:
            return ("", "")

        try:
            return self.create_resp.get_nowait()
        except Empty:
            return None

    def async_process(self, upload_url, filename):
        self.process_req.put((upload_url, filename))


    def sync_create_post(self, mov_suffix):
        name = "%s%s" % (self.conf['upload']['atende']['title_prefix'], mov_suffix)
        logger.debug("name: %s", name)

        try:
            start = time.time()
            resp = requests.post(
                '%s/api/v1/videos/create/' % self.conf['upload']['atende']['api_endpoint'],
                {
                    'category': self.conf['upload']['atende']['category_id'],
                    'name': name,
                    'description': self.conf['upload']['atende']['description'],
                },
                headers={
                    'X-Token': self.conf['upload']['atende']['api_token']
                },
                timeout=self.conf['upload']['atende']['timeout_secs'])

            logger.debug("create time: %f seconds", (time.time() - start))
            resp_json = json.loads(resp.content)
            return (
                resp_json['uploadUri'],
                self.conf['upload']['atende']['api_endpoint'] + resp_json['frontendUri'])
        except requests.exceptions.RequestException:
            logger.exception("create: exception")
            return ("","")


    def create_worker(self):
        while self.is_running:
            mov_suffix = self.create_req.get()
            logger.debug("create_worker: START")

            ret = self.sync_create_post(mov_suffix)
            self.create_resp.put(ret)

            self.create_req.task_done()
            logger.debug("create_worker: END")


    def process_worker(self):
        while self.is_running:
            (upload_url, filepath) = self.process_req.get()
            logger.debug("process_worker: START")
            start = time.time()

            # (1) convert mpeg-ts to MP4:
            (tmp_filepath, ext) = os.path.splitext(filepath)
            if ext == ".ts":
                (_, filename) = os.path.split(tmp_filepath)
                new_filepath = os.path.join(self.conf['picam']['archive_dir'], filename + ".mp4")
                cmd = ['ffmpeg', '-i', filepath, '-c:v', 'copy', '-c:a', 'copy', '-bsf:a', 'aac_adtstoasc', new_filepath]
                logger.debug("CONVERT CMD: %s", cmd)
                subprocess.call(cmd)
                logger.debug("creating MP4 took %f seconds", (time.time() - start))
                os.unlink(filepath) # NOTE: removing original .ts file
                filepath = new_filepath

            if not self.conf['upload']['enabled']:
                logging.warn("not uploading file: uploading is disabled")
                self.process_req.task_done()
                continue

            # (2) only when reuploading at startup - create upload URL synchronously
            if upload_url is None:
                # generate mov_prefix similar to strftime
                fn = os.path.splitext(os.path.split(filepath)[1])[0]
                (fn_date, fn_time) = fn.split('_')
                mov_prefix = fn_date + " " + fn_time.replace("-", ":")

                logger.debug("upload uri is None, getting new one(mov_prefix='%s')", mov_prefix)
                (upload_url, _) = self.sync_create_post(mov_prefix)

            if len(upload_url) == 0:
                logging.warn("not uploading file: empty post url")
                continue

            # (3) save upload URL in case it wasn't done already
            if not os.path.exists(filepath + URL_SUFFIX):
                with open(filepath + URL_SUFFIX, "w") as f:
                    f.write(upload_url)

            # (4) upload
            try:
                logger.debug("uploading file '%s' to '%s'", filepath, upload_url)
                start = time.time()
                with open(filepath, 'rb') as file_obj:
                    resp = requests.put(
                        '%s%s' % (self.conf['upload']['atende']['api_endpoint'], upload_url),
                        data=file_obj,
                        headers={
                            'X-Token': self.conf['upload']['atende']['api_token'],
                            'Content-Type': 'video/mp4'
                        },
                        timeout=self.conf['upload']['atende']['timeout_secs'])

                if resp.status_code == 204:
                    logger.info("upload sucessful")
                else:
                    import pprint
                    logger.warn("Failed upload response: %s", pprint.pformat(resp.__dict__))
                    resp.raise_for_status()

                # (5) save upload URL in case it wasn't done already:
                with open(filepath + DONE_SUFFIX, "w") as f:
                    f.write("%f" % (time.time()-start))

                logger.debug("uploading took %f seconds", (time.time() - start))

            except requests.exceptions.RequestException:
                logger.exception("upload: exception")

            self.process_req.task_done()
            logger.debug("upload_worker: END")

