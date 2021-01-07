from misc.utils import variadic_contains_or, check_input
from misc.utils import predict_business, predict_category
from misc.string_manip import format_date, format_time
from misc.utils import change_datetime, rectify_element, parse_expense
from data.record import Record
from data.sqlite_proxy import SQLiteProxy
from ui.static import WMAIN

import curses
import re
from sqlite3 import OperationalError as SQLiteOperationalError
from datetime import datetime

def expense(terminal, stdscr, index: str):
     # exception handling
    if terminal.windows[WMAIN].account == None:
        return ["current account not set"]
    if stdscr is None:
        return ["cannot edit expenses in warmup mode"]
    try:
        list_index = int(index, 16)
    except ValueError:
        return [f"expected hex value, got {index}"]
    if list_index > len(terminal.windows[WMAIN].account.records):
        return [f"given index does not exist"]

    # predictions
    org_record = terminal.windows[WMAIN].account.records[list_index].copy()
    pre_amount_str = '+' + str(org_record.amount) \
                      if org_record.amount > 0 else str(org_record.amount)
    tr_date = org_record.t_datetime
    # basic intialization
    terminal.exepnse_mode = True
    terminal.terminal_history.append(f"editing record 0x{hex(list_index)[2:].zfill(6)}:"
            f"{pre_amount_str} on {tr_date.isoformat(' ')} to {org_record.business}")
    terminal.command = ''
    terminal.cursor_x = 0
    terminal.redraw()
    S_AMOUNT = 0; S_BUSINESS = 1; S_CATEGORY = 2
    S_DATE = 3; S_TIME = 4; S_NOTE = 5
    sub_element_start = {S_DATE: [0, 5, 8],
                         S_TIME: [0, 3]}
    element_hint =  ['amount', 'payee', 'category', 'date', 'time', 'note']
    element_start = [0, 0, 0, 0, 0, 0]
    element_end   = [0, 0, 0, 0, 0, 0]
    elements = ['', '', '', '', '', '']
    state = 0
    sub_state = 0
    # some functions ------------------------------------------------------------------
    def input_allowed():
        if state == S_AMOUNT or state == S_BUSINESS or \
           state == S_CATEGORY or state == S_NOTE:
            return True
        return False
    def get_hint() -> str:
        return '=' * (element_start[state] + 3) + f" {element_hint[state]}:"
    def update_predictions(predicted_record: Record, force_update: bool):
        if state == S_AMOUNT and bool(re.match(terminal.command, pre_amount_str)):
            terminal.shadow_string = pre_amount_str
            terminal.shadow_index = 0
        elif state == S_BUSINESS:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.business
                terminal.shadow_index = element_start[1]
                return
            terminal.shadow_string, predicted_record = predict_business(elements[0], \
                terminal.command[element_start[1]:], terminal.windows[WMAIN].account)
            terminal.shadow_index = element_start[1]
        elif state == S_CATEGORY:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.subcategory \
                    if predicted_record.subcategory != '' \
                    else predicted_record.category
                terminal.shadow_index = element_start[2]
                return
            terminal.shadow_string, predicted_record = predict_category(elements[1], \
                terminal.command[element_start[2]:], terminal.windows[WMAIN].account)
            terminal.shadow_index = element_start[2]
        elif state == S_NOTE and bool(re.match(terminal.command[element_start[5]:], \
                                      org_record.note, re.I)):
            terminal.shadow_string = org_record.note
            terminal.shadow_index = element_start[5]
        else:
            terminal.shadow_string = ''
            terminal.shadow_index = 0
    # start accepting input -----------------------------------------------------------
    terminal.terminal_history.append(f"{get_hint()}")
    update_predictions(org_record, False)
    terminal.redraw()
    kb_interrupt = False
    while terminal.exepnse_mode:
        try:
            input_char = stdscr.getch()
            kb_interrupt = False
        except KeyboardInterrupt:
            if kb_interrupt or terminal.command == '':
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                return ["edit mode deactivated"]
            kb_interrupt = True
            elements = ['', '', '', '', '', '']
            terminal.command = ''
            terminal.cursor_x = 0
            state = sub_state = 0
            terminal.terminal_history[-1] = 'press ctrl + c again to exit edit mode'
            terminal.terminal_history.append(f'{get_hint()}')
            terminal.redraw()
            continue
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE:
            if input_allowed():
                terminal.cursor_x = max(element_start[state], terminal.cursor_x - 1)
                if terminal.cursor_x == len(terminal.command) - 1:
                    terminal.command = terminal.command[:terminal.cursor_x]
                    update_predictions(org_record, True)
                else:
                    terminal.command = terminal.command[:terminal.cursor_x] + \
                                    terminal.command[terminal.cursor_x + 1:]
                    update_predictions(org_record, True)
                terminal.redraw()
        elif input_char == curses.KEY_DC:
            if input_allowed() and len(terminal.command) != 0 and \
               terminal.cursor_x < len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + \
                                terminal.command[terminal.cursor_x + 1:]
                update_predictions(org_record, True)
                terminal.redraw()
        # submit ----------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == ord('\n'):
            element_end[state] = len(terminal.command) - 1
            elements[state] = terminal.command[element_start[state]: \
                                               element_end[state] + 1].strip()
            terminal.redraw()
            # done with editing
            if state == S_NOTE:
                parsed_record = parse_expense(elements, tr_date, \
                                              terminal.windows[WMAIN].account)
                terminal.windows[WMAIN].account.update_transaction(list_index, \
                                                                parsed_record)
                terminal.windows[WMAIN].update_table_row(list_index)
                terminal.windows[WMAIN].redraw()
                terminal.command = ''
                terminal.shadow_index = 0
                terminal.shadow_string = ''
                terminal.redraw()
                return ["edit successful"]
            # nothing written?
            elif elements[state] == '':
                continue
            error = check_input(elements[state], state)
            # accept & rectify the element, prepare next element
            if len(error) == 0:
                terminal.command += ' | '
                elements[state] = rectify_element(elements[state], state, terminal.windows[WMAIN].account)
                # skip payee for income
                if state == S_AMOUNT and elements[state][0] == '+':
                    element_start[state + 2] = element_end[state] + 4
                    state += 2
                else:
                    element_start[state + 1] = element_end[state] + 4
                    state += 1
                if state == S_DATE or state == S_TIME:
                    terminal.command += format_date(tr_date) \
                                        if state == S_DATE else \
                                        format_time(tr_date)
                    sub_state = 0
                    terminal.cursor_x = element_start[state] + \
                                        sub_element_start[state][0]
                else:
                    terminal.cursor_x = len(terminal.command)
                update_predictions(org_record, False)
                terminal.terminal_history[-1] = f"{get_hint()}"
            # reject & reset input
            else:
                elements[state] = ''
                element_end[state] = 0
                terminal.terminal_history[-1]= error
                terminal.terminal_history.append(get_hint())
                terminal.command = terminal.command[:element_start[state]]
                terminal.cursor_x = len(terminal.command)
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
        # suggestion surfing, changing date & time ------------------------------------
        elif input_char == curses.KEY_UP:
            if input_allowed():
                pass
            else:
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date) if state == S_DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        elif input_char == curses.KEY_DOWN:
            if input_allowed():
                pass
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
                terminal.cursor_x = max(element_start, terminal.cursor_x - 1)
                terminal.redraw()
            else:
                sub_state = max(0, sub_state - 1)
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
                terminal.redraw()
        elif input_char == curses.KEY_RIGHT:
            if input_allowed():
                terminal.cursor_x = min(len(terminal.command), terminal.cursor_x + 1)
                terminal.redraw()
            else:
                sub_state = min(len(sub_element_start[state]) - 1, sub_state + 1)
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
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
        elif input_char == ord('\t'):
            if terminal.shadow_string != '':
                terminal.command = terminal.command[:element_start[state]] + \
                                   terminal.shadow_string
                terminal.cursor_x = len(terminal.command)
                terminal.scroll = 0
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
        # normal input ----------------------------------------------------------------
        elif 32 <= input_char <= 154:
            if not input_allowed():
                continue
            if input_char == ord(' '):
                # leading spaces don't count
                if len(terminal.command) == element_start[state]:
                    terminal.redraw()
                    continue
            if terminal.cursor_x == len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + \
                    chr(input_char)
            else:
                terminal.command = terminal.command[:terminal.cursor_x] + \
                    chr(input_char) + terminal.command[terminal.cursor_x:]
            update_predictions(org_record, True)
            terminal.cursor_x += 1
            terminal.scroll = 0
            terminal.redraw()