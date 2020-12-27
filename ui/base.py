import curses, _curses
from ui.static import min_window_x, min_window_y

#pylint: disable=E1101

class CursesWindow:
    def __init__(self, stdscr, w_x, w_y, w_wperc, w_hperc):
        raise NotImplementedError
    def get_window(self) -> '_curses._CursesWindow':
        raise NotImplementedError
    def refresh(self):
        raise NotImplementedError

