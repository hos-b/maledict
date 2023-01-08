import curses

import data.config as cfg

from data.account import Account
from data.record import Record
from misc.utils import change_datetime, rectify_element, parse_expense
from misc.utils import check_input, predict_business, predict_category
from misc.utils import ExpState
from misc.string_manip import format_date, format_time
from misc.statics import WinID, KeyCombo



def expense(terminal, stdscr, index: str):
    account: Account = terminal.windows[WinID.Main].account
    # exception handling
    if account is None:
        return ['current account not set']
    if stdscr is None:
        return ['cannot edit expenses in warmup mode']
    try:
        transaction_id = int(index, 16)
    except ValueError:
        return [f'expected hex value, got {index}']

    list_index = -1
    for idx, record in enumerate(account.records):
        if record.transaction_id == transaction_id:
            list_index = idx
            break
    if list_index == -1:
        return [f'given transaction id does not exist']
    # predictions
    org_record: Record = account.records[list_index].copy()
    pre_amount_str = org_record.amount.as_str(use_plus_sign=True)
    tr_date = org_record.t_datetime
    # basic intialization
    terminal.append_to_history(
        f"editing record 0x{hex(transaction_id)[2:].zfill(6)}:"
        f"{pre_amount_str} on {tr_date.isoformat(' ')} to {org_record.business}"
    )
    terminal.command = ''
    terminal.cursor_x = 0
    sub_element_start = {ExpState.DATE: [0, 5, 8], ExpState.TIME: [0, 3]}
    sub_element_length = {ExpState.DATE: [4, 2, 2], ExpState.TIME: [2, 2]}
    element_hint = ['amount', 'payee', 'category', 'date', 'time', 'note']
    element_start = [0, 0, 0, 0, 0, 0]
    element_end = [0, 0, 0, 0, 0, 0]
    elements = ['', '', '', '', '', '']
    state = ExpState.AMOUNT
    sub_state = 0

    # some functions ------------------------------------------------------------------
    def input_allowed():
        if state == ExpState.AMOUNT or state == ExpState.BUSINESS or \
           state == ExpState.CATEGORY or state == ExpState.NOTE:
            return True
        return False

    def get_hint() -> str:
        return '=' * (element_start[state] + 3) + f' {element_hint[state]}:'

    def update_predictions(predicted_record: Record, force_update: bool):
        if state == ExpState.AMOUNT and pre_amount_str.startswith(terminal.command):
            terminal.shadow_string = pre_amount_str
            terminal.shadow_index = 0
        elif state == ExpState.BUSINESS:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.business
                terminal.shadow_index = element_start[ExpState.BUSINESS]
                return
            terminal.shadow_string, predicted_record = predict_business(elements[0],
                    terminal.command[element_start[ExpState.BUSINESS]:], account)
            terminal.shadow_index = element_start[ExpState.BUSINESS]
        elif state == ExpState.CATEGORY:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.subcategory \
                    if predicted_record.subcategory != '' \
                    else predicted_record.category
                terminal.shadow_index = element_start[ExpState.CATEGORY]
                return
            terminal.shadow_string, predicted_record = predict_category(
                elements[ExpState.BUSINESS], 
                terminal.command[element_start[ExpState.CATEGORY]:],
                account)
            terminal.shadow_index = element_start[ExpState.CATEGORY]
        elif state == ExpState.NOTE and org_record.note.casefold().\
            startswith(terminal.command[element_start[5]:].casefold()):
            terminal.shadow_string = org_record.note
            terminal.shadow_index = element_start[ExpState.NOTE]
        else:
            terminal.shadow_string = ''
            terminal.shadow_index = 0

    # start accepting input -----------------------------------------------------------
    update_predictions(org_record, False)
    terminal.append_to_history(get_hint())
    terminal.redraw()
    kb_interrupt = False
    ec_interrupt = False
    while True:
        try:
            input_char = stdscr.get_wch()
            kb_interrupt = False
            ec_interrupt = False
        except KeyboardInterrupt:
            if kb_interrupt or terminal.command == '':
                break
            kb_interrupt = True
            state = sub_state = 0
            elements = ['', '', '', '', '', '']
            terminal.shadow_string = ''
            terminal.shadow_index = 0
            terminal.reset_input_field()
            terminal.print_history[-1] = 'press ctrl + c again to exit edit mode'
            terminal.append_to_history(get_hint())
            update_predictions(org_record, True)
            terminal.redraw()
            continue
        except:
            continue
        # escape = interrupt ----------------------------------------------------------
        if input_char == '\x1b':
            if ec_interrupt or terminal.command == '':
                break
            ec_interrupt = True
            state = sub_state = 0
            elements = ['', '', '', '', '', '']
            terminal.reset_input_field()
            terminal.shadow_string = ''
            terminal.shadow_index = 0
            terminal.print_history[-1] = 'press escape again to exit expense mode'
            terminal.append_to_history(get_hint())
            update_predictions(org_record, True)
            terminal.redraw()
            continue
        # backspace, del --------------------------------------------------------------
        elif input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            if input_allowed():
                terminal.delete_previous_char(element_start[state], False)
                update_predictions(org_record, True)
                terminal.redraw()
        elif input_char == curses.KEY_DC:
            if input_allowed():
                terminal.delete_next_char(False)
                update_predictions(org_record, True)
                terminal.redraw()
        # submit ----------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            element_end[state] = len(terminal.command) - 1
            elements[state] = terminal.command[
                element_start[state]:element_end[state] + 1].strip()
            # done with editing
            if state == ExpState.NOTE:
                parsed_record = parse_expense(elements, tr_date, account)
                account.update_transaction(transaction_id, parsed_record)
                terminal.windows[WinID.Main].update_table_row(list_index)
                terminal.windows[WinID.Main].update_table_statistics(
                    org_record.amount, parsed_record.amount)
                terminal.windows[WinID.Main].redraw()
                terminal.command = ''
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
                break
            # nothing written?
            elif elements[state] == '':
                continue
            error = check_input(elements[state], state, account.currency_type)
            # accept & rectify the element, prepare next element
            if error is None:
                terminal.command += ' ǁ ' if cfg.application.enable_utf8_support else ' | '
                elements[state] = rectify_element(elements[state], state, account)
                # skip payee for income
                if state == ExpState.AMOUNT and elements[state][0] == '+':
                    element_start[state + 2] = element_end[state] + 4
                    state += 2
                else:
                    element_start[state + 1] = element_end[state] + 4
                    state += 1
                # handle date & time input
                if state == ExpState.DATE or state == ExpState.TIME:
                    terminal.command += format_date(tr_date, cfg.application.use_jdate) \
                                        if state == ExpState.DATE else \
                                        format_time(tr_date)
                    sub_state = 2 if state == ExpState.DATE else 1
                    # enable reverse text
                    terminal.rtext_start = element_start[state] + \
                                           sub_element_start[state][sub_state]
                    terminal.rtext_end = terminal.rtext_start + \
                                         sub_element_length[state][sub_state]
                    terminal.reverse_text_enable = True
                else:
                    terminal.reverse_text_enable = False
                    terminal.cursor_x = len(terminal.command)
                terminal.print_history[-1] = get_hint()
                update_predictions(org_record, False)
            # reject & reset input
            else:
                elements[state] = ''
                element_end[state] = 0
                terminal.print_history[-1] = error
                terminal.append_to_history(get_hint())
                terminal.command = terminal.command[:element_start[state]]
                terminal.cursor_x = len(terminal.command)
            terminal.redraw()
        # history scrolling -----------------------------------------------------------
        elif input_char == curses.KEY_PPAGE:
            terminal.scroll_page_up()
        elif input_char == curses.KEY_NPAGE:
            terminal.scroll_page_down()
        # suggestion surfing, changing date & time ------------------------------------
        elif input_char == curses.KEY_UP:
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date, cfg.application.use_jdate) \
                                   if state == ExpState.DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        elif input_char == curses.KEY_DOWN:
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, -1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date, cfg.application.use_jdate) \
                                   if state == ExpState.DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        # cursor shift ----------------------------------------------------------------
        elif input_char == curses.KEY_LEFT:
            if input_allowed():
               terminal.cursor_move_left(element_start[state])
            else:
                sub_state = max(0, sub_state - 1)
                terminal.rtext_start = element_start[state] + \
                                       sub_element_start[state][sub_state]
                terminal.rtext_end = terminal.rtext_start + \
                                     sub_element_length[state][sub_state]
                terminal.redraw()
        elif input_char == curses.KEY_RIGHT:
            if input_allowed():
                terminal.cursor_move_right()
            else:
                sub_state = min(
                    len(sub_element_start[state]) - 1, sub_state + 1)
                terminal.rtext_start = element_start[state] + \
                                       sub_element_start[state][sub_state]
                terminal.rtext_end = terminal.rtext_start + \
                                     sub_element_length[state][sub_state]
                terminal.redraw()
        elif input_char == KeyCombo.CTRL_LEFT:
            if input_allowed():
                terminal.cursor_jump_left(element_start[state])
        elif input_char == KeyCombo.CTRL_RIGHT:
            if input_allowed():
                terminal.cursor_jump_right()
        elif input_char == curses.KEY_HOME:
            if input_allowed():
               terminal.cursor_jump_start(element_start[state])
            else:
                sub_state = 0
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
        elif input_char == curses.KEY_END:
            if input_allowed():
                terminal.cursor_jump_end()
            else:
                sub_state = 2 if state == ExpState.DATE else 1
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
        # do predictions --------------------------------------------------------------
        elif input_char == '\t':
            if terminal.shadow_string != '':
                terminal.command = terminal.command[:element_start[state]] + \
                                   terminal.shadow_string
                terminal.cursor_x = len(terminal.command)
                terminal.vscroll = 0
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
        # normal input ----------------------------------------------------------------
        elif input_allowed():
            terminal.insert_char(input_char, False)
            update_predictions(org_record, True)
            terminal.redraw()

    # in case the edit was cancelled half way
    terminal.shadow_string = ''
    terminal.shadow_index = 0
    terminal.reset_input_field()
    return ['edit mode deactivated']