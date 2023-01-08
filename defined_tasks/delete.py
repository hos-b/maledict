import curses

from sqlite3 import OperationalError as SQLiteOperationalError

from misc.statics import WinID, KeyCombo


def account(terminal, stdscr, name: str) -> str:
    terminal.reset_input_field()
    terminal.append_to_history(
        f'delete {name} and all its transactions? '
          'this operation can >>NOT<< be reverted')
    terminal.redraw()
    delete_flag = False
    while True:
        try:
            input_char = stdscr.get_wch()
        except KeyboardInterrupt:
            terminal.append_to_history()
            terminal.redraw()
            return ['account deletion canceled']
        except:
            return ['unexpected error encountered']
        # escape = interrupt ----------------------------------------------------------
        if input_char == '\x1b':
            return ['account deletion canceled']
        # backspace, del --------------------------------------------------------------
        elif input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            terminal.delete_previous_char()
        elif input_char == curses.KEY_DC:
            terminal.delete_next_char()
        # submit ----------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            if terminal.command.lower() in ['y', 'yes', '1', 'true']:
                terminal.append_to_history(f'>>> {terminal.command}')
                terminal.reset_input_field()
                delete_flag = True
                break
            elif terminal.command.lower() in ['n', 'no', '0', 'false']:
                terminal.append_to_history(f'>>> {terminal.command}')
                terminal.reset_input_field()
                delete_flag = False
                break
            else:
                terminal.append_to_history(f'unexpected input {terminal.command}')
                terminal.reset_input_field()
            terminal.redraw()
        # cursor shift ----------------------------------------------------------------
        elif input_char == curses.KEY_LEFT:
            terminal.cursor_move_left()
        elif input_char == curses.KEY_RIGHT:
            terminal.cursor_move_right()
        elif input_char == KeyCombo.CTRL_LEFT:
            terminal.cursor_jump_left()
        elif input_char == KeyCombo.CTRL_RIGHT:
            terminal.cursor_jump_right()
        elif input_char == curses.KEY_HOME:
            terminal.cursor_jump_start()
        elif input_char == curses.KEY_END:
            terminal.cursor_jump_end()
        else:
            terminal.insert_char(input_char)

    if delete_flag:
        try:
            terminal.database.delete_account(name)
        except SQLiteOperationalError:
            return [f"account {name} doesn't exist"]
        except:
            return [f'could not delete account {name}... go figure out why']
        # if removing the current account
        current_account = terminal.windows[WinID.Main].account
        if current_account and current_account.name == name:
            terminal.windows[WinID.Main].change_current_account(None)
        return [f'successfully deleted {name}']
    else:
        return ['account deletion canceled']

def expense(main_window, index: str) -> str:
    try:
        transaction_id = int(index, 16)
    except ValueError:
        return [f'expected hex value, got {index}']
    list_index = -1
    for idx, record in enumerate(main_window.account.records):
        if record.transaction_id == transaction_id:
            list_index = idx
            break
    if list_index == -1:
        return [f'given transaction id does not exist']

    main_window.update_table_statistics(
        main_window.account.records[list_index].amount,
        main_window.account.currency_type(0, 0))
    main_window.account.delete_transaction(transaction_id)
    main_window.delete_table_row(list_index)
    return ['expense deleted successfully']