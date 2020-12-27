import curses
from curses.textpad import Textbox, rectangle

from ui.overview import OverviewWindow
#pylint: disable=E1101


def main(stdscr):
    stdscr.addstr(0, 0, "welcome to eXpenis")
    # get overview window
    overview_win = OverviewWindow(stdscr, 5, 5, 2/3, 3/4)

    box = Textbox(overview_win.get_window())
    # Let the user edit until Ctrl-G is struck.
    box.edit()

    # Get resulting contents
    message = box.gather()

curses.wrapper(main)