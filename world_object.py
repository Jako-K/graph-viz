from __future__ import annotations

import warnings

import numpy as np
import pygame
from helpers import DEFAULT_COLORS
from input_management import Mouse, Keyboard
from typing import List

###################################################################
# Helper classes - Large
###################################################################


class BaseInteractiveObject:
    unique_ids = []
    unique_object_ids = list([*'abcdefghijklmnopqrstuvwxyz'.upper(), *[str(i) for i in range(100)]])

    def __init__(self, object_type, screen,
                 x:int|None, y:int|None, offset_x=0, offset_y=0, anchor=None, depth=0,
                 is_selected = False, is_hovered = False, is_active = False, is_selectable=True,
                 is_movable=True, is_previewing=False, is_under_placement=False, is_deletable=True):

        # General
        self.object_type = object_type
        self.screen = screen
        self.colors = DEFAULT_COLORS
        self.depth_color = (255,255,255)
        self.unique_id = self.unique_object_ids.pop(0)
        assert self.unique_id not in self.unique_ids
        self.unique_ids.append(self.unique_id)

        # Placement
        self._x = x # center
        self._y = y # center
        self.anchor = anchor
        self.old_anchor = anchor
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.depth = depth

        # `is` states
        self.is_selected = is_selected
        self.is_hovered = is_hovered
        self.is_active = is_active
        self.is_selectable = is_selectable
        self.is_movable = is_movable
        self.is_previewing = is_previewing
        self.is_under_placement = is_under_placement
        self.is_deletable = is_deletable

        # Bonds
        self.bonds:List[GenericBond] = []

    @property
    def x(self):
        if self._x is None:
            return None
            #raise RuntimeError("`x` has been set to None. This mean you cannot access its position this way")
        x = self._x + self.offset_x
        if self.anchor is not None:
            x = self.anchor.x + self.offset_x
        self._x = x # I don't wanna deal with discrepancies between the object's coordinates before and after an anchor get assigned/removed
        return x

    @property
    def y(self):
        if self._y is None:
            return None
            #raise RuntimeError("`y` has been set to None. This mean you cannot access its position this way")
        y = self._y + self.offset_y
        if self.anchor is not None:
            y = self.anchor.y + self.offset_y
        self._y = y # I don't wanna deal with discrepancies between the object's coordinates before and after an anchor get assigned/removed
        return y

    @x.setter
    def x(self, value):
        assert self.anchor is None, "You cannot change the position of an anchor. Either remove the anchor or change the <self>.offset_x instead"
        self._x = value

    @y.setter
    def y(self, value):
        assert self.anchor is None, "You cannot change the position of an anchor. Either remove the anchor or change the <self>.offset_y instead"
        self._y = value

    def __repr__(self):
        to_write = f"type: {self.object_type}, x: {self.x}, y: {self.y}, depth: {self.depth}, selected: {int(self.is_selected)}, "\
                   f"hovered: {int(self.is_hovered)}, previewing: {int(self.is_previewing)}, active: {int(self.is_active)}, " \
                   f"depth: {self.depth}, depth_color: {self.depth_color}"
        return to_write

    def get_connection_anchor(self, interact:BaseInteractiveObject) -> SimpleAnchor|BaseInteractiveObject:
        return self

    def respond(self, mouse:Mouse, keyboard:Keyboard, depth_map:np.ndarray):
        raise NotImplemented

    def interact(self, interact:BaseInteractiveObject=None):
        raise NotImplemented

    def draw_depth(self, screen_depth:pygame.Surface):
        raise NotImplemented

    def draw(self):
        raise NotImplemented

    def add_bond(self, bond:str, other:BaseInteractiveObject, add_to_other_as_well:bool=False) -> None:
        # Add bond to current object
        new_bond = GenericBond(self, bond, other)
        # if any([b == new_bond for b in self.bonds]):
        #     warnings.warn(f"The bond `{new_bond.obj1.object_type} {new_bond.bond} {new_bond.obj2.object_type}` already exists in `self`")
        #     return
        self.bonds.append(new_bond)

        # Add object to other object
        if add_to_other_as_well:
            other.add_bond(bond=new_bond.reversed, other=self, add_to_other_as_well=False)

    def remove_bond(self, bond):
        assert bond in self.bonds
        self.bonds = [b for b in self.bonds if (b != bond)]

    def delete_all_bonds(self):
        for bond in self.bonds:
            bond.obj2.remove_bond(bond)
        self.bonds = []

    def get_all_objects(self, including_self:bool=False) -> List[BaseInteractiveObject]:
        if including_self:
            return [self] + [bond.obj2 for bond in self.bonds]
        return [bond.obj2 for bond in self.bonds]

    def get_parent_objects(self) -> List[BaseInteractiveObject]:
        return [bond.obj2 for bond in self.bonds if (bond.bond_type == "<--")]

    def get_children_objects(self) -> List[BaseInteractiveObject]:
        return [bond.obj2 for bond in self.bonds if (bond.bond_type == "-->")]

