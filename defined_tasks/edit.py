import re
import curses

from data.record import Record
from misc.utils import change_datetime, rectify_element, parse_expense
from misc.utils import check_input, predict_business, predict_category
from misc.utils import ExpState
from misc.string_manip import format_date, format_time
from misc.statics import WinID, KeyCombo



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
    state = 0
    sub_state = 0

    # some functions ------------------------------------------------------------------
    def input_allowed():
        if state == ExpState.AMOUNT or state == ExpState.BUSINESS or \
           state == ExpState.CATEGORY or state == ExpState.NOTE:
            return True
        return False

    def get_hint() -> str:
        return '=' * (element_start[state] + 3) + f" {element_hint[state]}:"

    def update_predictions(predicted_record: Record, force_update: bool):
        if state == ExpState.AMOUNT and pre_amount_str.startswith(terminal.command):
            terminal.shadow_string = pre_amount_str
            terminal.shadow_index = 0
        elif state == ExpState.BUSINESS:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.business
                terminal.shadow_index = element_start[ExpState.BUSINESS]
                return
            terminal.shadow_string, predicted_record = predict_business(elements[0], \
                    terminal.command[element_start[ExpState.BUSINESS]:], \
                    terminal.windows[WinID.Main].account)
            terminal.shadow_index = element_start[ExpState.BUSINESS]
        elif state == ExpState.CATEGORY:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.subcategory \
                    if predicted_record.subcategory != '' \
                    else predicted_record.category
                terminal.shadow_index = element_start[ExpState.CATEGORY]
                return
            terminal.shadow_string, predicted_record = predict_category(elements[1], \
                    terminal.command[element_start[ExpState.CATEGORY]:], \
                    terminal.windows[WinID.Main].account)
            terminal.shadow_index = element_start[ExpState.CATEGORY]
        elif state == ExpState.NOTE and bool(re.match(terminal.command[element_start[5]:], \
                                      org_record.note, re.I)):
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
            terminal.print_history[
                -1] = 'press ctrl + c again to exit edit mode'
            terminal.append_to_history(get_hint())
            terminal.redraw()
            continue
        except:
            continue
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            if input_allowed():
                terminal.delete_previous_char(element_start[state], False)
                update_predictions(True, org_record)
                terminal.redraw()
        elif input_char == curses.KEY_DC:
            if input_allowed():
                terminal.delete_next_char(False)
                update_predictions(True, org_record)
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
            if state == ExpState.NOTE:
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
                if state == ExpState.AMOUNT and elements[state][0] == '+':
                    element_start[state + 2] = element_end[state] + 4
                    state += 2
                else:
                    element_start[state + 1] = element_end[state] + 4
                    state += 1
                # handle date & time input
                if state == ExpState.DATE or state == ExpState.TIME:
                    terminal.command += format_date(tr_date) \
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
                update_predictions(org_record, False)
                terminal.print_history[-1] = get_hint()
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
        # TODO: add suggestion surfing, actually fix suggestions
        elif input_char == curses.KEY_UP:
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date) if state == ExpState.DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        elif input_char == curses.KEY_DOWN:
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, -1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date) if state == ExpState.DATE \
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
        elif input_char == KeyCombo.CTRL_LEFT and input_allowed():
            terminal.cursor_jump_left(element_start[state])
        elif input_char == KeyCombo.CTRL_RIGHT:
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
                terminal.scroll = 0
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
        # normal input ----------------------------------------------------------------
        else:
            terminal.insert_char(input_char, False)
            update_predictions(True, org_record)
            terminal.redraw()

    # in case the edit was cancelled half way
    terminal.shadow_string = ''
    terminal.shadow_index = 0
    return ["edit mode deactivated"]