import curses

from ui.overview import OverviewWindow
from ui.actions import ActionWindow
from ui.terminal import TerminalWindow

from parser.mk_parser import MKParser
from data.sqlite_proxy import SQLiteProxy
import csv
#pylint: disable=E1101


debugstr = ""


def main(stdscr):
    global debugstr

    # getting screen data
    stdscr.addstr(0, 1, "Maledict [version: 0.0.0]")
    stdscr.keypad(True)
    screen_width = curses.COLS - 1
    screen_height = curses.LINES - 1

    # connecting to sqlite db
    database = SQLiteProxy('database/maledict.db')

    # get overview window
    windows = []
    windows.append(OverviewWindow(stdscr, 5, 3, 0.6 * screen_width, 0.75 * screen_height, database))
    windows.append(ActionWindow(stdscr, windows[0].max_x + 5, 3, 0.3 * screen_width , 0.75 *screen_height, windows[0]))
    windows.append(TerminalWindow(stdscr, 5, windows[0].max_y + 1, windows[1].max_x - 5, 0.2 * screen_height, windows[0], database))
    
    # initially disable cursor
    curses.curs_set(False)
    # TODO: comment out
    # stdscr = curses.initscr()

    # 0 = overview, 1 = actions, 2 = cmd
    active_window = 2

    # return
    while True:
        windows[active_window].focus(True)
        break_str = windows[active_window].loop(stdscr)
        windows[active_window].focus(False)
        # break_str = stdscr.getkey()
        # debugstr += (break_str + ' ')

        # exiting or changing window focus
        if break_str == 'q' or break_str == '\t':
            break
        elif break_str == 'KEY_F(1)':
            # focus window 0 (overview)
            active_window = 0
        elif break_str == 'KEY_F(2)':
            # focus window 1 (actions)
            active_window = 1
        elif break_str == 'KEY_F(3)':
            # focus window 2 (cmd)
            active_window = 2

curses.wrapper(main)
print(debugstr)