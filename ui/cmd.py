import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
#pylint: disable=E1101



class CommandWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.command = ''
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
        if self.focused:
            self.cwindow.addstr(1, 2, ">>> ")
            self.cwindow.addstr(1, 6, self.command)
            # if we have a prediction, add it but dimmed
            # and without moving the cursor
            if self.prediction != '':
                self.cwindow.addstr(1, 6 + self.pred_start, self.prediction, curses.A_DIM)
                self.cwindow.move(1, 6 + len(self.command))
        else:
            self.cwindow.addstr(1, 2, ">>> ", curses.A_DIM)
            self.cwindow.addstr(1, 6, self.command, curses.A_DIM)
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
            elif input_str == '\n':
                self.command = ''
                self.segment = 0
                self.redraw()
                # TODO: perform task
            elif input_str == '\t':
                # do predictions
                pass
            elif len(input_str) == 1:
                if input_str == ' ':
                    self.segment += 1
                    self.pred_start = len(input_str)
                self.command += input_str
                self.redraw()
            