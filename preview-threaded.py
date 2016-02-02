#!/usr/bin/env python
from local_modules import piggyphoto
import pygame
from StringIO import StringIO
from Queue import Queue
import threading
import os
import time

### FOR PROFILING
PROFILING=0

class ProfiledThread(threading.Thread):
    # Overrides threading.Thread.run()
    def run(self):
        import cProfile
        profiler = cProfile.Profile()
        try:
            return profiler.runcall(threading.Thread.run, self)
        finally:
            profiler.dump_stats('myprofile-%d.profile' % (self.ident,))

MAX_FPS=30

C = piggyphoto.Camera()
size = None
main_surface = None
is_paused = False

next_preview = Queue(maxsize=0)

preview_running = True

def get_image():
    while preview_running:
        if not is_paused:
            cfile = C.capture_preview()
            picture = StringIO(cfile.get_data())
            #picture = pygame.image.load(StringIO(cfile.get_data())).convert()
            next_preview.put(picture)

def quit_pressed():
    global is_paused, C
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            is_paused = not is_paused
            if is_paused:
                C.close()
                C = piggyphoto.Camera()
    return False

def update_preview():
    file = next_preview.get()
    picture = pygame.image.load(file).convert()
    main_surface.blit(picture, (0, 0))
    pygame.display.flip()
    next_preview.task_done()

cfile = C.capture_preview()
picture = pygame.image.load(StringIO(cfile.get_data()))

size = picture.get_size()
pygame.display.set_mode(size)
main_surface = pygame.display.get_surface()

pygame.display.set_mode(picture.get_size())
main_surface = pygame.display.get_surface()
clock = pygame.time.Clock()

if PROFILING:
    get_image_worker = ProfiledThread(target=get_image)
else:
    get_image_worker = threading.Thread(target=get_image)
get_image_worker.setDaemon(True)
get_image_worker.start()

while not quit_pressed():
    clock.tick_busy_loop(MAX_FPS)
    if not is_paused:
        update_preview()

    pygame.display.set_caption("[FPS]: %.2f" % (clock.get_fps()))

preview_running = False
get_image_worker.join()
C.close()
