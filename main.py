import curses
from curses.textpad import Textbox, rectangle

from ui.overview import OverviewWindow
from ui.actions import ActionWindow
from ui.cmd import CommandWindow
#pylint: disable=E1101


debugstr = ""


def main(stdscr):
    global debugstr

    stdscr.addstr(0, 1, "Maledict [version: 0.0.0]")
    screen_width = curses.COLS - 1
    screen_height = curses.LINES - 1
    # get overview window
    windows = []
    windows.append(OverviewWindow(stdscr, 5, 3, 0.6 * screen_width, 0.75 * screen_height))
    windows.append(ActionWindow(stdscr, windows[0].max_x + 5, 3, 0.3 * screen_width , 0.75 *screen_height))
    windows.append(CommandWindow(stdscr, 5, windows[0].max_y + 1, windows[1].max_x - 5, 0.2 * screen_height))
    
    # initially disable cursor
    curses.curs_set(False)
    # TODO: comment out
    # stdscr = curses.initscr()

    # 0 = overview, 1 = actions, 2 = cmd
    active_window = 0

    while True:
        # break_str = stdscr.getkey()
        windows[active_window].focus(True)
        break_str = windows[active_window].loop(stdscr)
        windows[active_window].focus(False)
        debugstr += (break_str + ' ')

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