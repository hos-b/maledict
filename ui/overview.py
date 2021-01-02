import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow

from data.sqlite_proxy import SQLiteProxy
#pylint: disable=E1101

class OverviewWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height, database: SQLiteProxy):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.database = database
    
    def loop(self, stdscr) -> str:
        while True:
            input_str = stdscr.getch()
            if CursesWindow.is_exit_sequence(input_str):
                return input_str
    
    def redraw(self):
        pass

