import random
import collections
import itertools
from utils import Table
from vector import V2

class Mode:
    def __init__(self, area):
        self.area = area
        self.latestp = None
        self.instance = None

class InteractiveMode(Mode):
    NAME = "interactive"

    def __init__(self, area):
        Mode.__init__(self, area)
        self.instance = Melkman([])

    @property
    def finished(self): return False

    def next(self, p):
        self.latestp = self.instance.add(p)

class StepMode(Mode):
    NAME = "step"
    NPOINTS = 100

    def __init__(self, area):
        Mode.__init__(self, area)
        self.instance = Melkman(
            SimplePolygonalChain.generate(self.area, self.NPOINTS)
        )

    @property
    def finished(self): return (
        self.instance.hull
        and (not self.latestp)
    )

    def next(self, *args):
        self.latestp = self.instance.next()

class TestMode(Mode):
    NAME = "test"
    NPOINTS = 300
    CHECKS  = 5000
    SLICES  = 10

    def __init__(self, area):
        Mode.__init__(self, area)
        self.passed  = 0
        self.failed  = 0

    @property
    def checks(self): return self.passed + self.failed

    @property
    def finished(self): return self.checks >= self.CHECKS

    def next(self, *args):
        for _ in range(self.SLICES):
            if self.finished: return False
            self.instance = Melkman(
                SimplePolygonalChain.generate(self.area, self.NPOINTS)
            )
            self.instance.run()
            if self.instance.check(): self.passed += 1
            else: self.failed += 1 ; return False
        return True

# Proxy class for Melkman allowing to switch between modes.
# * Interactive: points are added individually to the simple polygonal chain.
# * Step: a simple polygonal chain is generated.
# * Test: algorithm robustness test.
class ModePicker:
    MODES = Table(
        interactive = InteractiveMode,
        step        = StepMode,
        test        = TestMode,
    )

    def __init__(self, area):
        self.mode = InteractiveMode(area)
        self.area = area

    def __getattr__(self, key):
        value = getattr(self.mode, key, None)
        if value is None: value = getattr(self.mode.instance, key, None)
        return value

    def select(self, mode):
        self.mode = mode(self.area)

class SimplePolygonalChain:
    # Generate a simple polygonal chain containing at most `n` points and
    # restricted to `area`.
    # Complexity: O(n^2)
    @classmethod
    def generate(cls, area, n):
        lst = []
        for _ in range(n):
            p = V2(
                random.randrange(area.x, area.width),
                random.randrange(area.y, area.height),
                index = len(lst),
            )
            if cls.verify(lst, p): lst.append(p)
        return lst

    # Given `lst`, a simple polygonal chain, verify if the property is still
    # true for `lst U {p}`.
    # Complexity: O(n)
    @classmethod
    def verify(cls, lst, p):
        if len(lst) <= 1: return True
        for i, _ in enumerate(lst):
            if i == len(lst) - 1: break
            if V2.intersection(
                a = lst[i],  b = lst[i + 1],
                c = lst[-1], d = p,
            ): return False
        return True

class Melkman:
    # Initializes the algorithm with a simple polygonal chain `lst`. If `lst`
    # is empty, points can be added later.
    def __init__(self, lst):
        self.lst = lst
        self.iter = iter(self.lst)
        self.hull = collections.deque()

    # Process all points from `self.lst`.
    # Complexity: O(n)
    def run(self):
        while self.next(): pass

    # Process the next point from `self.lst`.
    # Then, execute one step of the Melkman algorithm to decide whether to add
    # this point to `self.hull` or not.
    # Returns the latest processed point.
    # Complexity: O(1)
    def next(self):
        def init(i = 0):
            hull = (self.lst[i + 2], self.lst[0],
                    self.lst[i + 1], self.lst[i + 2])
            self.rotation = V2.rotation(*hull[1:])
            if self.rotation == 0: return init(i + 1)
            else:
                self.hull.extend(hull)
                for _ in range(i + 3): next(self.iter, None)
                return self.hull[-1]

        # Initialize hull
        if len(self.hull) == 0: return init()

        # Update hull
        p = next(self.iter, None)
        if p is None: return # finished
        self.step(p)

        return p

    # Add a new point `p` to `self.lst` if `self.lst U {p}` satisfies the
    # simple polygonal chain property.
    # Then, execute one step of the Melkman algorithm to decide whether to add
    # this point to `self.hull` or not.
    # Returns the latest processed point.
    # Complexity: O(n)
    def add(self, p):
        def init(p):
            self.lst.append(p)
            if len(self.lst) < 3: return
            hull = (self.lst[-1], self.lst[0], self.lst[-2], self.lst[-1])
            self.rotation = V2.rotation(*hull[1:])
            if self.rotation == 0: return # collinear
            self.hull.extend(hull)

        p = V2(p, index = len(self.lst))
        if not SimplePolygonalChain.verify(self.lst, p): return

        # Initialize hull
        if len(self.hull) == 0: init(p)
        # Update hull
        else:
            self.lst.append(p)
            self.step(p)

        return self.lst[-1]

    # Execute one step of the Melkman algorithm. Add `p` to `self.hull` if it
    # contributes to the convex hull. The `self.rotation` property must be
    # satisfied at each step of the algorithm.
    # Complexity: O(1)
    def step(self, p):
        def rotstart(): return V2.rotation(
            self.hull[0], self.hull[1], p
        ) == self.rotation
        def rotend(): return V2.rotation(
            self.hull[-2], self.hull[-1], p
        ) == self.rotation

        if rotstart() and rotend(): return
        while not rotstart(): self.hull.popleft()
        while not rotend(): self.hull.pop()

        self.hull.appendleft(p)
        self.hull.append(p)

    def __repr__(self): return " ".join(
        str(p.index) for p in self.hull
    )

    # Once the algorithm has processed the whole `self.lst`, this method can
    # check the validity of the convex hull.
    # For each edge [AB] in the hull, for every point P from `self.lst`,
    # check that the rotation for (A, B, P) is equal to `self.rotation` or 0
    # (colinear). It means that each point must be inside or on the hull.
    def check(self):
        # NB deque does not allow slice notation
        for i in range(len(self.hull) - 1):
            a = self.hull[i]
            b = self.hull[i + 1]
            for p in self.lst:
                r = V2.rotation(a, b, p)
                if (r != self.rotation) and (r != 0): return False
        return True
