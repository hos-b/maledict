import curses

from ui.main import MainWindow
from ui.actions import ActionWindow
from ui.terminal import TerminalWindow

from parser.mk_parser import MKParser
from data.sqlite_proxy import SQLiteProxy
import csv
#pylint: disable=E1101


debugstr = ""
database = None
windows = []

def wrap_up():
    database.connection.commit()
    database.db_close()
    windows[2].write_command_history()

def main(stdscr):
    global debugstr
    global database
    global windows

    # getting screen data
    stdscr.addstr(0, 1, "Maledict [version: 0.0.0]")
    stdscr.keypad(True)
    screen_width = curses.COLS - 1
    screen_height = curses.LINES - 1

    # connecting to sqlite db
    database = SQLiteProxy('database/maledict.db')

    # get overview window
    windows.append(MainWindow(stdscr, 5, 3, 0.65 * screen_width, 0.75 * screen_height))
    windows.append(ActionWindow(stdscr, windows[0].max_x + 5, 3, 0.3 * screen_width , 0.75 * screen_height, windows[0]))
    windows.append(TerminalWindow(stdscr, 5, windows[0].max_y + 1, windows[1].max_x - 5, 0.2 * screen_height, windows[0], database))
    
    # initially disable cursor
    curses.curs_set(False)
    # TODO: comment out
    # stdscr = curses.initscr()
    # 0 = overview, 1 = actions, 2 = cmd
    active_window = 2
    
    while True:
        windows[active_window].focus(True)
        break_char = windows[active_window].loop(stdscr)
        windows[active_window].focus(False)
        # break_char = stdscr.getkey()
        # debugstr += (break_char + ' ')

        # changing window focus
        if break_char == curses.KEY_F1:
            # focus window 0 (overview)
            active_window = 0
        elif break_char == curses.KEY_F2:
            # focus window 2 (cmd)
            active_window = 2
        elif break_char == curses.KEY_F60:
            # focus window 1 (actions)
            active_window = 1

try:
    curses.wrapper(main)
except KeyboardInterrupt:
    wrap_up()
# except ValueError:
#     print("unexpected exit. did you ctrl-c in the middle of something?")
#     wrap_up()

# print(debugstr)