import curses, _curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
#pylint: disable=E1101



class OverviewWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_wperc, w_hperc):
        """ 
        initializes the curses window using the given measurements
        """
        window_w = int((curses.COLS - 1) * w_wperc)
        window_h = int((curses.LINES - 1) * w_hperc)
        self.cwindow = curses.newwin(window_h, window_w, w_y, w_x)
        curses.textpad.rectangle(stdscr, w_y - 1, w_x - 1, window_h + 5, window_w + 5)
        stdscr.refresh()

    def get_window(self) -> '_curses._CursesWindow':
        """
        returns the curses window
        """
        return self.cwindow

    def refresh(self):
        """
        refreshes the curses window
        """
        self.cwindow.refresh()

def get_overview(stdscr):
    # size measurements
    window_y = 5
    window_x = 5
    window_w = int((curses.COLS - 1) * 2 / 3)
    window_h = int((curses.LINES - 1) * 4 / 5)
    overview_win = curses.newwin(window_h, window_w, window_y, window_x)
    curses.textpad.rectangle(stdscr, window_y - 1, window_x - 1, window_h + 5, window_w + 5)
    return overview_win