#!/usr/bin/env python
import pygame
import math

MAX_FPS=30
DIR="../assets/shutter/big/"

size = None
main_surface = None
is_paused = False

def quit_pressed():
    global is_paused, C
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYUP and event.key == pygame.K_q:
            return True
        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            is_paused = not is_paused
            if is_paused:
                C.close()
                C = piggyphoto.Camera()
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


class ShutterSprite(pygame.sprite.Sprite):
    # WARN: gave up on this, not working
    # tried to port jquery-shutter.js
    frames = {'num':15, 'height':1000, 'width':1000}
    slices = {'num':8, 'width': 416, 'height':500, 'startDeg':30}

    def __init__(self, size):
        super(ShutterSprite, self).__init__()

        self.size = size
        self.image = pygame.Surface(self.size)
        self.rect = self.image.get_rect()
        self.image.set_colorkey((255,0,0)) # black transparent
        self.image.convert_alpha()

        self.slice_img = pygame.image.load("shutter.png").convert_alpha()

        self.frame_imgs = []
        self.curr_frame = 0
        self.generate_frames()

    def generate_frames(self):
        # This will calculate the rotate difference between the
        # slices of the shutter. (2*Math.PI equals 360 degrees in radians):

        rotateStep = 2 * math.pi / self.slices['num']
        rotateDeg = 30

        # Calculating the offset
        self.slices['angleStep']= ((90 - self.slices['startDeg']) / self.frames['num']) * math.pi / 180

        #creating requesed frames
        for z in xrange(0, self.frames['num']):
            surf = pygame.Surface((self.frames['width'], self.frames['height']))
            surf.fill((255, 0, 0))
            #surf.set_colorkey((255,0,0)) # black transparent
            surf.convert()
            self.frame_imgs.append(surf)

            for i in xrange (0, self.slices['num']):
                # For each frame, generate the different
                # states of the shutter by drawing the shutter
                # slices with a different rotation difference.

                # Rotating the canvas with the step, so we can
                # paint the different slices of the shutter.
                #c.rotate(-rotateStep);

                # Saving the current rotation settings, so we can easily revert
                # back to them after applying an additional rotation to the slice.

                #c.save();

                # Moving the origin point (around which we are rotating
                # the canvas) to the bottom-center of the shutter slice.
                #c.translate(0,frames.height/2);

                # This rotation determines how widely the shutter is opened.
                #c.rotate((frames.num-1-z)*slices.angleStep);

                # An additional offset, applied to the last five frames,
                # so we get a smoother animation:

                offset = 0
                #if((frames.num-1-z) <5){
                #        offset = (frames.num-1-z)*5;
                #}

                # Drawing the shutter image
                surf.blit(self.slice_img, (self.slices['width'] / 2, self.frames['height'] / 2 + offset))
                #c.drawImage(img,-slices.width/2,-(frames.height/2 + offset));

                # Reverting back to the saved settings above.
                # c.restore();


    def update(self):
        width = (self.size[0] - self.frames['width']) / 2
        height = (self.size[1] - self.frames['height']) / 2
        self.image.blit(self.frame_imgs[self.curr_frame], (width, height))
        self.curr_frame = (self.curr_frame + 1) % self.frames['num']

    def draw(self, canvas):
        canvas.blit(self.image, (0,0))


picture = pygame.image.load("../capture_preview.jpg")

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

