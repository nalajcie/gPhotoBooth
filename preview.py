#!/usr/bin/env python
from local_modules import piggyphoto
import pygame
from StringIO import StringIO
import os
import time

C = piggyphoto.Camera()
size = None
main_surface = None

def quit_pressed():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
    return False

def update_preview():
    cfile = C.capture_preview()
    picture = pygame.image.load(StringIO(cfile.get_data()))
    cfile.clean()
    main_surface.blit(picture, (0, 0))
    pygame.display.flip()

C.leave_locked()
cfile = C.capture_preview()
picture = pygame.image.load(StringIO(cfile.get_data()))
cfile.clean()

size = picture.get_size()
pygame.display.set_mode(size)
main_surface = pygame.display.get_surface()

pygame.display.set_mode(picture.get_size())
main_surface = pygame.display.get_surface()

while not quit_pressed():
    update_preview()

C.close()
