import curses
import yaml

from ui.main import MainWindow
from ui.actions import ActionWindow
from ui.terminal import TerminalWindow
from ui.static import WTERMINAL, WACTION, WMAIN

from parser.mk_parser import MKParser
from data.sqlite_proxy import SQLiteProxy

#pylint: disable=E1101


debugstr = ""
database = None
windows = []

def wrap_up(conf: dict):
    database.connection.commit()
    database.db_close()
    windows[WTERMINAL].write_command_history(conf['command_history_file_length'])

def main(stdscr):
    global debugstr
    global database
    global windows

    # getting screen data
    stdscr.addstr(0, 1, "Maledict [version: 1.0.1]")
    stdscr.keypad(True)

    screen_width = curses.COLS - 1
    screen_height = curses.LINES - 1

    # connecting to sqlite db
    database = SQLiteProxy('database/maledict.db')

    # reading config yaml
    conf_file = open('config/settings.yaml')
    conf = yaml.load(conf_file, Loader=yaml.FullLoader)

    # get overview window
    windows.append(MainWindow(stdscr, conf['main']['x'], conf['main']['y'], \
                   conf['main']['width_percentage'] * screen_width, \
                   conf['main']['height_percentage'] * screen_height, windows, conf))
    windows.append(ActionWindow(stdscr, windows[WMAIN].max_x + conf['action']['x_offset'], \
                                conf['action']['y'], conf['action']['width_percentage'] * \
                                screen_width , conf['action']['height_percentage'] * \
                                screen_height, windows))
    windows.append(TerminalWindow(stdscr, conf['terminal']['x'], windows[WMAIN].max_y + \
                                  conf['terminal']['y_offset'], windows[WACTION].max_x + \
                                  conf['terminal']['width_offset'], conf['terminal']['height_percentage'] * \
                                  screen_height, windows, database, conf))

    # initially disable cursor
    curses.curs_set(False)
    # 0 = overview, 1 = actions, 2 = cmd
    active_window = 2

    while True:
        windows[active_window].focus(True)
        break_char = windows[active_window].loop(stdscr)
        windows[active_window].focus(False)

        # changing window focus
        if break_char == curses.KEY_F1:
            # focus window 0 (main)
            active_window = 0
        elif break_char == curses.KEY_F2:
            # focus window 2 (terminal)
            active_window = 2
        elif break_char == curses.KEY_F60:
            # focus window 1 (actions)
            active_window = 1
        elif break_char == curses.KEY_F50:
            wrap_up(conf)
            break

curses.wrapper(main)