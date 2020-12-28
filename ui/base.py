import curses
from ui.static import min_window_x, min_window_y

#pylint: disable=E1101

class CursesWindow:
    def __init__(self, stdscr, w_x, w_y, w_width, w_height):
        """ 
        initializes the curses window using the given measurements
        """
        self.min_x = max(w_x, 0)
        self.min_y = max(w_y, 0)
        w_width = int(min(w_width, curses.COLS - 1))
        w_height = int(min(w_height, curses.LINES - 1))
        self.max_x = self.min_x + w_width
        self.max_y = self.min_y + w_height
        self.cwindow = curses.newwin(w_height, w_width, int(w_y), int(w_x))
        self.cwindow.box()
        # self.cwindow.addstr(0, 0, f"rect from {self.min_x}, {self.min_y} to {self.max_x}, {self.max_y}: {rect_w}, {rect_h}")
        stdscr.refresh()
        self.cwindow.refresh()
        self.focused = False

    def refresh(self):
        """
        refreshes the curses window
        """
        self.cwindow.refresh()

    def focus(self, enable: bool):
        """
        basic changes in appearance when the window is selected
        """
        raise NotImplementedError

    def loop(self, stdscr) -> str:
        """
        main loop that captures input, performs tasks, etc.
        returns the key that relinquished control
        """
        raise NotImplementedError

    @staticmethod
    def is_exit_sequence(input_str: str):
        if input_str == 'q' or input_str == 'KEY_F(1)' or input_str == 'KEY_F(2)' or input_str == 'KEY_F(3)':
            return True
        return False