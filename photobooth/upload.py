import pytumblr
import time
import os
import subprocess

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

GIF_FILENAME = "merge.gif"

def get_gif_filename(file_name):
    return os.path.join(os.path.dirname(file_name), GIF_FILENAME)


def run(config, send_pipe, recv_pipe):
    """ we expect file list to be turned into GIF and uploaded """
    logger.info("uploader process has started")

    # setup tumblr client
    client = pytumblr.TumblrRestClient(
        config.tumblr_consumer_key,
        config.tumblr_consumer_secret,
        config.tumblr_oauth_token,
        config.tumblr_oauth_token_secret
    )

    while True:
        try:
            sess_id, file_list = recv_pipe.recv()
        except EOFError:
            break

        try:
            logger.info("processing sess(%d) files: %s", sess_id, file_list)

            # (1) create GIF
            start = time.time()
            gif_name = get_gif_filename(file_list[0])
            cmd = ["convert", "-delay", "20", "-loop", "0"]
            cmd.extend(file_list)
            cmd.append(gif_name)
            logger.debug("CMD: %s", cmd)
            subprocess.call(cmd)
            logger.debug("creating GIF took %f seconds", (time.time() - start))

            # (2) upload only the GIF
            start = time.time()
            post = client.create_photo(config.tumblr_blogname, state="published", tags=["testing", "ok"], data=gif_name, caption=("Sesja %d" % sess_id))
            logger.debug("create_photo: %s", post)
            logger.debug("create_photo time: %f seconds", (time.time() - start))

            # (3) retrieve and send the short_url ASAP
            start = time.time()
            created_post = client.posts(config.tumblr_blogname, id=post['id'])
            logger.debug("posts: %s", created_post)
            logger.debug("posts time: %f seconds", (time.time() - start))
            logger.debug("short URL: %s", created_post['posts'][0]['short_url'])
            send_pipe.send((sess_id, created_post['posts'][0]['short_url']))

            # (4) reupload GIF + upload remaining files
            start = time.time()
            imgs_to_upload = [gif_name]
            imgs_to_upload.extend(file_list)
            res = client.edit_post(config.tumblr_blogname, id=post['id'], data=imgs_to_upload)
            logger.debug("reupload result: %s", res)
            logger.debug("edit_post time: %f seconds", (time.time() - start))
            logger.info("uploading sess(%d) has finished", sess_id)
        except Exception:
            logger.exception("Uploader worker exception!")

