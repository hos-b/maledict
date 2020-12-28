import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
#pylint: disable=E1101



class OverviewWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
    
    def loop(self, stdscr) -> str:
        while True:
            input_str = stdscr.getkey()
            if CursesWindow.is_exit_sequence(input_str):
                self.focused = False
                return input_str
    
    def focus(self, enable: bool):
        self.focused = enable
    
    def redraw(self):
        pass

