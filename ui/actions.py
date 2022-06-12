import curses
from misc.statics import WinID
from ui.base import CursesWindow
from ui.elements.list import CursesList
#pylint: disable=E1101

class ActionWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height, \
                 windows: list):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.index = 0
        self.w_width = w_width
        self.options = ['EDIT', 'DELETE', 'CANCEL', 'PLACEHOLDER #1',
                        'PLACEHOLDER #3','PLACEHOLDER #4','PLACEHOLDER #5',]
        # padding on the sides
        list_width = int(w_width - 4)
        list_height = int(w_height - 3)
        self.clist = CursesList(2, 1, list_width, list_height, self.options, False)
        # curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        self.windows = windows
        # index of the list element that enabled the window
        self.transaction_id = -1
        self.redraw()

    def focus(self, enable: bool):
        """
        overwriting base due to the extra element
        """
        self.focused = enable
        self.clist.focused = enable
        if not enable:
            self.list_index = -1
        self.redraw()

    def redraw(self):
        """
        redraws the actions menu
        """
        self.cwindow.erase()
        curses_attr = curses.A_NORMAL if self.focused else curses.A_DIM
        self.clist.redraw(self.cwindow, curses_attr)
        self.cwindow.box()
        self.cwindow.refresh()

    def loop(self, stdscr) -> str:
        while True:
            try:
                input_char = stdscr.getch()
            except KeyboardInterrupt:
                self.clist.index = 0
                return curses.KEY_F1

            if CursesWindow.is_exit_sequence(input_char):
                return input_char
            if input_char == curses.KEY_UP:
                self.clist.key_up()
                self.redraw()
            elif input_char == curses.KEY_DOWN:
                self.clist.key_down()
                self.redraw()
            elif input_char == ord('\n') or input_char == curses.KEY_ENTER:
                opt_idx, _ = self.clist.get_selected_item()
                if 0 <= opt_idx <= 2:
                    # if cancel, return focus to main window
                    if opt_idx == 2:
                        self.clist.index = 0
                        return curses.KEY_F1
                    # edit
                    self.windows[WinID.Terminal].pending_action = opt_idx
                    self.windows[WinID.Terminal].pending_tr_id = self.transaction_id
                    self.clist.index = 0
                    # switch to terminal to take care of pending tasks
                    return curses.KEY_F2
