from misc.utils import variadic_contains_or
from data.record import Record
from data.sqlite_proxy import SQLiteProxy

import curses
from sqlite3 import OperationalError as SQLiteOperationalError
from datetime import datetime

def account(database: SQLiteProxy, name: str, initial_balance: str) -> str:
    try:
        balance_f = float(initial_balance)
    except:
        return [f"{initial_balance} is not a float value"]
    # should stop basic sql injections
    if name.count(';') > 0:
        return ["sneaky but no"]
    # this shouldn't be possible anyway but meh
    if name.count(' ') > 0:
        return ["account name cannot contain spaces"]
    # other stuff
    forbidden, frch = variadic_contains_or(name, '/', '\\','\'', '\"', '!', '?',\
                                                 '+', '=', '%', '*', '&', '^',\
                                                 '@', '#', '$', '~', '.', '`',\
                                                 '[', ']', '(', ')', '[', ']')
    if forbidden:
        return [f"account name cannot contain {frch}"]
    if balance_f < 0:
        return ["initial account balance cannot be negative. are you really that poor?"]

    try:
        database.create_table(name)
    except SQLiteOperationalError:
        return [f"account {name} already exists"]
    except:
        return [f"could not create account {name}... go figure out why"]
    
    # adding the initial balance
    # the account object doesn't get created until we use set account, therefor
    # we cannot use the much more convenient call: account.add_transaction(...)
    intial_record = Record(datetime(1, 1, 1, 0, 0, 0, 0), balance_f, '', '', '', 'initial balance')
    database.add_record(name, intial_record)
    database.connection.commit()
    return [f"successfully added {name} with {balance_f} initial balance"]


def expense(terminal, stdscr, chronological_order):
    S_AMOUNT = 0; S_BUSINESS = 1; S_CATEGORY = 2; S_YEAR = 3
    S_MONTH = 4; S_DAY = 5; S_HOUR = 6; S_MINUTE = 7; S_NOTE = 8
    # exception handling
    if terminal.main_window.account == None:
        return ["current account not set"]
    if stdscr is None:
        return ["cannot add expenses in warmup mode"]
    chronological = False
    if chronological_order in ['1', 'y', 'true', 'yes', 'ye', 't', 'yy', 'fuck']:
        chronological = True
    elif chronological_order in ['0', 'n', 'false', 'no', 'f', 'ff']:
        chronological = False
    else:
        return [f"expected boolean, got {chronological_order}"]

    terminal.exepnse_mode = True
    terminal.terminal_history.append("exepnse mode activated")
    terminal.command = ''
    terminal.cursor_x = 0
    terminal.redraw()
    transaction_date = datetime.now()
    # 0: amount, 1: business, 2: cat, 3: year
    # 4: month, 5: day, 6: hour, 7: minute, 8: note
    element_start = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    element_end = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    state = 0
    def input_allowed():
        if state == S_AMOUNT or state == S_BUSINESS or \
           state == S_CATEGORY or state == S_NOTE:
            return True
        return False
    
    interrupted = False
    while terminal.exepnse_mode:
        try:
            input_char = stdscr.getch()
            interrupted = False
        except KeyboardInterrupt:
            if interrupted or state == 0:
                # TODO: exit expense mode
                pass
            else:
                interrupted = True
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE:
            if input_allowed():
                terminal.cursor_x = max(element_start, terminal.cursor_x - 1)
                if terminal.cursor_x == len(terminal.command) - 1:
                    terminal.command = terminal.command[:terminal.cursor_x]
                else:
                    terminal.command = terminal.command[:terminal.cursor_x] + \
                                    terminal.command[terminal.cursor_x + 1:]
                terminal.redraw()
        elif input_char == curses.KEY_DC:
            if len(terminal.command) != 0 and terminal.cursor_x < len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + \
                                terminal.command[terminal.cursor_x + 1:]
                terminal.redraw()
        # execute ---------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == ord('\n'):
            if terminal.command != '':
                terminal.terminal_history.append(">>> " + terminal.command)
                
            terminal.command = ''
            terminal.scroll = 0
            terminal.cursor_x = 0
            terminal.redraw()
        # scrolling -------------------------------------------------------------------
        elif input_char == curses.KEY_PPAGE:
            max_scroll = len(terminal.terminal_history) + 3 - terminal.w_height
            # if we can show more than history + 3 reserved lines:
            if max_scroll > 0:
                terminal.scroll = min(terminal.scroll + 1, max_scroll)
            terminal.redraw()
        elif input_char == curses.KEY_NPAGE:
            terminal.scroll = max(terminal.scroll - 1, 0)
            terminal.redraw()
        # cursor shift ----------------------------------------------------------------
        elif input_char == curses.KEY_LEFT:
            terminal.cursor_x = max(0, terminal.cursor_x - 1)
            terminal.redraw()
        elif input_char == curses.KEY_RIGHT:
            terminal.cursor_x = min(len(terminal.command), terminal.cursor_x + 1)
            terminal.redraw()
        elif input_char == curses.KEY_HOME:
            cursor_y, _ = curses.getsyx()
            curses.setsyx(cursor_y, terminal.cursor_x_min)
            terminal.cursor_x = 0
            terminal.redraw()
        elif input_char == curses.KEY_END:
            terminal.cursor_x = len(terminal.command)
            terminal.redraw()
        # normal input ----------------------------------------------------------------
        elif input_char <= 256:
            if input_char == ord(' '):
                # leading spaces don't count
                if len(terminal.command) == 0:
                    continue
            if terminal.cursor_x == len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + chr(input_char)
            else:
                terminal.command = terminal.command[:terminal.cursor_x] + chr(input_char) + \
                                terminal.command[terminal.cursor_x:]
            terminal.cursor_x += 1
            terminal.cmd_history_index = 0
            terminal.scroll = 0
            terminal.redraw()