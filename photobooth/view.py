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

    @classmethod
    def width(self):
        return self.WIDTH + 2 * self.BORDER

    @classmethod
    def height(self):
        return self.HEIGHT + 2 * self.BORDER

    def draw_rect(self):
        """ draws empty rectangle with the number in the middle of it"""
        self.image.fill((0,0,0)) # black
        if self.border:
            pygame.draw.rect(self.image, self.conf.border_color, (0,0, self.size[0] - self.border / 2, self.size[1] - self.border / 2), self.border)
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
        """
        Starts indefinately animating file list ala GIF.
        if fps = 0 -> synchronize with display FPS
        """
        self.animate_file_list = file_list
        self.animate_idx = 0
        if fps == 0: # next pframe every update()
            self.animate_change_every_ms = 0
        else:
            self.animate_change_every_ms = 1000 / fps

    def stop_animate(self):
        self.animate_file_list = None

    def draw(self, canvas):
        if self.dirty:
            self.dirty = 0
            canvas.blit(self.image, self.rect)
            return self.rect

    def update(self, force_redraw = 0):
        if force_redraw:
            self.dirty = 1
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
    BORDER = 2

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
    BORDER = 4

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
        #self.camera.start_preview()
        self.is_started = True

    def stop(self):
        self.is_started = False
        #self.camera.stop_preview()
        self.draw_rect()

    def pause(self):
        self.is_started = False
        #self.camera.stop_preview()
        # do not overwrite with black rectangle

    def update(self, force_redraw):
        if self.is_started:
            self.draw_flip_image(self.camera.capture_preview(), self.conf.flip_preview)
        else:
            super(LivePreview, self).update(force_redraw)


class TextBox(PhotoPreview):
    """
    TODO
    """
    WIDTH = 1
    HEIGHT = 100
    BORDER = 5

    def __init__(self, group, conf, size, center):
        super(TextBox, self).__init__(group, conf, (size[0], self.HEIGHT), center, self.BORDER)
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size/2)

        # surface & positioning
        #self.image = pygame.Surface(size)
        #self.image.set_colorkey((0,0,0)) # black transparent
        #self.rect = self.image.get_rect()
        self.rect.center = center
        self.image.convert()
        self.current_text = ""

    def update(self, force_redraw):
        if force_redraw:
            self.dirty = 1

    def draw_text(self, text):
        if self.current_text == text:
            return

        self.current_text = text
        self.image.fill((0,0,0))
        location = self.image.get_rect()
        line = self.font.render(text, True, self.conf.font_color)
        line_height = self.font.get_linesize()
        line_pos = line.get_rect()
        line_pos.center = (self.rect.width / 2, self.rect.height / 2)

        self.image.blit(line, line_pos)
        self.dirty = 1

    def draw(self, canvas):
        if self.dirty: # blit only when displaying text
            canvas.blit(self.image, self.rect)
            self.dirty = 0
            return self.rect


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
        self.mainview_group.set_timing_treshold(1000. / self.conf.working_fps)
        self.idleview_group.clear(self.canvas, self.back_image)
        self.idleview_group.set_timing_treshold(1000. / self.conf.idle_fps)

        self.init_child_components()
        self.fps = self.conf.idle_fps
        self.idle = True

    def init_child_components(self):
        """ Create child graphics components """
        width = self.conf.screen_width
        height = self.conf.screen_height

        main_total_width = LivePreview.width() + self.conf.idle_space + SmallPhotoPreview.width()
        main_total_height = LivePreview.height() + self.conf.idle_space + TextBox.height()
        left_margin = (self.conf.screen_width - main_total_width) / 2
        top_margin = (self.conf.screen_height - main_total_height) / 2

        self.lv = LivePreview(self.mainview_group, self.conf, (left_margin, top_margin), self.camera)

        #main previews
        self.main_previews = dict()

        main_previews_spacer = (LivePreview.height() - 4 * SmallPhotoPreview.height()) / 3

        left_offset = left_margin + LivePreview.width() + self.conf.idle_space
        top_offset = top_margin
        for num in xrange(1, 5):
            self.main_previews[num] = SmallPhotoPreview(self.mainview_group, self.conf, (left_offset, top_offset), num)
            top_offset += SmallPhotoPreview.height() + main_previews_spacer

        #TEXT BOX
        top_offset = top_margin + LivePreview.height() + self.conf.idle_space + TextBox.height() / 2
        self.textbox = TextBox(self.mainview_group, self.conf, (main_total_width, TextBox.height()), (width / 2, top_offset))

        #idle previews
        self.idle_previews = dict()


        idle_total_width = SmallPhotoPreview.width() * 4 + self.conf.idle_space * 3
        idle_total_height = SmallPhotoPreview.height() * 4 + self.conf.idle_space * 4 + TextBox.height()
        left_margin = (self.conf.screen_width - idle_total_width) / 2

        left_offset = left_margin
        top_offset = (self.conf.screen_height - idle_total_height) / 2
        for num in xrange (1, 17):
            self.idle_previews[num] = SmallPhotoPreview(self.idleview_group, self.conf, (left_offset, top_offset), num)
            left_offset += SmallPhotoPreview.width() + self.conf.idle_space
            if num % 4 == 0:
                left_offset = left_margin
                top_offset += SmallPhotoPreview.height() + self.conf.idle_space

        self.idle_textbox = TextBox(self.idleview_group, self.conf, (idle_total_width, TextBox.height()), (width / 2, top_offset + TextBox.height() / 2))
        self.idle_textbox.draw_text("Push a button!")


    @property
    def idle(self):
        return self.is_idle

    @idle.setter
    def idle(self, val):
        self.is_idle = val
        logger.info("Idle: %s" % val)
        self.canvas.blit(self.back_image, (0,0))
        pygame.display.flip() # ensure we will update full screen, not only dirty rects
        if self.is_idle:
            self.idleview_group.update(1) # force_redraw = 1
            self.fps = self.conf.idle_fps
            for pp in self.main_previews.values():
                pp.reset()
        else:
            self.mainview_group.update(1) # force_redraw = 1
            self.fps = self.conf.working_fps


    def update(self):
        dirty_rects = []
        if self.is_idle:
            self.idleview_group.update(0)
            #dirty_rects = self.idleview_group.draw(self.canvas)
            dirty_rects += [ pp.draw(self.canvas) for pp in self.idle_previews.values() ]
            dirty_rects += [ self.idle_textbox.draw(self.canvas) ]
        else:
            #dirty_rects = self.mainview_group.draw(self.canvas)
            self.mainview_group.update(0)
            dirty_rects += [ self.lv.draw(self.canvas) ]
            dirty_rects += [ pp.draw(self.canvas) for pp in self.main_previews.values() ]
            dirty_rects += [ self.textbox.draw(self.canvas) ]

        #logger.debug("DIRTY RECTS: %s" % dirty_rects)
        pygame.display.update(dirty_rects)


