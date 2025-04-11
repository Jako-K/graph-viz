import numpy as np
import math

COLORS = {
    'blue': (31, 119, 180),
    'orange': (255, 127, 14),
    'green': (44, 160, 44),
    'red': (214, 39, 40),
    'purple': (148, 103, 189),
    'brown': (140, 86, 75),
    'pink': (227, 119, 194),
    'grey_light': (155, 155, 155),
    'grey': (127, 127, 127),
    'grey_dark': (95, 95, 95),
    'white': (225, 255, 255)
}

DEFAULT_COLORS = {
    "base": COLORS["grey"],
    "select": COLORS["orange"],
    "hover": COLORS["blue"],
    "shadow": COLORS["grey_dark"],
    "preview": COLORS["white"],
    "outline": COLORS["grey_light"],
    "addition": COLORS["green"],
    "text": COLORS["white"]
}


def rotate_point(p_offset, p_rotate, theta_rad):
    x_off = p_offset[0]
    y_off = p_offset[1]

    x = p_rotate[0] - x_off
    y = p_rotate[1] - y_off

    x_ = x*np.cos(theta_rad) - y*np.sin(theta_rad)
    y_ = x*np.sin(theta_rad) + y*np.cos(theta_rad)

    return [x_off+x_, y_off+y_]


def angle_between_points_rad(p1, p2):
    d = (p2.x-p1.x)**2 + (p2.y-p1.y)**2
    r = d**0.5
    diff = p2.x-p1.x
    theta = 0
    if diff != 0:
        theta = np.arccos((p2.x-p1.x)/r)
    return theta

def release_active_obj(active_obj):
    if active_obj is None:
        return
    active_obj.is_selected = False
    active_obj.anchor = active_obj.old_anchor

rad2deg = math.degrees