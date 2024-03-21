#!/usr/bin/env python

import os
import curses

import data.config as cfg

from ui.main import MainWindow
from ui.actions import ActionWindow
from ui.terminal import TerminalWindow
from misc.statics import WinID
from data.sqlite_proxy import SQLiteProxy
from version import version as app_version


def main(stdscr):
    # getting screen data
    stdscr.addstr(0, 1, f'Maledict [version: {app_version}]')
    stdscr.keypad(True)

    screen_width = curses.COLS - 1
    screen_height = curses.LINES - 1

    # connecting to sqlite db
    db_path = os.path.join(os.path.dirname(__file__), 'database/maledict.db')
    database = SQLiteProxy(db_path)

    # reading config yaml
    cfg.update_config(
        os.path.join(os.path.dirname(__file__), 'config/settings.yaml'))

    windows = []
    # get overview window
    windows.append(
        MainWindow(stdscr, cfg.main.x, cfg.main.y,
                   cfg.main.width_percentage * screen_width,
                   cfg.main.height_percentage * screen_height, windows))
    windows.append(
        ActionWindow(stdscr, windows[WinID.Main].max_x + cfg.action.x_offset,
                     cfg.action.y, cfg.action.width_percentage * screen_width,
                     cfg.action.height_percentage * screen_height, windows))
    windows.append(
        TerminalWindow(stdscr, cfg.terminal.x,
                       windows[WinID.Main].max_y + cfg.terminal.y_offset,
                       windows[WinID.Action].max_x + cfg.terminal.width_offset,
                       cfg.terminal.height_percentage * screen_height, windows,
                       database))

    # initially disable cursor
    curses.curs_set(False)
    active_window = WinID.Terminal

    while True:
        windows[active_window].focus(True)
        break_char = windows[active_window].loop(stdscr)
        windows[active_window].focus(False)

        # changing window focus
        if break_char == curses.KEY_F1:
            # focus main window
            active_window = WinID.Main
        elif break_char == curses.KEY_F2:
            # focus terminal window
            active_window = WinID.Terminal
        elif break_char == curses.KEY_F60:
            # focus actions window
            active_window = WinID.Action
        elif break_char == curses.KEY_F50:
            database.connection.commit()
            database.db_close()
            windows[WinID.Terminal].write_command_history(
                cfg.application.command_history_file_length)
            break


# disable ESC delay. must be called before curses takes over
os.environ.setdefault('ESCDELAY', '0')
curses.wrapper(main)
