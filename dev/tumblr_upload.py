#!/usr/bin/env python
import pytumblr
import time
import yaml
import os
import sys

yaml_path = os.path.expanduser('~') + '/.tumblr'
if not os.path.exists(yaml_path):
    print " Please use interactive_console.py in local_modules/pytumblr to save ~/.tumblr config file with Your OAuth authentication"
    sys.exit(1)

yaml_file = open(yaml_path, "r")
tokens = yaml.safe_load(yaml_file)
yaml_file.close()

BLOGNAME='donothavetimeforthis'


# Authenticate via OAuth
start = time.time()
client = pytumblr.TumblrRestClient(
    tokens['consumer_key'],
    tokens['consumer_secret'],
    tokens['oauth_token'],
    tokens['oauth_token_secret']
)
print "time = %f" % (time.time() - start)

# Make the request
#print client.info()
print "\n\nPOST_CREATE:\n"
start = time.time()
post = client.create_photo(BLOGNAME, state="published", tags=["testing", "ok"], data='py.gif', caption="Sesja 223")
print post
print "time = %f" % (time.time() - start)

start = time.time()
post_2 = client.posts(BLOGNAME, id=post['id'])
print post_2['posts'][0]['short_url']
print "time taken = %f" % (time.time() - start)

start = time.time()
print client.edit_post(BLOGNAME, id=post['id'], data=['py.gif', '../tmp/223/1.jpg', '../tmp/223/2.jpg', '../tmp/223/3.jpg', '../tmp/223/4.jpg'])
print "time = %f" % (time.time() - start)

