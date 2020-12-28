import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
#pylint: disable=E1101



class ActionWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.index = 0
        self.w_width = w_width
        self.options = [
            'ADD'.ljust(int(self.w_width) - 4),
            'EDIT'.ljust(int(self.w_width) - 4),
            'VIEW'.ljust(int(self.w_width) - 4),
            'FIND'.ljust(int(self.w_width) - 4),
            'SQL QUERY'.ljust(int(self.w_width) - 4),
            'SETTINGS'.ljust(int(self.w_width) - 4),
            'EXIT'.ljust(int(self.w_width) - 4)
        ]
        # curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        self.redraw()

    def focus(self, enable: bool):
        """
        enables or disables window focus
        """
        self.focused = enable
        self.redraw()
    
    def redraw(self):
        """
        redraws the actions menu
        """
        self.cwindow.clear()
        if self.focused:
            for i in range (len(self.options)):
                if i == self.index:
                    self.cwindow.addstr(i + 1, 2, self.options[i], curses.A_STANDOUT)
                else:
                    self.cwindow.addstr(i + 1, 2, self.options[i])
        else:
            for i in range (len(self.options)):
                self.cwindow.addstr(i + 1, 2, self.options[i], curses.A_DIM)
        self.cwindow.box()
        self.cwindow.refresh()
    
    def loop(self, stdscr) -> str:
        while True:
            input_str = stdscr.getkey()
            if CursesWindow.is_exit_sequence(input_str):
                return input_str
            if input_str == 'KEY_UP':
                self.index = max(0, self.index - 1)
                self.redraw()
            elif input_str == 'KEY_DOWN':
                self.index = min(len(self.options) - 1, self.index + 1)
                self.redraw()
            elif input_str == '\n':
                # TODO other functions
                if self.options[self.index].startswith('EXIT'):
                    return 'q'
