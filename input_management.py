import pygame

class Keyboard:
    def __init__(self):
        self.pressed = False
        self.released = False
        self.alt = False
        self.ctrl = False
        self.shift = False
        self.event = None

    def is_pressed(self, key:str, alt=None, ctr=None, shift=None):
        assert len(key) == 1
        if self.event:
            return self.event.key == eval(f"pygame.K_{key}")
        return False

    def end_of_tick_update(self):
        self.pressed, self.released, self.alt, self.ctrl, self.shift = [False] * 5
        self.event = None

    def update(self, event):
        self.event = event
        if event.type == pygame.KEYDOWN:
            self.pressed = True
        if event.type == pygame.KEYUP:
            self.released = True
        if event.mod & pygame.KMOD_SHIFT:
            self.shift = True
        if event.mod & pygame.KMOD_CTRL:
            self.ctrl = True
        if event.mod & pygame.KMOD_ALT:
            self.alt = True

class Mouse:
    def __init__(self):
        self.x = None
        self.y = None
        self._last_update_time = pygame.time.get_ticks()
        self._double_click_max_interval_seconds = 0.4
        self._last_time_left_pressed = -999

        self.left_double_clicked = False
        self.left_pressed = False
        self.left_held = False
        self.left_seconds_pressed = 0
        self.middle_pressed = False
        self.middle_held = False
        self.middle_seconds_pressed = 0
        self.right_pressed = False
        self.right_held = False
        self.right_seconds_pressed = 0

        self.end_of_tick_update()


    def end_of_tick_update(self):
        self.x, self.y = pygame.mouse.get_pos()
        left_pressed, middle_pressed, right_pressed = pygame.mouse.get_pressed()
        current_time_seconds = pygame.time.get_ticks() / 1000
        update_time_delta = (current_time_seconds - self._last_update_time)

        # Reset ticks
        if not self.left_pressed:
            self.left_seconds_pressed = 0
        if not self.middle_pressed:
            self.middle_seconds_pressed = 0
        if not self.right_pressed:
            self.right_seconds_pressed = 0

        # Check if held
        self.left_held = self.left_seconds_pressed > 0
        self.middle_held = self.middle_seconds_pressed > 0
        self.right_held = self.right_seconds_pressed > 0

        # Detect double left click
        self.left_double_clicked = False
        if (not self.left_pressed) and left_pressed:
            if (current_time_seconds - self._last_time_left_pressed) < self._double_click_max_interval_seconds:
                self.left_double_clicked = True
        if left_pressed:
            self._last_time_left_pressed = current_time_seconds

        # Assign seconds pressed
        if left_pressed:
            self.left_seconds_pressed += update_time_delta
        if middle_pressed:
            self.middle_seconds_pressed += update_time_delta
        if right_pressed:
            self.right_seconds_pressed += update_time_delta

        # Update state
        self.left_pressed = left_pressed
        self.middle_pressed = middle_pressed
        self.right_pressed = right_pressed
        self._last_update_time = current_time_seconds