import pygame

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class LiveView(pygame.sprite.Sprite):
    """
    LiveView display from the camera
    """
    WIDTH  = 848
    HEIGHT = 560
    BORDER = 2

    def __init__(self, group, conf, camera):
        pygame.sprite.Sprite.__init__(self, group)
        self.conf = conf
        self._layer = 5
        self.camera = camera

        # surface & positioning
        self.image = pygame.Surface((LiveView.WIDTH + LiveView.BORDER * 2, LiveView.HEIGHT + LiveView.BORDER * 2)) # previews width/height
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.conf.left_margin - LiveView.BORDER, self.conf.top_margin - LiveView.BORDER)
        self.image.convert()
        self.stop()


    def draw_image(self, image, flip_image):
        """ starts displaying image instead of empty rect """
        scalled = pygame.transform.scale(image, (LiveView.WIDTH, LiveView.HEIGHT))
        if flip_image:
            scalled = pygame.transform.flip(scalled, True, False)
        self.image.blit(scalled, (LiveView.BORDER, LiveView.BORDER))

    def start(self):
        self.is_started = True

    def stop(self):
        self.is_started = False

        # draw empty rect
        pygame.draw.rect(self.image, (255,0,0), (0, 0, LiveView.WIDTH + LiveView.BORDER + 1, LiveView.HEIGHT + LiveView.BORDER + 1),LiveView.BORDER)

    def pause(self):
        self.is_started = False
        # do not overwrite with black rectangle

    def update(self):
        #TODO: capture preview in other thread
        if (self.is_started):
            self.draw_image(self.camera.capture_preview(), self.conf.flip_preview)



class PhotoPreview(pygame.sprite.Sprite):
    """
    Small static photo preview, displays empty frame at first, and a small picture afterwards
    """
    WIDTH  = 200
    HEIGHT = 133
    BORDER = 1

    def __init__(self, group, number, conf):
        pygame.sprite.Sprite.__init__(self, group)
        self.conf = conf
        self._layer = 4
        self.number = number
        # surface & positioning
        self.image = pygame.Surface((PhotoPreview.WIDTH + PhotoPreview.BORDER * 2, PhotoPreview.HEIGHT + PhotoPreview.BORDER * 2)) # previews width/height
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.conf.left_margin - PhotoPreview.BORDER + self.number * (PhotoPreview.WIDTH + self.conf.left_offset),
                self.conf.top_margin - PhotoPreview.BORDER + LiveView.HEIGHT + self.conf.bottom_margin)
        self.image.convert()
        self.draw_empty_rect()

    def draw_empty_rect(self):
        """ draws empty rectangle with the number in the middle of it"""
        pygame.draw.rect(self.image, (0,255,0), (0,0,PhotoPreview.WIDTH + PhotoPreview.BORDER + 1,PhotoPreview.HEIGHT + PhotoPreview.BORDER + 1), PhotoPreview.BORDER)
        font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size)
        fw, fh = font.size(str(self.number + 1))
        surface = font.render(str(self.number + 1), True, self.conf.font_color)
        self.image.blit(surface, ((self.rect.width - fw) // 2, (self.rect.height - fh) // 2))

    def draw_image(self, image):
        """ starts displaying image instead of empty rect """
        scalled = pygame.transform.scale(image, (PhotoPreview.WIDTH, PhotoPreview.HEIGHT))
        self.image.blit((scalled), (PhotoPreview.BORDER, PhotoPreview.BORDER))

class TextBox(pygame.sprite.Sprite):
    def __init__(self, group, conf, size, center):
        pygame.sprite.Sprite.__init__(self, group)
        self.conf = conf
        self._layer = 99 # on top of everything
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size/2)

        # surface & positioning
        self.image = pygame.Surface(size)
        self.image.set_colorkey((0,0,0)) # black transparent
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.image.convert_alpha()
        self.current_text = [""]

    def update(self):
        pass

    #def draw_text(self, text):
    #    fw, fh = self.font.size(text)
    #    surface = self.font.render(text, True, self.conf.font_color)
    #    self.image.blit(surface, ((self.rect.width - fw) // 2, (self.rect.height - fh) // 2))

    def draw_text(self, text_lines):
        if self.current_text == text_lines:
            return

        self.current_text = text_lines
        self.image.fill((0,0,0))
        location = self.image.get_rect()
        rendered_lines = [self.font.render(text, True, self.conf.font_color) for text in text_lines]
        line_height = self.font.get_linesize()
        middle_line = len(text_lines) / 2.0 - 0.5

        for i, line in enumerate(rendered_lines):
            line_pos = line.get_rect()
            lines_to_shift = i - middle_line
            line_pos.centerx = location.centerx
            line_pos.centery = location.centery + lines_to_shift * line_height
            self.image.blit(line, line_pos)

    def render_text_bottom(self, text, size=142):
        #FIXME
        location = self.canvas.get_rect()
        line = self.font.render(text, True, self.conf.font_color)
        line_height = font.get_linesize()

        line_pos = line.get_rect()
        line_pos.centerx = location.centerx
        line_pos.centery = location.height - 2 * line_height
        self.canvas.blit(line, line_pos)


class PygView(object):
    """
    Main view which handles all of the rendering.

    We have 2 main different screens:
        - idle screen - showing previews of previous shoots
        - main view with LiveView and 4 previews
    """

    def __init__(self, controller, conf, camera):
        self.conf = conf
        self.camera = camera
        self.controller = controller

        flags = pygame.DOUBLEBUF | [0, pygame.FULLSCREEN][self.conf.fullscreen]
        self.canvas = pygame.display.set_mode((self.conf.screen_width, self.conf.screen_height), flags)
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size)
        if self.conf.back_image:
            image = pygame.image.load(self.conf.back_image)
            self.back_image = pygame.transform.scale(image, (self.conf.screen_width, self.conf.screen_height))
            self.back_image.convert()

        # create drawing components
        self.mainview_group = pygame.sprite.LayeredUpdates()
        self.idleview_group = pygame.sprite.LayeredUpdates()
        self.is_idle = True

        self.init_child_components()

    def init_child_components(self):
        """ Create child graphics components """
        self.previews = dict()
        for num in xrange(4):
            self.previews[num] = PhotoPreview(self.mainview_group, num, self.conf)
        self.lv = LiveView(self.mainview_group, self.conf, self.camera)
        self.textbox = TextBox(self.mainview_group, self.conf, self.lv.rect.size, self.lv.rect.center)

    @property
    def idle(self):
        return self.is_idle

    @idle.setter
    def set_idle(self, val):
        self.is_idle = val


    def update(self):
        if self.is_idle:
            self.idleview_group.update()
            self.idleview_group.draw(self.canvas)
        else:
            self.mainview_group.update()
            self.mainview_group.draw(self.canvas)

        self.flip()


    def flip(self):
        pygame.display.update()
        if self.back_image:
            self.canvas.blit(self.back_image, (0,0))
        else:
            self.canvas.fill(self.conf.back_color)


