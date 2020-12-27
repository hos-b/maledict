import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
#pylint: disable=E1101



class ActionWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_wperc, w_hperc):
        super().__init__(stdscr, w_x, w_y, w_wperc, w_hperc)
        self.cwindow.addstr(1, 2, "ADD")
        self.cwindow.addstr(2, 2, "EDIT")
        self.cwindow.addstr(3, 2, "VIEW")
        self.cwindow.addstr(4, 2, "FIND")
        self.cwindow.addstr(5, 2, "SQL QUERY")
        self.cwindow.addstr(5, 2, "SETTINGS")
        self.cwindow.refresh()
