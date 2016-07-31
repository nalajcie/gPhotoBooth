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

class UploadProxy(object):
    def __init__(self, config):
        self.conf = config

        if not self.conf['upload']['enabled']:
            return

        self.is_running = False

        # create post thread
        self.create_req = Queue(maxsize=8)
        self.create_resp = Queue(maxsize=8)
        self.thread_create = Thread(target=self.create_worker)
        self.thread_create.setDaemon(True)

        # upload file thread
        self.process_req = Queue(maxsize=0)
        self.thread_process = Thread(target=self.process_worker)
        self.thread_process.setDaemon(True)

    def start(self):
        if not self.conf['upload']['enabled']:
            return

        self.is_running = True
        self.thread_create.start()
        self.thread_process.start()

    def async_create_post(self):
        if not self.conf['upload']['enabled']:
            return

        self.create_req.put("TODO")

    def async_create_post_result(self):
        if not self.conf['upload']['enabled']:
            return ""

        try:
            return self.create_resp.get_nowait()
        except Empty:
            return None

    def async_process(self, post_url, filename):
        self.process_req.put((post_url, filename))

    def create_worker(self):
        while self.is_running:
            req = self.create_req.get()
            logger.debug("create_worker: START")

            try:
                start = time.time()
                resp = requests.post('%s/api/v1/videos/create/' % self.conf['upload']['atende']['api_endpoint'], {
                    'category': self.conf['upload']['atende']['category_id'],
                    'name': "Wideobudka: film testowy",  #FIXME
                    'description': self.conf['upload']['atende']['description'],
                }, headers={
                    'Authorization': 'Token %s' % self.conf['upload']['atende']['api_token']
                },
                timeout=self.conf['upload']['atende']['timeout_secs'])

                logger.debug("create time: %f seconds", (time.time() - start))
                import pprint
                pprint.pprint(resp.__dict__)
                self.create_resp.put(json.loads(resp.content)['uploadUri'])
            except requests.exceptions.RequestException:
                logger.exception("create: exception")
                self.create_resp.put("")

            self.create_req.task_done()
            logger.debug("create_worker: END")


    def process_worker(self):
        while self.is_running:
            (post_url, filepath) = self.process_req.get()
            logger.debug("process_worker: START")
            start = time.time()

            # (1) convert mpeg-ts to MP4:
            (filename, ext) = os.path.splitext(filepath)
            if ext == ".ts":
                new_filepath = filename + ".mp4"
                cmd = ['ffmpeg', '-i', filepath, '-c:v', 'copy', '-c:a', 'copy', '-bsf:a', 'aac_adtstoasc', new_filepath]
                logger.debug("CONVERT CMD: %s", cmd)
                subprocess.call(cmd)
                logger.debug("creating MP4 took %f seconds", (time.time() - start))
                filepath = new_filepath
                #TODO: remove .ts


            if not self.conf['upload']['enabled']:
                logging.warn("not upolading file: %s -> empty post url", post_url)
                self.process_req.task_done()
                continue

            if post_url is None or len(post_url) == 0:
                logging.warn("not upolading file: %s -> empty post url", post_url)
                # TODO: retry creating post url?
                continue


            # (2) upload
            # TODO

            self.process_req.task_done()

