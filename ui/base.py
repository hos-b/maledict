import curses

#pylint: disable=E1101

class CursesWindow:
    def __init__(self, stdscr, w_x, w_y, w_width, w_height):
        """ 
        initializes the curses window using the given measurements
        """
        self.min_x = max(w_x, 0)
        self.min_y = max(w_y, 0)
        self.w_width = int(min(w_width, curses.COLS - 1))
        self.w_height = int(min(w_height, curses.LINES - 1))
        self.max_x = self.min_x + w_width
        self.max_y = self.min_y + w_height
        self.cwindow = curses.newwin(self.w_height, self.w_width, int(w_y), int(w_x))
        self.cwindow.box()
        stdscr.refresh()
        self.cwindow.refresh()
        self.focused = False

    def redraw(self):
        """
        redraws the window, according to its focus status
        """
        raise NotImplementedError

    def focus(self, enable: bool):
        """
        basic changes in appearance when the window is selected
        """
        self.focused = enable
        self.redraw()

    def loop(self, stdscr) -> str:
        """
        main loop that captures input, performs tasks, etc.
        returns the key that relinquished control
        """
        raise NotImplementedError

    @staticmethod
    def is_exit_sequence(input_char):
        if input_char == curses.KEY_F1 or input_char == curses.KEY_F2:
            return True
        return False