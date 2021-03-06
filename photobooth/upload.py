# encoding: utf-8
import pytumblr
import dropbox
import time
import os
import subprocess

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

GIF_FILENAME = "animation.gif"
STAMP_FILENAME = ".stamp_uploaded"

def get_gif_filename(file_name):
    return os.path.join(os.path.dirname(file_name), GIF_FILENAME)

def get_stamp_filename(file_name):
    return os.path.join(os.path.dirname(file_name), STAMP_FILENAME)

def get_sess_dirname(conf, sess_id):
    return os.path.join(conf['event_dir'], conf['m']['upload_session_dir'] % sess_id)

def setup_dropbox_client(conf):
    """ Setuping dropbox client and basic folder structure """
    if not 'dropbox' in conf['upload'] or not conf['upload']['dropbox']['enabled']:
        return None

    db_client = dropbox.client.DropboxClient(conf['upload']['dropbox']['access_token'])
    try:
        account_info = db_client.account_info()
    except dropbox.rest.ErrorResponse, ex:
        if ex.status == 401:
            logging.error("Expired/invalid dropbox token. Use web browser to generate new one")
        msg = ex.user_error_msg or str(ex)
        logger.error("Dropbox error: %s", msg)
        return None

    logger.debug("Dropbox: %s", account_info)

    # check if upload folder exists and create if necessary
    try:
        db_client.file_create_folder(conf['event_dir'])
    except dropbox.rest.ErrorResponse, ex:
        if ex.status == 403:
            logger.debug("Dropbox folder was already there")
        else:
            msg = ex.user_error_msg or str(ex)
            logger.error("Dropbox error: %s", msg)

    return db_client

def run(conf, pipe):
    """ we expect file list to be turned into GIF and uploaded """
    logger.info("uploader process has started")
    serv_pipe, client_pipe = pipe
    serv_pipe.close()

    # setup tumblr client
    client = pytumblr.TumblrRestClient(
        conf['upload']['tumblr']['consumer_key'],
        conf['upload']['tumblr']['consumer_secret'],
        conf['upload']['tumblr']['oauth_token'],
        conf['upload']['tumblr']['oauth_token_secret'],
    )

    db_client = setup_dropbox_client(conf)

    while True:
        try:
            sess_id, medium_file_list, full_file_list, tags = client_pipe.recv()
        except EOFError:
            break
        except IOError:
            break

        try:
            logger.info("processing sess(%d) files: %s", sess_id, full_file_list)

            # (1) create GIF (or do noting if it exists)
            start = time.time()
            gif_name = get_gif_filename(medium_file_list[0])
            if not os.path.exists(gif_name):
                # GIF dealy is in 'ticks' (100 ticks = 1 s)
                cmd = ["convert", "-delay", str(conf['control']['gif_delay_ms']/10), "-loop", "0"]
                cmd.extend(medium_file_list)
                cmd.append(gif_name)
                logger.debug("CMD: %s", cmd)
                subprocess.call(cmd)
                logger.debug("creating GIF took %f seconds", (time.time() - start))

            # (2) prepare dropbox folder for the session
            if db_client:
                start = time.time()
                sess_dir = get_sess_dirname(conf, sess_id)
                db_client.file_create_folder(sess_dir)
                shared = db_client.share(sess_dir)
                logger.debug("dropbox_share: %s", shared)
                logger.debug("dropbox_share time: %f seconds", (time.time() - start))

            # (3) upload only the GIF
            start = time.time()
            caption = (u"<h1>" + conf['m']['upload_session_title'] + "</h1>") % sess_id
            if db_client:
                caption += u"<a href=\"%s\">%s</a>" % (shared['url'], conf['m']['upload_download_photos'])
            post = client.create_photo(conf['upload']['tumblr']['blogname'], state="published", tags=tags, data=gif_name, caption=caption, format="html")
            logger.debug("create_photo: %s", post)
            logger.debug("create_photo time: %f seconds", (time.time() - start))
            if not post or not 'id' in post:
                logging.error("Thumblr post failure. Aborting this session.")
                continue

            # (4) retrieve and send the short_url ASAP
            start = time.time()
            created_post = client.posts(conf['upload']['tumblr']['blogname'], id=post['id'])
            logger.debug("posts: %s", created_post)
            logger.debug("posts time: %f seconds", (time.time() - start))
            short_url = created_post['posts'][0]['short_url']
            logger.debug("short URL: %s", short_url)
            client_pipe.send((sess_id, short_url))

            # (5) write stamp file to ensure we've sent data to tumblr
            with open(get_stamp_filename(gif_name), 'w') as stamp_file:
                stamp_file.write(short_url)

            # (6) reupload GIF + upload remaining files onto dropbox
            if db_client:
                start = time.time()
                imgs_to_upload = [gif_name]
                imgs_to_upload.extend(full_file_list)
                for img in imgs_to_upload:
                    up_file = open(img, "rb")
                    dest_file = sess_dir + "/" + os.path.basename(img)
                    logging.debug("Dropbox: uploading file to: %s", dest_file)
                    db_client.put_file(dest_file, up_file)
                logger.debug("dropbox_upload time: %f seconds", (time.time() - start))

            # reuploading all images to tumblr - not used!
            #start = time.time()
            #imgs_to_upload = [gif_name]
            #imgs_to_upload.extend(file_list)
            #res = client.edit_post(config.tumblr_blogname, id=post['id'], data=imgs_to_upload)
            #logger.debug("reupload result: %s", res)
            #logger.debug("edit_post time: %f seconds", (time.time() - start))
            logger.info("uploading sess(%d) has finished", sess_id)
        except Exception:
            logger.exception("Uploader worker exception!")

    logger.info("uploader worker exiting!")

