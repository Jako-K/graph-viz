from __future__ import annotations

import pygame
import sys
from world_object import Circle, ObjectSignal, BaseInteractiveObject, MouseAnchor, SimpleObjectConnection, GenericBond
from input_management import Mouse, Keyboard
from helpers import release_active_obj
import cv2
import numpy as np


# Initialize Pygame
pygame.init()
window_size = (1080, 720)
screen = pygame.display.set_mode(window_size)
screen_depth = pygame.Surface(window_size)
pygame.display.set_caption("Elements")
clock = pygame.time.Clock()

# Objects
mouse = Mouse()
keyboard = Keyboard()
objects = [
    Circle(screen, 200, 400, radius=50, depth=1),
    Circle(screen, 700, 600, radius=50, depth=2),
    # Rectangle(screen, 800, 200, width=100, height=100, depth=3, is_selectable=False),
]

active_obj:BaseInteractiveObject|None = None
delayed_active: BaseInteractiveObject|None = None
DELAY_SELECTABLE = pygame.USEREVENT + 1


############################################################
# Game loop
############################################################


running = True
while running:

    #---------------------------------
    # Events
    #---------------------------------

    for event in pygame.event.get():
        if (event.type == pygame.QUIT) or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
            pygame.quit()
            sys.exit()
        if (event.type == pygame.KEYDOWN) or (event.type == pygame.KEYUP):
            keyboard.update(event)
        if event.type == DELAY_SELECTABLE:
            delayed_active.is_active = True
            pygame.time.set_timer(DELAY_SELECTABLE, 0)
            for obj in delayed_active.get_all_objects():
                obj.is_active = True
            delayed_active = None

    #---------------------------------
    # Object placement
    #---------------------------------

    # User keyboard input
    release_active_obj_for_placement = active_obj and (not active_obj.is_under_placement)
    no_active_obj = active_obj is None
    if keyboard.is_pressed("1") and (release_active_obj_for_placement or no_active_obj):
        release_active_obj(active_obj)
        active_obj = Circle(screen, 0, 0, radius=50, depth=50, anchor=mouse)
        active_obj.is_under_placement = True
        active_obj.is_previewing = True
        for obj in active_obj.get_all_objects():
            obj.is_active = False
        objects.append(active_obj)

    # Placement
    if active_obj and active_obj.is_under_placement and mouse.left_pressed:
        active_obj.is_under_placement = False
        active_obj.is_previewing = False
        active_obj.is_selected = False
        active_obj.anchor = None
        delayed_active = active_obj
        active_obj = None
        pygame.time.set_timer(DELAY_SELECTABLE, 200)

    # Object deletion
    if keyboard.is_pressed("x") and active_obj and active_obj.is_deletable:
        active_obj.delete_all_bonds()
        objects = [obj for obj in objects if (obj != active_obj)]
        active_obj = None

    #---------------------------------
    # Depth
    #---------------------------------


    objects_flatten = set()
    for parent_obj in objects:
        for obj in parent_obj.get_all_objects(including_self=True):
            objects_flatten.add(obj)

    if len(objects) >= 255:
        raise RuntimeError("Depth map only use black and white for now. Change all 3 color channels to support more objects.")

    depth_sorted_objects = sorted(objects_flatten, key=lambda o: o.depth)
    depth_colors = np.linspace(0, 255, len(depth_sorted_objects)+1).astype(int)[1:]

    for depth_color, obj in zip(depth_colors, depth_sorted_objects):
        obj.depth_color = (depth_color, depth_color, depth_color)
        obj.draw_depth(screen_depth)

    depth_map = pygame.surfarray.array3d(screen_depth)

    #---------------------------------
    # Object loop
    #---------------------------------

    for i, obj in enumerate(depth_sorted_objects):
        if not obj.is_active:
            continue

        signal:ObjectSignal = obj.respond(mouse, keyboard, depth_map)

        # Selection
        if (active_obj is None) and signal.selected:
            obj.is_selected = signal.selected
            active_obj = obj

        # Hover
        if (active_obj is not None) and (obj != active_obj) and mouse.left_pressed:
            obj.is_hovered = False

        # Release object upon right click
        if active_obj and mouse.right_pressed:
            active_obj = release_active_obj(active_obj)

        # Drag object
        activate_drag = (obj.is_hovered and obj.is_selected and mouse.left_pressed and obj.is_movable) or obj.is_previewing
        if isinstance(obj.anchor, MouseAnchor) and (not mouse.left_held):
            obj.anchor = obj.old_anchor
        if (not isinstance(obj.anchor, MouseAnchor)) and activate_drag:
            obj.old_anchor = obj.anchor
            obj.anchor = MouseAnchor(mouse, offset_x=obj.x - mouse.x, offset_y=obj.y - mouse.y)

        # Interact with another object
        if (not activate_drag) and (active_obj is not None) and (active_obj != obj) and signal.hovered and mouse.left_pressed and (not mouse.left_held):
            new_interaction_obj = active_obj.interact(obj)
            if new_interaction_obj is None:
                continue
            elif isinstance(new_interaction_obj, SimpleObjectConnection):
                active_obj.add_bond("i_am_in_connection_with", new_interaction_obj, add_to_other_as_well=True)
                obj.add_bond("i_am_in_connection_with", new_interaction_obj, add_to_other_as_well=True)
            else:
                print(new_interaction_obj)
                raise NotImplementedError

        # Draw
        obj.draw()

    #---------------------------------
    # Wrap up frame
    #---------------------------------

    # Input
    mouse.end_of_tick_update()
    keyboard.end_of_tick_update()

    # Depth map
    screen_depth.fill((0,0,0))
    cv2.imwrite(r"C:\Users\Jakob\Desktop\image.png", depth_map.transpose((1,0,2)))

    # Screen
    clock.tick(60)
    pygame.display.flip()
    screen.fill((50, 50, 50))


pygame.quit()
sys.exit()
