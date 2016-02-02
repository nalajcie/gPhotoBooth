#!/usr/bin/env python
from local_modules import piggyphoto
import pygame
from StringIO import StringIO
import os
import time

MAX_FPS=30

C = piggyphoto.Camera()
size = None
main_surface = None
is_paused = False

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
    cfile = C.capture_preview()
    picture = pygame.image.load(StringIO(cfile.get_data())).convert()
    main_surface.blit(picture, (0, 0))
    pygame.display.flip()

cfile = C.capture_preview()
picture = pygame.image.load(StringIO(cfile.get_data()))

size = picture.get_size()
pygame.display.set_mode(size)
main_surface = pygame.display.get_surface()

pygame.display.set_mode(picture.get_size())
main_surface = pygame.display.get_surface()
clock = pygame.time.Clock()

while not quit_pressed():
    clock.tick_busy_loop(MAX_FPS)
    if not is_paused:
        update_preview()

    pygame.display.set_caption("[FPS]: %.2f" % (clock.get_fps()))

C.close()
