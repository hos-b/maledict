import curses
from typing import Tuple
from data.record import Record
from misc.string_manip import fit_string

class CursesList:
    def __init__(self, x:int, y:int, l_width: int, l_height: int, items: list, \
                 scrollbar_enable, static_line = None):
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
        self.items = items
        self.static_line = static_line
        self.sl_length = len(self.static_line) if static_line else 0

        # scrolling & scrollbar
        self.scroll = 0
        self.scrollbar_enable = scrollbar_enable
        self.__calculate_scrollbar_size()

    def change_items(self, new_items: list):
        """
        changes the list itemes, resets index and recalculates
        the scrollbar size
        """
        self.index = 0
        self.items = new_items
        self.__calculate_scrollbar_size()

    def delete_item(self, index: int):
        """
        removes an item given the index, updates the index and
        recalculates the scrollbar size.
        """
        self.items.pop(index)
        self.index = min(len(self.items) - 1, index)
        self.__calculate_scrollbar_size()

    def redraw (self, cwindow, curses_attr):
        """
        redraws the list. it's assumed that the this call is placed inside the draw
        call of the containing window, i.e. the window's cleared before & refreshed
        after the call.
        """
        limit = min(len(self.items), self.l_height)
        sb_begin = 0
        sb_end = 0
        drawing_scrollbar = self.scrollbar_enable and self.scrollbar_size > 0
        if drawing_scrollbar:
            max_scroll = len(self.items) - self.l_height
            sb_mid = (self.scroll / max_scroll) * (self.l_height - 1)
            sb_mid = max(self.scrollbar_size / 2, min(sb_mid, self.l_height - self.scrollbar_size / 2))
            sb_begin = int(sb_mid - self.scrollbar_size / 2)
            sb_end = int(sb_begin + self.scrollbar_size)

        # draw column headers
        if self.static_line:
            cwindow.addstr(self.y - 2, self.x, ' ' * self.sl_length, curses.A_UNDERLINE | curses_attr)
            cwindow.addstr(self.y - 1, self.x, self.static_line, curses.A_UNDERLINE | curses_attr | curses.A_BOLD)

        # draw items
        for i in range (limit):
            list_index = i + self.scroll
            opt_str = self.items[list_index] # fit_string(, self.l_width)
            if i == self.index:
                cwindow.addstr(self.y + i, self.x, opt_str, curses_attr | curses.A_STANDOUT)
            else:
                cwindow.addstr(self.y + i, self.x, opt_str, curses_attr)
            # drawing scrollbar
            if drawing_scrollbar and sb_begin <= i <= sb_end:
                cwindow.addstr(self.y + i, self.x + len(opt_str) , " ▒", curses_attr)

        # draw lower border if we're showing columns
        if self.static_line:
            cwindow.addstr(self.y + self.l_height, self.x, ' ' * self.sl_length, curses.A_UNDERLINE | curses_attr)
            span_str = f' {self.scroll}-{self.scroll + limit} out of {len(self.items)} '
            cwindow.addstr(self.y + self.l_height, self.x + self.l_width - len(span_str) - 15, \
                                            span_str, curses_attr | curses.A_ITALIC)

    def move_selection_up(self):
        if self.index == 0:
            self.scroll = max(0, self.scroll - 1)
        else:
            self.index -= 1

    def move_selection_down(self):
        max_scroll = len(self.items) - self.l_height
        if self.index == self.l_height - 1 and max_scroll > 0:
            self.scroll = min(self.scroll + 1, max_scroll)
        else:
            self.index = min(self.index + 1, len(self.items) - 1)

    def scroll_page_up(self):
        if self.index != 0:
            self.index = 0
        else:
            self.scroll = max(0, self.scroll - self.l_height)

    def scroll_page_down(self):
        if self.index < self.l_height - 1:
            self.index = min(self.l_height - 1, len(self.items) - 1)
        else:
            max_scroll = len(self.items) - self.l_height
            if max_scroll > 0:
                self.scroll = min(self.scroll + self.l_height, max_scroll)

    def get_selected_item(self) -> Tuple[int, str]:
        return self.index + self.scroll, self.items[self.index + self.scroll]
    
    def __calculate_scrollbar_size(self):
        if len(self.items) <= self.l_height:
            self.scrollbar_size = 0
        else:
            self.scrollbar_size = max(1, (self.l_height * self.l_height) / len(self.items))