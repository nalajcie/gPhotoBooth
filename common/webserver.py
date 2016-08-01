#!/usr/bin/env python
# encoding: utf-8
import multiprocessing
import os
import json
import operator



from twisted.internet import reactor
from twisted.web import static, server, resource


import logging
logger = logging.getLogger('common.%s' % __name__)


class PlaylistResource(resource.Resource):
    isLeaf = True

    def __init__(self, _dir, count, poster):
        self.dir = _dir
        self.count = count
        self.poster = poster

        self.cache = {}
        self.cached_response = None

        self.update_cache()

    def read_new_files(self):
        has_changed = False
        for root, _, files in os.walk(self.dir):
            for file in files:
                if file not in self.cache.keys() and file.endswith(".mp4"):
                    self.cache[file] = os.path.getmtime(os.path.join(root, file))
                    has_changed = True

        return has_changed

    def update_cache(self):
        if self.read_new_files():
            sorted_by_time = sorted(self.cache.items(), key=operator.itemgetter(1), reverse=True)
            self.cached_response = []
            for file, _ in sorted_by_time[:self.count]:
                self.cached_response.append({
                    'sources': [{ 'src': '/mov/' + file, 'type':'video/mp4' }],
                    'poster': self.poster,
                })

    def render_GET(self, request):
        self.update_cache()

        request.responseHeaders.addRawHeader(b"content-type", b"application/json")
        return json.dumps(self.cached_response, ensure_ascii=False, encoding='utf-8').encode('utf-8')


def serve(conf):
    """ main server function - never returns """

    port = conf['webserver']['port']

    root = static.File("web")
    root.putChild("mov", static.File(conf['picam']['archive_dir']))

    playlistRes = PlaylistResource(conf['picam']['archive_dir'],
            conf['webserver']['last_videos_count'],
            conf['webserver']['poster_img'])
    root.putChild("play.json", playlistRes)


    reactor.listenTCP(port, server.Site(root))
    reactor.run()

def try_start_background(conf):
    """ start webserver in separate process """
    if conf['webserver']['enabled']:
        logger.info("starting webserver")
        srv_process = multiprocessing.Process(target=serve, args=(conf,))
        # start and forget
        srv_process.daemon = True
        srv_process.start()



def main():
    """ for testing: read config from file and start webserver """
    import config
    import sys
    if len(sys.argv) < 2:
        print("USAGE:\n\t%s <event_dir>" % sys.argv[0])
        sys.exit(1)

    conf = config.read_config(sys.argv[1], default_config=config.DEFAULT_CONFIG_FILE_VIDEO)

    serve(conf)

if __name__ == "__main__":
    main()