###################################################################
# Helper classes - Small
###################################################################

# Trigger types
HOVERED = 0
SELECTED = 1
LEFT_CLICKED = 2
RIGHT_CLICKED = 3

class ObjectSignal:
    def __init__(self, who:BaseInteractiveObject, triggers:List[int]):
        self.who = who
        self.hovered = HOVERED in triggers
        self.selected = SELECTED in triggers
        self.left_clicked = LEFT_CLICKED in triggers
        self.right_clicked = RIGHT_CLICKED in triggers

    def __str__(self):
        triggers = f"hovered: {self.hovered} , selected: {self.selected} , left_clicked: {self.left_clicked} , right_clicked: {self.right_clicked}"
        return f"Who:      {self.who}\n" \
               f"Trigger:  {triggers}"

class SimpleAnchor:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class MouseAnchor:
    def __init__(self, mouse, offset_x:int=0, offset_y:int=0):
        self._x = None
        self._y = None
        self.mouse = mouse
        self.offset_x = offset_x
        self.offset_y = offset_y

    @property
    def x(self):
        return self.mouse.x + self.offset_x

    @property
    def y(self):
        return self.mouse.y + self.offset_y

class GenericBond:
    bond_mapper = {"i_am_parent_of":"-->", "i_am_in_connection_with":"--", "i_am_child_off":"<--", "-->":"-->", "--":"--", "<--":"<--"}

    def __init__(self, obj1:BaseInteractiveObject, bond:str, obj2:BaseInteractiveObject):
        # Setup and checks
        assert bond in ["i_am_parent_of", "-->", "i_am_in_connection_with", "--", "i_am_child_off", "<--"]
        assert obj1 != obj2
        self.obj1:BaseInteractiveObject = obj1
        self.bond_type = self.bond_mapper[bond]
        self.obj2:BaseInteractiveObject = obj2

        # Reversed
        if self.bond_type == "--":
            self.reversed = "--"
        if self.bond_type == "-->":
            self.reversed = "<--"
        if self.bond_type == "<--":
            self.reversed = "-->"

    def __eq__(self, other):
        A1, C1, B1 = self.obj1, self.bond_type, self.obj2
        A2, C2, B2 = other.obj1, other.bond_type, other.obj2

        # The obvious one:
        if (A1 == A2) and (C1 != C2) and (B1 != B2):
            return True

        # The crossed one:
        if (A1 == B2) and (A2 == B1):
            if (C1 == "--") and (C2 == "--"):
                return True
            if (C1 == "-->") and ("<--" == C2):
                return True
            if (C1 == "<--") and ("-->" == C2):
                return True

        # Must be false otherwise
        return False


###################################################################
# Base object classes
###################################################################


class Rectangle(BaseInteractiveObject):
    def __init__(self, screen, x, y, width, height, offset_x=0, offset_y=0, anchor=None, depth=0, is_previewing = False, is_selected = False, is_hovered = False, is_active = True, is_selectable=True, is_movable=True):
        super().__init__("Rectangle", screen, x, y, offset_x=offset_x, offset_y=offset_y, anchor=anchor, depth=depth, is_selected=is_selected, is_hovered=is_hovered, is_active=is_active, is_selectable=is_selectable, is_movable=is_movable, is_previewing=is_previewing)
        self.width = width
        self.height = height

    def respond(self, mouse:Mouse, keyboard:Keyboard, depth_map:np.ndarray) -> ObjectSignal:
        # Setup
        triggers = []

        # Hovered
        self.is_hovered = all(depth_map[mouse.x, mouse.y] == self.depth_color)
        if self.is_hovered:
            triggers.append(HOVERED)

        # Selected
        if self.is_selectable and (HOVERED in triggers) and mouse.left_pressed:
            triggers.append(SELECTED)

        # Wrap up
        signal = ObjectSignal(who=self, triggers=triggers)
        return signal


    def interact(self, interact:BaseInteractiveObject=None) -> None|BaseInteractiveObject:
        if not isinstance(interact, (Rectangle, Circle)):
            print("Unknown interaction")
            return None

        print(f"{self.object_type} interact")
        return SimpleObjectConnection(self.screen, self, interact, depth=0)

    def draw_depth(self, screen_depth:pygame.Surface):
        x_left, y_top = self.x - self.width//2, self.y - self.height//2
        W, H = self.width, self.height
        pygame.draw.rect(screen_depth, self.depth_color, (x_left, y_top, W, H))

    def draw(self):
        x_left, y_top = self.x - self.width//2, self.y - self.height//2
        W, H = self.width, self.height

        if self.is_previewing:
            pygame.draw.rect(self.screen, self.colors["preview"], (x_left, y_top, W, H), width=1)
            return
        elif self.is_selected:
            outline_color = self.colors["select"]
        elif self.is_hovered:
            outline_color = self.colors["hover"]
        else:
            outline_color = self.colors["outline"]

        pygame.draw.rect(self.screen, outline_color, (x_left, y_top, W, H))
        pygame.draw.rect(self.screen, self.colors["base"], (x_left+2, y_top+2, W-4, H-4))


