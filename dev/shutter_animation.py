#!/usr/bin/env python
import pygame
import math

MAX_FPS=30
DIR="../assets/shutter/big/"

size = None
main_surface = None
is_paused = False

def quit_pressed():
    global is_paused
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYUP and event.key == pygame.K_q:
            return True
        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            is_paused = not is_paused
    return False

class ShutterStaticSprite(pygame.sprite.Sprite):
    FRAMES=16
    def __init__(self, size):
        super(ShutterStaticSprite, self).__init__()

        self.size = size
        self.image = pygame.Surface(self.size)
        self.rect = self.image.get_rect()
        self.image.set_colorkey((0,0,0)) # black transparent
        self.image.convert_alpha()

        self.frame_imgs = []
        self.curr_frame = 0
        self.read_frames()

    def read_frames(self):
        for i in xrange (0, self.FRAMES):
            img = pygame.image.load(DIR + "shutter%02d.png" % i).convert_alpha()
            img = pygame.transform.scale(img, self.size)
            self.frame_imgs.append(img)


    def update(self):
        self.curr_frame = (self.curr_frame + 1) % self.FRAMES

    def draw(self, canvas):
        canvas.blit(self.frame_imgs[self.curr_frame], (0,0))
        #canvas.blit(self.image, (0,0))



picture = pygame.image.load("dummy-preview.jpg")

size = picture.get_size()
pygame.display.set_mode(size)
main_surface = pygame.display.get_surface()
clock = pygame.time.Clock()

shutter = ShutterStaticSprite(size)

while not quit_pressed():
    clock.tick_busy_loop(MAX_FPS)
    if not is_paused:
        #
        pass

    pygame.display.set_caption("[FPS]: %.2f" % (clock.get_fps()))
    shutter.update()

    main_surface.blit(picture, (0, 0))
    shutter.draw(main_surface)
    pygame.display.flip()

