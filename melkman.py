import collections
import retro
from vector import V2

class Melkman:
    def __init__(self):
        self.lst = []
        self.hull = collections.deque()

    # Returns whether the points in `self.lst` form a simple polygonal chain.
    # If `v` is specified, the function assumes `self.lst` is already a
    # simple polygonal chain and verifies if the property is still true for
    # {`p`} U `self.lst`.
    def simple_polygonal_chain(self, v = None):
        # TODO add V2.intersection classmethod
        return True

    # Adds a new point `p` to `self.lst` if {`p`} U `self.lst` satisfies the
    # simple polygonal chain property. Then, apply the Melkman algorithm to
    # decide whether to add this point to `self.hull` or not.
    def add(self, p):
        v = V2(p, index = len(self.lst))
        # Initialize counter-clockwise hull
        if len(self.lst) < 2:
            self.lst.append(v)
        elif len(self.lst) == 2:
            self.lst.append(v)
            if V2.position(*self.lst) < 0: # clockwise -> 3213
                self.hull.extend(self.lst[::-1])
                self.hull.append(self.lst[-1])
            else: # counter-clockwise or colinear -> 3123
                self.hull.append(self.lst[-1])
                self.hull.extend(self.lst)
        # Update hull
        elif self.simple_polygonal_chain(v):
            self.lst.append(v)
            self.step(v)

    def step(self, v):
        def left_start(): return V2.position(
            self.hull[0], self.hull[1], v
        ) >= 0
        def left_end(): return V2.position(
            self.hull[-2], self.hull[-1], v
        ) >= 0

        if left_start() and left_end(): return
        while not left_start(): self.hull.popleft()
        while not left_end(): self.hull.pop()

        self.hull.appendleft(v)
        self.hull.append(v)

    def draw_points(self, collection, image, simple):
        for v in collection:
            if not simple: image.draw_circle(
                color  = retro.WHITE,
                center = tuple(v),
                radius = 10,
                width  = 0,
            )
            image.draw_circle(
                color  = retro.BLACK if simple else retro.RED,
                center = tuple(v),
                radius = 2 if simple else 10,
                width  = 0 if simple else 1,
            )
            if not simple:
                txt = retro.Sprite(retro.Font(18).render(
                    text      = str(v.index),
                    color     = retro.RED,
                    antialias = True,
                ))
                txt.rect.center = tuple(v)
                txt.draw(image)

    def draw_lines(self, collection, image, color):
        for i, _ in enumerate(collection):
            if i == len(collection) - 1: return
            v1 = collection[i]
            v2 = collection[i + 1]
            image.draw_line(
                color     = color,
                start_pos = tuple(v1),
                end_pos   = tuple(v2),
                width     = 1,
            )

    def draw(self, image):
        self.draw_points(self.lst, image, True)
        self.draw_lines(self.lst, image, retro.BLACK)
        self.draw_points(self.hull, image, False)
        self.draw_lines(self.hull, image, retro.RED)