class Circle(BaseInteractiveObject):
    def __init__(self, screen, x, y, radius, offset_x=0, offset_y=0, anchor=None, depth=0, is_previewing = False, is_selected = False, is_hovered = False, is_active = True, is_selectable=True, is_movable=True):
        super().__init__("Circle", screen, x, y, offset_x=offset_x, offset_y=offset_y, anchor=anchor, depth=depth, is_selected=is_selected, is_hovered=is_hovered, is_active=is_active, is_selectable=is_selectable, is_movable=is_movable, is_previewing=is_previewing)
        self.radius = radius
        center_text_box = TextRectangle(screen, 0, 0, radius//2, radius//2, text=self.unique_id, anchor=self, depth=99)
        self.add_bond("i_am_parent_of", center_text_box, True)

    def respond(self, mouse:Mouse, keyboard:Keyboard, depth_map:np.ndarray) -> ObjectSignal:
        # Setup
        x, y, r = self.x, self.y, self.radius
        triggers = []

        # Hovered
        self.is_hovered = all(depth_map[mouse.x, mouse.y] == self.depth_color)
        if self.is_hovered:
            triggers.append(HOVERED)

        # Selected
        if self.is_selectable and (HOVERED in triggers) and mouse.left_pressed:
            triggers.append(SELECTED)

        # Wrap up
        signal = ObjectSignal(who=self, triggers=triggers)
        return signal


    def interact(self, interact:BaseInteractiveObject=None) -> None|BaseInteractiveObject:
        if not isinstance(interact, (Rectangle, Circle)):
            print("Unknown interaction")
            return None

        # If node (A) is already connected to node (B) than I don't want to connect (B) with (A).
        connection_objs = [obj for obj in interact.get_all_objects() if isinstance(obj, SimpleObjectConnection)]
        if len(connection_objs) > 0:
            for connection_obj in connection_objs:
                if (connection_obj.obj1 is self) or (connection_obj.obj2 is self):
                    return None

        print(f"{self.object_type} interact")
        return SimpleObjectConnection(self.screen, self, interact)


    def draw_depth(self, screen_depth:pygame.Surface):
        x, y = self.x, self.y
        pygame.draw.circle(screen_depth, self.depth_color, (x, y), self.radius)


    def draw(self):
        x, y = self.x, self.y

        if self.is_previewing:
            pygame.draw.circle(self.screen, self.colors["preview"], (x, y), self.radius, width=1)
            return
        elif self.is_selected:
            outline_color = self.colors["select"]
        elif self.is_hovered:
            outline_color = self.colors["hover"]
        else:
            outline_color = self.colors["outline"]

        pygame.draw.circle(self.screen, outline_color, (x, y), self.radius)
        pygame.draw.circle(self.screen, self.colors["base"], (x, y), self.radius-2)


    def get_connection_anchor(self, interact:BaseInteractiveObject):
        if not isinstance(interact, SimpleObjectConnection):
            return self

        p1, p2 = interact.obj1, interact.obj2
        if p1 is not self:
            p1, p2 = p2, p1

        d = ((p2.x-p1.x)**2 + (p2.y-p1.y)**2)**0.5 + 1e-6
        r_factor = (self.radius + 5) / d
        return SimpleAnchor(p1.x+(p2.x-p1.x)*r_factor, p1.y+(p2.y-p1.y)*r_factor)


###################################################################
# Text classes
###################################################################


class TextRectangle(BaseInteractiveObject):
    def __init__(self, screen, x, y, width, height, text:str="", font_size=25, font_color=(230, 230, 230), offset_x=0, offset_y=0, anchor=None, depth=0, is_previewing = False, is_selected = False, is_hovered = False, is_active = True, is_selectable=True, is_movable=False, is_deletable=False):
        super().__init__("TextRectangle", screen, x, y, offset_x=offset_x, offset_y=offset_y, anchor=anchor, depth=depth, is_selected=is_selected, is_hovered=is_hovered, is_active=is_active, is_selectable=is_selectable, is_movable=is_movable, is_previewing=is_previewing, is_deletable=is_deletable)
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont(None, font_size)  # None uses the default font
        self.font_color = font_color
        self.text = text

    def respond(self, mouse:Mouse, keyboard:Keyboard, depth_map:np.ndarray) -> ObjectSignal:
        # Setup
        triggers = []

        # Hovered
        self.is_hovered = all(depth_map[mouse.x, mouse.y] == self.depth_color)
        if self.is_hovered:
            triggers.append(HOVERED)

        # Selected
        if self.is_selectable and (HOVERED in triggers) and mouse.left_pressed:
            triggers.append(SELECTED)

        # Wrap up
        signal = ObjectSignal(who=self, triggers=triggers)
        return signal


    def interact(self, interact:BaseInteractiveObject=None) -> None|BaseInteractiveObject:
        if not isinstance(interact, (Rectangle, Circle)):
            print("Unknown interaction")
            return None

    def draw_depth(self, screen_depth:pygame.Surface):
        x_left, y_top = self.x - self.width//2, self.y - self.height//2
        W, H = self.width, self.height
        pygame.draw.rect(screen_depth, self.depth_color, (x_left, y_top, W, H))

    def draw(self):
        x_left, y_top = self.x - self.width//2, self.y - self.height//2
        W, H = self.width, self.height

        if self.is_previewing:
            pygame.draw.rect(self.screen, self.colors["preview"], (x_left, y_top, W, H), width=1)
            return
        elif self.is_selected:
            outline_color = self.colors["select"]
        elif self.is_hovered:
            outline_color = self.colors["hover"]
        else:
            outline_color = self.colors["outline"]

        pygame.draw.rect(self.screen, outline_color, (x_left, y_top, W, H))
        pygame.draw.rect(self.screen, self.colors["base"], (x_left+2, y_top+2, W-4, H-4))

        # Draw centered text
        text = self.font.render(self.text, True, self.font_color)
        text_width, text_height = text.get_size()
        top_left_x = self.x - text_width // 2
        top_left_y = self.y - text_height // 2
        self.screen.blit(text, (top_left_x, top_left_y))


###################################################################
# Connection classes
###################################################################


class SimpleObjectConnection(BaseInteractiveObject):
    def __init__(self, screen, obj1:BaseInteractiveObject, obj2:BaseInteractiveObject, line_thickness:int=9, offset_x=0, offset_y=0, anchor=None, depth=0, is_previewing = False, is_selected = False, is_hovered = False, is_active = True, is_selectable=True, is_movable=False):
        super().__init__("SimpleObjectConnection", screen, x=None, y=None, offset_x=offset_x, offset_y=offset_y, anchor=anchor, depth=depth, is_selected=is_selected, is_hovered=is_hovered, is_active=is_active, is_selectable=is_selectable, is_movable=is_movable, is_previewing=is_previewing)
        assert line_thickness % 2 != 0, "Expect line thickness to be odd"
        self.line_thickness = line_thickness
        self.height_half = (line_thickness - 1) // 2
        self.obj1 = obj1
        self.obj2 = obj2
        self.obj1_anchor = self.obj1.get_connection_anchor(self)
        self.obj2_anchor = self.obj2.get_connection_anchor(self)


    def respond(self, mouse:Mouse, keyboard:Keyboard, depth_map:np.ndarray) -> ObjectSignal:
        # Setup
        self.obj1_anchor = self.obj1.get_connection_anchor(self)
        self.obj2_anchor = self.obj2.get_connection_anchor(self)
        triggers = []

        # # Hovered
        self.is_hovered = all(depth_map[mouse.x, mouse.y] == self.depth_color)
        if self.is_hovered:
            triggers.append(HOVERED)

        # Selected
        if self.is_selectable and (HOVERED in triggers) and mouse.left_pressed:
            triggers.append(SELECTED)

        # Wrap up
        signal = ObjectSignal(who=self, triggers=triggers)
        return signal


    def interact(self, interact:BaseInteractiveObject=None) -> None|BaseInteractiveObject:
        if not isinstance(interact, (Rectangle, Circle)):
            print("Unknown interaction")
            return None

        print(f"{self.object_type} interact")


    def draw_depth(self, screen_depth:pygame.Surface):
        p1 = self.obj1_anchor
        p2 = self.obj2_anchor
        pygame.draw.line(screen_depth, self.depth_color, (p1.x, p1.y), (p2.x, p2.y), width=self.line_thickness)


    def draw(self):
        p1 = self.obj1_anchor
        p2 = self.obj2_anchor

        if self.is_previewing:
            pygame.draw.line(self.screen, self.colors["preview"], (p1.x, p1.y), (p2.x, p2.y), width=self.line_thickness + 2)
            return
        elif self.is_selected:
            outline_color = self.colors["select"]
        elif self.is_hovered:
            outline_color = self.colors["hover"]
        else:
            outline_color = self.colors["outline"]

        pygame.draw.line(self.screen, outline_color, (p1.x, p1.y), (p2.x, p2.y), width=self.line_thickness)
        pygame.draw.line(self.screen, self.colors["base"], (p1.x, p1.y), (p2.x, p2.y), width=max(1, self.line_thickness-2))













































