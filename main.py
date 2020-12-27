import curses
from curses.textpad import Textbox, rectangle

from ui.overview import OverviewWindow
from ui.actions import ActionWindow
from ui.cmd import CommandWindow
#pylint: disable=E1101

# 0 = overview, 1 = actions, 2 = cmd
focused_win = 2



def main(stdscr):
    stdscr.addstr(0, 1, "Maledict [version: 0.0.0]")
    screen_width = curses.COLS - 1
    screen_height = curses.LINES - 1
    # get overview window
    overview_win = OverviewWindow(stdscr, 5, 3, 0.6 * screen_width, 0.75 * screen_height)
    action_win = ActionWindow(stdscr, overview_win.max_x + 5, 3, 0.3 * screen_width , 0.75 *screen_height)
    cmd_win = CommandWindow(stdscr, 5, overview_win.max_y + 1, action_win.max_x - 5, 0.2 * screen_height)
    stdscr.getch()


curses.wrapper(main)