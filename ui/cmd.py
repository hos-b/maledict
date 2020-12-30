import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
#pylint: disable=E1101

class TerminalWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.command = ''
        self.history = []
        self.scroll = 0

        # prediction stuff
        self.segment = 0
        self.prediction = ''
        self.pred_start = 0

        self.redraw()

    def focus(self, enable: bool):
        self.focused = enable
        curses.curs_set(int(enable))
        if enable:
            self.cwindow.move(1, 6 + len(self.command))
        self.redraw()

    def redraw(self):
        self.cwindow.clear()
        # not using first or last line, 1 reserved for current command
        visible_history = min(len(self.history), self.w_height - 3)
        visible_history += self.scroll
        # disable cursor if scrolling
        curses.curs_set(int(self.scroll == 0 and self.focused))
        if self.focused:
            for i in range (self.w_height - 2):
                if visible_history == 0:
                    self.cwindow.addstr(i + 1, 2, ">>> ")
                    self.cwindow.addstr(i + 1, 6, self.command)
                    break
                self.cwindow.addstr(i + 1, 2, self.history[-visible_history])
                visible_history -= 1
        else:
            for i in range (self.w_height - 2):
                if visible_history == 0:
                    self.cwindow.addstr(i + 1, 2, ">>> ", curses.A_DIM)
                    self.cwindow.addstr(i + 1, 6, self.command, curses.A_DIM)
                    break
                self.cwindow.addstr(i + 1, 2, self.history[-visible_history], curses.A_DIM)
                visible_history -= 1
        self.cwindow.box()
        self.cwindow.refresh()

    def loop(self, stdscr) -> str:
        while True:
            input_str = stdscr.getkey()
            if CursesWindow.is_exit_sequence(input_str):
                return input_str
            elif input_str == 'KEY_BACKSPACE':
                if len(self.command) != 0:
                    self.command = self.command[:-1]
                    self.redraw()
            elif (input_str == '\n' or input_str == 'KEY_ENTER'):
                if self.command != '':
                    self.history.append(">>> " + self.command)
                self.command = ''
                self.segment = 0
                self.redraw()
                # TODO: perform task
            elif input_str == 'KEY_UP':
                max_scroll = len(self.history) + 3 - self.w_height
                # if we can show more than history + 3 reserved lines:
                if max_scroll > 0:
                    self.scroll = min(self.scroll + 1, max_scroll)
                self.redraw()
            elif input_str == 'KEY_DOWN':
                self.scroll = max(self.scroll - 1, 0)
                self.redraw()
            elif input_str == '\t':
                # do predictions
                pass
            elif len(input_str) == 1:
                self.scroll = 0
                if input_str == ' ':
                    # leading spaces don't count
                    if len(self.command) == 0:
                        continue
                    self.segment += 1
                    self.pred_start = len(input_str)
                self.command += input_str
                self.redraw()
