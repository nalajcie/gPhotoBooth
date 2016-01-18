import pygame

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class PhotoPreview(pygame.sprite.DirtySprite):
    """
    Generic photo preview, ancestor of all preview classes
    """
    def __init__(self, group, conf, size, position, border_width):
        super(PhotoPreview, self).__init__(group)
        self.conf = conf
        self._layer = 4
        self.border = border_width;
        self.size = (size[0] + 2 * border_width, size[1] + 2 * border_width)

        # surface & positioning
        self.image = pygame.Surface(self.size)
        self.rect = self.image.get_rect()
        self.rect.topleft = position
        self.image.convert()

        #animation
        self.animate_idx = 0
        self.animate_file_list = None
        self.animate_change_every_ms = 0
        self.animate_next_change = 0

    def draw_rect(self):
        """ draws empty rectangle with the number in the middle of it"""
        self.image.fill((0,0,0)) # black
        pygame.draw.rect(self.image, (0,255,0), (0,0, self.size[0], self.size[1]), self.border)
        #logger.debug("%s:  draw_rect()" % self)
        self.dirty = 1

    def draw_number(self, number):
        """ draws a number in the middle of the surface """
        font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size)
        fw, fh = font.size(str(number))
        surface = font.render(str(number), True, self.conf.font_color)
        self.image.blit(surface, ((self.rect.width - fw) // 2, (self.rect.height - fh) // 2))
        #logger.debug("%s: draw_number()" % self)
        self.dirty = 1

    def draw_image(self, image):
        """ blits image onto surface """
        self.image.blit(image, (self.border, self.border))
        #logger.debug("%s: draw_image()" % self)
        self.dirty = 1

    def start_animate(self, file_list, fps):
        """ Starts indefinately animating file list ala GIF """
        self.animate_file_list = file_list
        self.animate_idx = 0
        self.animate_change_every_ms = 1000 / fps

    def stop_animate(self):
        self.animate_file_list = None

    def update(self):
        if self.animate_file_list:
            if self.animate_next_change < pygame.time.get_ticks():
                self.draw_image(self.animate_file_list[self.animate_idx])
                self.animate_idx = (self.animate_idx + 1) % len(self.animate_file_list)
                self.animate_next_change = pygame.time.get_ticks() + self.animate_change_every_ms
                self.dirty = 1


class SmallPhotoPreview(PhotoPreview):
    """
    Small photo preview, displays empty frame at first, and a small picture afterwards
    """
    WIDTH  = 200
    HEIGHT = 133
    BORDER = 1

    def __init__(self, group, conf, position, number):
        size = (SmallPhotoPreview.WIDTH, SmallPhotoPreview.HEIGHT)
        super(SmallPhotoPreview, self).__init__(group, conf, size, position, SmallPhotoPreview.BORDER)
        self.number = number
        self.reset()

    def __str__(self):
        return "SmallPhotoPreview(num=%d)" % self.number

    def reset(self):
        self.draw_rect()
        self.draw_number(self.number)


class LivePreview(PhotoPreview):
    """
    LiveView display from the camera
    """
    WIDTH  = 848
    HEIGHT = 560
    BORDER = 2

    def __init__(self, group, conf, position, camera):
        size = (LivePreview.WIDTH, LivePreview.HEIGHT)
        super(LivePreview, self).__init__(group, conf, size, position, LivePreview.BORDER)
        self.camera = camera

        self.stop()

    def draw_flip_image(self, image, flip_image):
        """ starts displaying image instead of empty rect """
        #scalled = pygame.transform.scale(image, (LiveView.WIDTH, LiveView.HEIGHT))
        if flip_image:
            image = pygame.transform.flip(image, True, False)
        super(LivePreview, self).draw_image(image)

    def start(self):
        self.stop_animate()
        self.camera.start_preview()
        self.is_started = True

    def stop(self):
        self.is_started = False
        self.camera.stop_preview()
        self.draw_rect()

    def pause(self):
        self.is_started = False
        self.camera.stop_preview()
        # do not overwrite with black rectangle

    def update(self):
        if self.is_started:
            self.draw_flip_image(self.camera.capture_preview(), self.conf.flip_preview)
        else:
            super(LivePreview, self).update()


class TextBox(pygame.sprite.DirtySprite):
    def __init__(self, group, conf, size, center):
        super(TextBox, self).__init__(group)
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

    def draw_text(self, text_lines):
        if self.current_text == text_lines:
            return

        self.current_text = text_lines
        self.image.fill((0,0,0))
        location = self.image.get_rect()
        rendered_lines = [self.font.render(text, True, self.conf.font_color) for text in text_lines]
        line_height = self.font.get_linesize()
        middle_line = len(text_lines) / 2.0 - 0.5
        self.dirty = 1

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
        - idle screen - showing animated previews of previous shoots
        - main view with LivePreview and 4 small previews
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
        else:
            self.back_image = pygame.Surface((self.conf.screen_width, self.conf.screen_height))
            self.back_image.fill(self.conf.back_color)
        self.back_image.convert()

        # create drawing components
        self.mainview_group = pygame.sprite.LayeredDirty()
        self.idleview_group = pygame.sprite.LayeredDirty()

        self.mainview_group.clear(self.canvas, self.back_image)
        self.idleview_group.clear(self.canvas, self.back_image)

        self.init_child_components()
        self.fps = self.conf.idle_fps
        self.idle = True

    def init_child_components(self):
        """ Create child graphics components """
        width = self.conf.screen_width
        height = self.conf.screen_height
        self.lv = LivePreview(self.mainview_group, self.conf, (self.conf.left_margin, self.conf.top_margin), self.camera)

        #main previews
        self.main_previews = dict()

        left_offset = self.conf.left_margin - SmallPhotoPreview.BORDER
        top_offset = self.conf.top_margin - SmallPhotoPreview.BORDER + LivePreview.HEIGHT + self.conf.bottom_margin
        for num in xrange(1, 5):
            self.main_previews[num] = SmallPhotoPreview(self.mainview_group, self.conf, (left_offset, top_offset), num)
            left_offset += 2 * SmallPhotoPreview.BORDER + SmallPhotoPreview.WIDTH + self.conf.left_offset

        #idle previews
        self.idle_previews = dict()

        left_offset = self.conf.left_margin - SmallPhotoPreview.BORDER
        top_offset = self.conf.top_margin - SmallPhotoPreview.BORDER
        for num in xrange (1, 17):
            self.idle_previews[num] = SmallPhotoPreview(self.idleview_group, self.conf, (left_offset, top_offset), num)
            left_offset += 2 * SmallPhotoPreview.BORDER + SmallPhotoPreview.WIDTH + self.conf.left_offset
            if num % 4 == 0:
                left_offset = self.conf.left_margin - SmallPhotoPreview.BORDER
                top_offset += 2 * SmallPhotoPreview.BORDER + SmallPhotoPreview.HEIGHT + self.conf.top_offset

        self.textbox = TextBox(self.mainview_group, self.conf, self.lv.rect.size, self.lv.rect.center)

    @property
    def idle(self):
        return self.is_idle

    @idle.setter
    def idle(self, val):
        self.is_idle = val
        logger.info("Idle: %s" % val)
        self.canvas.blit(self.back_image, (0,0))
        pygame.display.flip()
        if self.is_idle:
            self.fps = self.conf.idle_fps
            self.lv.stop() # just to be sure
            for pp in self.main_previews.values():
                pp.reset()
        else:
            self.fps = self.conf.working_fps


    def update(self):
        if self.is_idle:
            self.idleview_group.update()
            dirty_rects = self.idleview_group.draw(self.canvas)
        else:
            self.mainview_group.update()
            dirty_rects = self.mainview_group.draw(self.canvas)

        #logger.debug("DIRTY RECTS: %s" % dirty_rects)
        pygame.display.update(dirty_rects)


