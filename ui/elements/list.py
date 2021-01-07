import curses
from data.record import Record
from misc.string_manip import fit_string

class CursesList:
    def __init__(self, x:int, y:int, l_width: int, l_height: int, items: list, static_line = None):
        """
        creates a traversable list with the given width and height. the x and y are
        relative to the containing window. width and height are the ncurses col and
        row count.
        """
        self.y = y if static_line == None else y + 1
        self.x = x
        self.l_width = l_width
        self.l_height = l_height
        self.focused = False
        self.index = 0
        self.scroll = 0
        self.items = items
        self.static_line = static_line
        self.sl_length = len(self.static_line) if static_line else 0
    
    def redraw (self, cwindow, curses_attr):
        """
        redraws the list. it's assumed that the this call is placed inside the draw
        call of the containing window, i.e. the window's cleared before & refreshed
        after the call.
        """
        if self.static_line:
            cwindow.addstr(self.y - 2, self.x, ' ' * self.sl_length, curses.A_UNDERLINE | curses_attr)
            cwindow.addstr(self.y - 1, self.x, self.static_line, curses.A_UNDERLINE | curses_attr | curses.A_BOLD)
        limit = min(len(self.items), self.l_height)
        for i in range (limit):
            list_index = i + self.scroll
            opt_str = self.items[list_index] # fit_string(, self.l_width)
            if i == self.index:
                cwindow.addstr(self.y + i, self.x, opt_str, curses_attr | curses.A_STANDOUT \
                                                            if self.focused else curses.A_DIM)
            else:
                cwindow.addstr(self.y + i, self.x, opt_str, curses_attr)
        # draw lower border if we're showing columns
        if self.static_line:
            cwindow.addstr(self.y + self.l_height, self.x, ' ' * self.sl_length, curses.A_UNDERLINE | curses_attr)

    def key_up(self):
        if self.index == 0:
            self.scroll = max(0, self.scroll - 1)
        else:
            self.index -= 1

    def key_down(self):
        if self.index == self.l_height - 1:
            max_scroll = len(self.items) - self.l_height
            self.scroll = min(self.scroll + 1, max_scroll)
        else:
            self.index = min(self.index + 1, len(self.items) - 1)

    def key_pgup(self):
        if self.index != 0:
            self.index = 0
        else:
            self.scroll = max(0, self.scroll - self.l_height)

    def key_pgdn(self):
        if self.index < self.l_height - 1:
            self.index = min(self.l_height - 1, len(self.items) - 1)
        else:
            max_scroll = len(self.items) - self.l_height
            if max_scroll > 0:
                self.scroll = min(self.scroll + self.l_height, max_scroll)

    def key_enter(self) -> (int, str):
        return self.index, self.items[self.index]
    