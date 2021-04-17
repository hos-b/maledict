from misc.utils import variadic_contains_or, check_input
from misc.utils import predict_business, predict_category
from misc.string_manip import format_date, format_time
from misc.utils import change_datetime, rectify_element, parse_expense
from data.record import Record
from data.sqlite_proxy import SQLiteProxy
from ui.static import WMAIN
import curses
from sqlite3 import OperationalError as SQLiteOperationalError
from datetime import datetime

def account(database: SQLiteProxy, name: str, initial_balance: str) -> str:
    try:
        balance_f = float(initial_balance)
    except:
        return [f"{initial_balance} is not a float value"]
    # should stop basic sql injections
    if ';' in name:
        return ["sneaky but no"]
    # this shouldn't be possible anyway but meh
    if ' ' in name:
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
    if balance_f > 0:
        intial_record = Record(datetime(1, 1, 1, 0, 0, 0, 0), balance_f, '', '', '', 'initial balance')
        database.add_record(name, intial_record)
        database.connection.commit()

    return [f"successfully added {name} with {balance_f} initial balance"]


def expense(terminal, stdscr):
    # exception handling
    if terminal.windows[WMAIN].account == None:
        return ["current account not set"]
    if stdscr is None:
        return ["cannot add expenses in warmup mode"]

    expense_mode = True
    terminal.terminal_history.append("expense mode activated")
    terminal.command = ''
    terminal.cursor_x = 0
    curses.curs_set(1)
    tr_date = datetime.now()
    tr_date = tr_date.replace(second=0, microsecond=0)
    S_AMOUNT = 0; S_BUSINESS = 1; S_CATEGORY = 2
    S_DATE = 3; S_TIME = 4; S_NOTE = 5
    sub_element_start = {S_DATE: [0, 5, 8],
                         S_TIME: [0, 3]}
    sub_element_length = {S_DATE: [4, 2, 2],
                          S_TIME: [2, 2]}
    element_hint =  ['amount', 'payee', 'category', 'date', 'time', 'note']
    element_start = [0, 0, 0, 0, 0, 0]
    element_end   = [0, 0, 0, 0, 0, 0]
    elements = ['', '', '', '', '', '']
    state = 0
    sub_state = 0
    # predictions
    predicted_record = None
    # some functions ------------------------------------------------------------------
    def input_allowed():
        if state == S_AMOUNT or state == S_BUSINESS or \
           state == S_CATEGORY or state == S_NOTE:
            return True
        return False
    def get_hint() -> str:
        return '=' * (element_start[state] + 3) + f" {element_hint[state]}:"
    def update_predictions(force_update: bool, predicted_record: Record):
        # global predicted_record
        if state == S_BUSINESS:
            terminal.shadow_string, predicted_record = predict_business(elements[0], \
                terminal.command[element_start[1]:], terminal.windows[WMAIN].account)
            terminal.shadow_index = element_start[1]
        elif state == S_CATEGORY:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.subcategory
                terminal.shadow_index = element_start[2]
                return
            terminal.shadow_string, predicted_record = predict_category(elements[1], \
                terminal.command[element_start[2]:], terminal.windows[WMAIN].account)
            terminal.shadow_index = element_start[2]
        else:
            terminal.shadow_string = ''
            terminal.shadow_index = 0
    # start accepting input -----------------------------------------------------------
    terminal.terminal_history.append(f"{get_hint()}")
    terminal.redraw()
    kb_interrupt = False
    while expense_mode:
        try:
            input_char = stdscr.get_wch()
            kb_interrupt = False
        except KeyboardInterrupt:
            if kb_interrupt or terminal.command == '':
                break
            kb_interrupt = True
            elements = ['', '', '', '', '', '']
            terminal.command = ''
            terminal.cursor_x = 0
            state = sub_state = 0
            terminal.shadow_string = ''
            terminal.shadow_index = 0
            terminal.terminal_history[-1] = 'press ctrl + c again to exit expense mode'
            terminal.terminal_history.append(f'{get_hint()}')
            terminal.redraw()
            continue
        except:
            continue
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            if input_allowed():
                terminal.cursor_x = max(element_start[state], terminal.cursor_x - 1)
                if terminal.cursor_x == len(terminal.command) - 1:
                    terminal.command = terminal.command[:terminal.cursor_x]
                    update_predictions(True, predicted_record)
                else:
                    terminal.command = terminal.command[:terminal.cursor_x] + \
                                    terminal.command[terminal.cursor_x + 1:]
                    update_predictions(True, predicted_record)
                terminal.redraw()
        elif input_char == curses.KEY_DC:
            if input_allowed() and len(terminal.command) != 0 and \
               terminal.cursor_x < len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + \
                                terminal.command[terminal.cursor_x + 1:]
                update_predictions(True, predicted_record)
                terminal.redraw()
        # submit ----------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            element_end[state] = len(terminal.command) - 1
            elements[state] = terminal.command[element_start[state]: \
                                               element_end[state] + 1].strip()
            terminal.redraw()
            # adding the expense
            if state == S_NOTE:
                parsed_record = parse_expense(elements, tr_date, \
                                              terminal.windows[WMAIN].account)
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                terminal.windows[WMAIN].account.add_transaction(parsed_record)
                terminal.windows[WMAIN].account.query_transactions(
                    terminal.windows[WMAIN].account.full_query, False)
                terminal.windows[WMAIN].refresh_table_records('all transactions')
                terminal.terminal_history[-1] = str(elements)
                elements = ['', '', '', '', '', '']
                terminal.command = ''
                terminal.cursor_x = 0
                state = sub_state = 0
                terminal.terminal_history.append(f"{get_hint()}")
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
                continue
            # nothing written?
            elif elements[state] == '':
                continue
            errors = check_input(elements[state], state)
            # accept & rectify the element, prepare next element
            if len(errors) == 0:
                terminal.command += ' | '
                elements[state] = rectify_element(elements[state], state, \
                                                  terminal.windows[WMAIN].account)
                # skip payee for income
                if state == S_AMOUNT and elements[state][0] == '+':
                    element_start[state + 2] = element_end[state] + 4
                    state += 2
                else:
                    element_start[state + 1] = element_end[state] + 4
                    state += 1
                # handle date & time input
                if state == S_DATE or state == S_TIME:
                    terminal.command += format_date(tr_date) \
                                        if state == S_DATE else \
                                        format_time(tr_date)
                    # prefer day|minute over other fields
                    sub_state = 2 if state == S_DATE else 1
                    # enable reverse text
                    terminal.rtext_start = element_start[state] + \
                                           sub_element_start[state][sub_state]
                    terminal.rtext_end = terminal.rtext_start + \
                                         sub_element_length[state][sub_state]
                    terminal.reverse_text_enable = True
                else:
                    terminal.reverse_text_enable = False
                    terminal.cursor_x = len(terminal.command)
                terminal.terminal_history[-1] = f"{get_hint()}"
                update_predictions(False, predicted_record)
            # reject & reset input
            else:
                elements[state] = ''
                element_end[state] = 0
                terminal.terminal_history[-1]= errors
                terminal.terminal_history.append(get_hint())
                terminal.command = terminal.command[:element_start[state]]
                terminal.cursor_x = len(terminal.command)
            terminal.redraw()
        # history scrolling -----------------------------------------------------------
        elif input_char == curses.KEY_PPAGE:
            max_scroll = len(terminal.terminal_history) + 3 - terminal.w_height
            # if we can show more than history + 3 reserved lines:
            if max_scroll > 0:
                terminal.scroll = min(terminal.scroll + 1, max_scroll)
            terminal.redraw()
        elif input_char == curses.KEY_NPAGE:
            terminal.scroll = max(terminal.scroll - 1, 0)
            terminal.redraw()
        # record scrolling ------------------------------------------------------------
        elif input_char == 555: # ctrl + page up            
            terminal.windows[WMAIN].clist.key_pgup()
            terminal.windows[WMAIN].redraw()
            terminal.redraw()
        elif input_char == 550: # ctrl + page down
            terminal.windows[WMAIN].clist.key_pgdn()
            terminal.windows[WMAIN].redraw()
            terminal.redraw()
        elif input_char == 566: # ctrl + up
            terminal.windows[WMAIN].clist.key_up()
            terminal.windows[WMAIN].redraw()
            terminal.redraw()
        elif input_char == 525: # ctrl + down
            terminal.windows[WMAIN].clist.key_down()
            terminal.windows[WMAIN].redraw()
            terminal.redraw()
        # suggestion surfing, changing date & time ------------------------------------
        elif input_char == curses.KEY_UP:
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date) if state == S_DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        elif input_char == curses.KEY_DOWN:
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, -1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date) if state == S_DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        # cursor shift ----------------------------------------------------------------
        elif input_char == curses.KEY_LEFT:
            if input_allowed():
                terminal.cursor_x = max(element_start[state], terminal.cursor_x - 1)
                terminal.redraw()
            else:
                sub_state = max(0, sub_state - 1)
                terminal.rtext_start = element_start[state] + \
                                       sub_element_start[state][sub_state]
                terminal.rtext_end = terminal.rtext_start + \
                                     sub_element_length[state][sub_state]
                terminal.redraw()
        elif input_char == curses.KEY_RIGHT:
            if input_allowed():
                terminal.cursor_x = min(len(terminal.command), terminal.cursor_x + 1)
                terminal.redraw()
            else:
                sub_state = min(len(sub_element_start[state]) - 1, sub_state + 1)
                terminal.rtext_start = element_start[state] + \
                                       sub_element_start[state][sub_state]
                terminal.rtext_end = terminal.rtext_start + \
                                     sub_element_length[state][sub_state]
                terminal.redraw()
        elif input_char == 545 and input_allowed(): # ctrl + left ---------------------
            cut_str = terminal.command[element_start[state]: \
                                        terminal.cursor_x][::-1]
            while len(cut_str) != 0 and cut_str[0] == ' ':
                cut_str = cut_str[1:]
                terminal.cursor_x = max(element_start[state], \
                                        terminal.cursor_x - 1)
            next_jump = cut_str.find(' ')
            if next_jump == -1:
                terminal.cursor_x = element_start[state]
            else:
                terminal.cursor_x = max(element_start[state], \
                                        terminal.cursor_x - next_jump)
            terminal.redraw()
        elif input_char == 560 and input_allowed(): # ctrl + right --------------------
            cut_str = terminal.command[terminal.cursor_x:]
            while len(cut_str) != 0 and cut_str[0] == ' ':
                cut_str = cut_str[1:]
                terminal.cursor_x = min(terminal.cursor_x + 1, len(terminal.command))
            next_jump = cut_str.find(' ')
            if next_jump == -1:
                terminal.cursor_x = len(terminal.command)
            else:
                terminal.cursor_x = min(terminal.cursor_x + next_jump, \
                                        len(terminal.command))
                cut_str = terminal.command[terminal.cursor_x:]
            terminal.redraw()
        elif input_char == curses.KEY_HOME:
            if input_allowed():
                terminal.cursor_x = element_start[state]
                terminal.redraw()
            else:
                sub_state = 0
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
        elif input_char == curses.KEY_END:
            if input_allowed():
                terminal.cursor_x = len(terminal.command)
                terminal.redraw()
            else:
                sub_state = 2 if state == S_DATE else 1
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
        # do predictions --------------------------------------------------------------
        elif input_char == '\t':
            if terminal.shadow_string != '':
                terminal.command = terminal.command[:element_start[state]] + \
                                   terminal.shadow_string
                terminal.cursor_x = len(terminal.command)
                terminal.scroll = 0
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
        # normal input ----------------------------------------------------------------
        else:
            if not input_allowed():
                continue
            # some command that's not used
            if type(input_char) is int:
                continue
            if input_char == ' ':
                # leading spaces don't count
                if len(terminal.command) == element_start[state]:
                    terminal.redraw()
                    continue
            if terminal.cursor_x == len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + input_char
            else:
                terminal.command = terminal.command[:terminal.cursor_x] + input_char \
                                 + terminal.command[terminal.cursor_x:]
            update_predictions(True, predicted_record)
            terminal.cursor_x += 1
            terminal.scroll = 0
            terminal.redraw()

    terminal.windows[WMAIN].account.flush_transactions()
    terminal.shadow_string = ''
    terminal.shadow_index = 0
    return ["expense mode deactivated"]