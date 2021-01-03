import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
from ui.elements.list import CursesList
from data.sqlite_proxy import SQLiteProxy
#pylint: disable=E1101

class ActionWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height, \
                 main_window: CursesWindow):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.index = 0
        self.w_width = w_width
        self.options = ['ADD', 'EDIT', 'VIEW', 'FIND',
                        'SQL QUERY' ,'SETTINGS']
        # padding on the sides
        list_width = int(w_width - 4)
        list_height = int(w_height - 3)
        self.clist = CursesList(2, 1, list_width, list_height, self.options)
        # curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        self.main_window = main_window
        self.redraw()

    def focus(self, enable: bool):
        """
        overwriting base due to the extra element
        """
        self.focused = enable
        self.clist.focused = enable
        self.redraw()

    def redraw(self):
        """
        redraws the actions menu
        """
        self.cwindow.clear()
        curses_attr = curses.A_NORMAL if self.focused else curses.A_DIM
        self.clist.redraw(self.cwindow, curses_attr)
        self.cwindow.box()
        self.cwindow.refresh()
    
    def loop(self, stdscr) -> str:
        while True:
            input_char = stdscr.getch()
            if CursesWindow.is_exit_sequence(input_char):
                return input_char
            if input_char == curses.KEY_UP:
                self.clist.key_up()
                self.redraw()
            elif input_char == curses.KEY_DOWN:
                self.clist.key_down()
                self.redraw()
            elif input_char == ord('\n') or input_char == curses.KEY_ENTER:
                # opt_idx, opt_str = self.clist.key_enter()
                # TODO: add functionalities
                pass
