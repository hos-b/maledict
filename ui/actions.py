import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
from data.sqlite_proxy import SQLiteProxy
#pylint: disable=E1101

class ActionWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height, \
                 overview_window: CursesWindow, database: SQLiteProxy):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.index = 0
        self.w_width = w_width
        self.options = [
            # 2 padding on each side
            'ADD'.ljust(int(self.w_width) - 4),
            'EDIT'.ljust(int(self.w_width) - 4),
            'VIEW'.ljust(int(self.w_width) - 4),
            'FIND'.ljust(int(self.w_width) - 4),
            'SQL QUERY'.ljust(int(self.w_width) - 4),
            'SETTINGS'.ljust(int(self.w_width) - 4),
            'EXIT'.ljust(int(self.w_width) - 4)
        ]
        # curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        self.overview_window = overview_window
        self.database = database
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
        curses_attr = curses.A_NORMAL if self.focused else curses.A_DIM
        for i in range (len(self.options)):
            if i == self.index:
                self.cwindow.addstr(i + 1, 2, self.options[i], curses_attr \
                                    | curses.A_STANDOUT if self.focused else curses.A_DIM)
            else:
                self.cwindow.addstr(i + 1, 2, self.options[i], curses_attr)
        self.cwindow.box()
        self.cwindow.refresh()
    
    def loop(self, stdscr) -> str:
        while True:
            input_char = stdscr.getch()
            if CursesWindow.is_exit_sequence(input_char):
                return input_char
            if input_char == curses.KEY_UP:
                self.index = max(0, self.index - 1)
                self.redraw()
            elif input_char == curses.KEY_DOWN:
                self.index = min(len(self.options) - 1, self.index + 1)
                self.redraw()
            elif input_char == ord('\n') or input_char == curses.KEY_ENTER:
                if self.options[self.index].startswith('EXIT'):
                    self.database.connection.commit()
                    self.database.db_close()
                    exit()
