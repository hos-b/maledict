from misc.utils import change_datetime, rectify_element, parse_expense
from misc.utils import check_input, predict_business, predict_category
from misc.string_manip import format_date, format_time
from data.record import Record

from misc.statics import WinID, KeyCombo
import curses
import re


def expense(terminal, stdscr, index: str):
    # exception handling
    if terminal.windows[WinID.Main].account == None:
        return ["current account not set"]
    if stdscr is None:
        return ["cannot edit expenses in warmup mode"]
    try:
        transaction_id = int(index, 16)
    except ValueError:
        return [f"expected hex value, got {index}"]

    list_index = -1
    for idx, record in enumerate(
            terminal.windows[WinID.Main].account.records):
        if record.transaction_id == transaction_id:
            list_index = idx
            break
    if list_index == -1:
        return [f"given transaction id does not exist"]
    # predictions
    org_record: Record = terminal.windows[
        WinID.Main].account.records[list_index].copy()
    pre_amount_str = '+' + str(
        org_record.amount) if org_record.amount.float_value > 0 else str(
            org_record.amount)
    tr_date = org_record.t_datetime
    # basic intialization
    edit_mode = True
    terminal.terminal_history.append(
        f"editing record 0x{hex(transaction_id)[2:].zfill(6)}:"
        f"{pre_amount_str} on {tr_date.isoformat(' ')} to {org_record.business}"
    )
    terminal.command = ''
    terminal.cursor_x = 0
    S_AMOUNT = 0
    S_BUSINESS = 1
    S_CATEGORY = 2
    S_DATE = 3
    S_TIME = 4
    S_NOTE = 5
    sub_element_start = {S_DATE: [0, 5, 8], S_TIME: [0, 3]}
    sub_element_length = {S_DATE: [4, 2, 2], S_TIME: [2, 2]}
    element_hint = ['amount', 'payee', 'category', 'date', 'time', 'note']
    element_start = [0, 0, 0, 0, 0, 0]
    element_end = [0, 0, 0, 0, 0, 0]
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
        if state == S_AMOUNT and pre_amount_str.startswith(terminal.command):
            terminal.shadow_string = pre_amount_str
            terminal.shadow_index = 0
        elif state == S_BUSINESS:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.business
                terminal.shadow_index = element_start[S_BUSINESS]
                return
            terminal.shadow_string, predicted_record = predict_business(elements[0], \
                    terminal.command[element_start[S_BUSINESS]:], \
                    terminal.windows[WinID.Main].account)
            terminal.shadow_index = element_start[S_BUSINESS]
        elif state == S_CATEGORY:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.subcategory \
                    if predicted_record.subcategory != '' \
                    else predicted_record.category
                terminal.shadow_index = element_start[S_CATEGORY]
                return
            terminal.shadow_string, predicted_record = predict_category(elements[1], \
                    terminal.command[element_start[S_CATEGORY]:], \
                    terminal.windows[WinID.Main].account)
            terminal.shadow_index = element_start[S_CATEGORY]
        elif state == S_NOTE and bool(re.match(terminal.command[element_start[5]:], \
                                      org_record.note, re.I)):
            terminal.shadow_string = org_record.note
            terminal.shadow_index = element_start[S_NOTE]
        else:
            terminal.shadow_string = ''
            terminal.shadow_index = 0

    # start accepting input -----------------------------------------------------------
    update_predictions(org_record, False)
    terminal.terminal_history.append(get_hint())
    terminal.redraw()
    kb_interrupt = False
    while edit_mode:
        try:
            input_char = stdscr.get_wch()
            kb_interrupt = False
        except KeyboardInterrupt:
            if kb_interrupt or terminal.command == '':
                break
            terminal.shadow_string = ''
            terminal.shadow_index = 0
            kb_interrupt = True
            elements = ['', '', '', '', '', '']
            terminal.command = ''
            terminal.cursor_x = 0
            state = sub_state = 0
            terminal.terminal_history[
                -1] = 'press ctrl + c again to exit edit mode'
            terminal.terminal_history.append(get_hint())
            terminal.redraw()
            continue
        except:
            continue
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            if input_allowed():
                terminal.cursor_x = max(element_start[state],
                                        terminal.cursor_x - 1)
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
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            element_end[state] = len(terminal.command) - 1
            elements[state] = terminal.command[
                element_start[state]:element_end[state] + 1].strip()
            # done with editing
            if state == S_NOTE:
                parsed_record = parse_expense(
                    elements, tr_date, terminal.windows[WinID.Main].account)
                terminal.windows[WinID.Main].account.update_transaction(
                    transaction_id, parsed_record)
                terminal.windows[WinID.Main].update_table_row(list_index)
                terminal.windows[WinID.Main].update_table_statistics(
                    org_record.amount, parsed_record.amount)
                terminal.windows[WinID.Main].redraw()
                terminal.command = ''
                terminal.shadow_index = 0
                terminal.shadow_string = ''
                terminal.redraw()
                break
            # nothing written?
            elif elements[state] == '':
                continue
            error = check_input(elements[state], state)
            # accept & rectify the element, prepare next element
            if len(error) == 0:
                terminal.command += ' | '
                elements[state] = rectify_element(
                    elements[state], state,
                    terminal.windows[WinID.Main].account)
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
                update_predictions(org_record, False)
                terminal.terminal_history[-1] = get_hint()
            # reject & reset input
            else:
                elements[state] = ''
                element_end[state] = 0
                terminal.terminal_history[-1] = error
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
        # suggestion surfing, changing date & time ------------------------------------
        # TODO: add suggestion surfing, actually fix suggestions
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
                terminal.cursor_x = max(element_start[state],
                                        terminal.cursor_x - 1)
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
                terminal.cursor_x = min(len(terminal.command),
                                        terminal.cursor_x + 1)
                terminal.redraw()
            else:
                sub_state = min(
                    len(sub_element_start[state]) - 1, sub_state + 1)
                terminal.rtext_start = element_start[state] + \
                                       sub_element_start[state][sub_state]
                terminal.rtext_end = terminal.rtext_start + \
                                     sub_element_length[state][sub_state]
                terminal.redraw()
        elif input_char == KeyCombo.CTRL_LEFT and input_allowed():
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
        elif input_char == KeyCombo.CTRL_RIGHT:
            cut_str = terminal.command[terminal.cursor_x:]
            while len(cut_str) != 0 and cut_str[0] == ' ':
                cut_str = cut_str[1:]
                terminal.cursor_x = min(terminal.cursor_x + 1,
                                        len(terminal.command))
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
                terminal.command = terminal.command[:terminal.
                                                    cursor_x] + input_char

            else:
                terminal.command = terminal.command[:terminal.cursor_x] + input_char \
                                 + terminal.command[terminal.cursor_x:]
            update_predictions(org_record, True)
            terminal.cursor_x += 1
            terminal.scroll = 0
            terminal.redraw()

    # in case the edit was cancelled half way
    terminal.shadow_string = ''
    terminal.shadow_index = 0
    return ["edit mode deactivated"]