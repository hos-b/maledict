import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
#pylint: disable=E1101



class CommandWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_wperc, w_hperc):
        super().__init__(stdscr, w_x, w_y, w_wperc, w_hperc)
        self.cwindow.addstr(1, 2, ">>> ")
        self.cwindow.refresh()

