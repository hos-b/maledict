#!/usr/bin/env python

import os
import curses
from typing import List
from pathlib import Path

import maledict.data.config as cfg

from maledict.ui.base import CursesWindow
from maledict.ui.main import MainWindow
from maledict.ui.actions import ActionWindow
from maledict.ui.terminal import TerminalWindow
from maledict.misc.statics import WinID
from maledict.misc.utils import get_data_dir
from maledict.data.sqlite_proxy import SQLiteProxy
from maledict.version import version as app_version

BASE_CONFIG_PATH = \
    Path(__file__).absolute().parent.joinpath("config", "settings.yaml")
USER_CONFIG_PATH = get_data_dir().joinpath('custom-settings.yaml')

def main(stdscr):
    # getting screen data
    stdscr.addstr(0, 1, f'Maledict [version: {app_version}]')
    stdscr.keypad(True)

    screen_width = curses.COLS - 1
    screen_height = curses.LINES - 1

    # connecting to sqlite db
    database = SQLiteProxy(get_data_dir().joinpath('maledict.db'))

    # reading base config yaml
    cfg.update_config(BASE_CONFIG_PATH, True)
    if USER_CONFIG_PATH.exists():
        cfg.update_config(USER_CONFIG_PATH, False)

    windows: List[CursesWindow] = []
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


def app():
    # disable ESC delay. must be called before curses takes over
    os.environ.setdefault('ESCDELAY', '0')
    curses.wrapper(main)


if __name__ == "__main__":
    app()
