import ui
from utils import Table
from melkman import Melkman
from spc import SimplePolygonalChain as SPC

class Mode:
    def __init__(self, window):
        self.window = window
        self.melkman = None

    @property
    def latestp(self): return self.melkman.iter.current

    @property
    def area(self): return Table(
        x = 0, y = 0,
        width  =  self.window.canvas.winfo_width(),
        height =  self.window.canvas.winfo_height(),
    )

class Interactive(Mode):
    NAME = "interactive"

    def __init__(self, window):
        Mode.__init__(self, window)
        self.melkman = Melkman([])

    @property
    def finished(self): return False

    def next(self, p):
        self.melkman.add(p)
        self.window.update()

    def delete(self, i):
        self.melkman.delete(i)
        self.window.update()

class Step(Mode):
    NAME = "step"
    NPOINTS = 100

    def __init__(self, window):
        Mode.__init__(self, window)
        self.melkman = Melkman(SPC.generate(
            self.area, self.NPOINTS
        ))

    @property
    def finished(self): return self.melkman.iter.finished

    def next(self, *args):
        self.melkman.next()
        self.window.update()

    def delete(self, i):
        if   i ==  0: print("not yet implemented")
        elif i == -1: self.melkman.rewind()
        self.window.update()

class Test(Mode):
    NAME = "test"
    NPOINTS = 300
    CHECKS  = 5000
    SLICES  = 10

    def __init__(self, window):
        Mode.__init__(self, window)
        self.passed  = 0
        self.failed  = 0
        self.cancel  = False

    @property
    def checks(self): return self.passed + self.failed

    @property
    def slice(self): return (self.checks % self.SLICES == 0)

    @property
    def finished(self): return self.checks >= self.CHECKS

    def next(self, *args):
        while not self.finished and not self.cancel:
            self.melkman = Melkman(SPC.generate(
                self.area, self.NPOINTS
            ))
            self.melkman.run()
            if self.melkman.check():
                self.passed += 1
                if self.slice: self.window.update()
            else: self.failed += 1 ; return False

    def delete(self, i): pass

# Controller allowing to switch between modes to manipulate the melkman
# algorithm.
# * Interactive: points are added individually to the simple polygonal chain.
# * Step: a simple polygonal chain is generated.
# * Test: algorithm robustness test.
class Controller:
    MODES = Table(
        interactive = Interactive,
        step        = Step,
        test        = Test,
    )

    def __init__(self):
        self.window = ui.Window(self)
        self.mode = Interactive(self.window)
        self.window.update()
        self.window.protocol('WM_DELETE_WINDOW', self.exit)

    # Expose mode and model attributes.
    def __getattr__(self, key):
        value = getattr(self.mode, key, None)
        if value is None: value = getattr(self.mode.melkman, key, None)
        return value

    def select(self, mode):
        self.mode.cancel = True
        self.mode = mode(self.window)
        self.window.update()

    def delete(self, p = None, i = None):
        assert (i is not None) or (p is not None)
        if not self.mode.melkman.lst: return
        if i is None: i = p.index
        self.mode.delete(i)

    def loop(self):
        self.window.mainloop()

    def exit(self):
        self.mode.cancel = True
        self.window.destroy()
