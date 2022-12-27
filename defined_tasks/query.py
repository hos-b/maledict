import re
import curses
import sqlite3

from typing import Dict

from data.account import Account
from data.record import Record
from misc.statics import WinID, KeyCombo
from datetime import datetime


def sqlite(terminal, stdscr):
    account: Account = terminal.windows[WinID.Main].account
    # exception handling
    if account == None:
        return ['current account not set']
    if stdscr is None:
        return ['cannot query in warmup mode']

    db_connection = account.database.connection
    table_map: Dict[str, int] = account.database.table_map
    table_cols = [i[0] for i in sorted(table_map.items(), key = lambda x: x[1])]
    terminal.windows[WinID.Main].disable_actions = True
    potential_table_update = False
    # back up previous state of the main window and terminal
    org_table_label = terminal.windows[WinID.Main].table_label
    org_terminal_ch = terminal.command_history
    org_terminal_hsi = terminal.history_surf_index
    org_terminal_chb = terminal.cmd_history_buffer
    terminal.command_history = []
    terminal.history_surf_index = 0
    terminal.cmd_history_buffer = ''

    terminal.append_to_history('query mode activated')
    terminal.append_to_history('> column names: {}', ', '.join(table_cols))
    terminal.append_to_history(
        '> tables: {}', ', '.join(account.database.list_tables()))
    terminal.append_to_history(
        '>> action menu is disabled: deleting & updating has to be done via terminal'
    )
    terminal.append_to_history(
        '>> listed records only update on valid select queries')
    terminal.append_to_history(
        '>> ctrl + (up|down|pgup|pgdown) can be used to scroll up & down the table'
    )
    terminal.append_to_history(
        '>> sample query: SELECT * FROM <table> ORDER BY datetime(datetime) DESC;'
    )
    terminal.reset_input_field()
    terminal.redraw()
    # start accepting input -----------------------------------------------------------
    kb_interrupt = False
    ec_interrupt = False
    while True:
        try:
            input_char = stdscr.get_wch()
            kb_interrupt = False
        except KeyboardInterrupt:
            if kb_interrupt or terminal.command == '':
                break
            kb_interrupt = True
            terminal.reset_input_field()
            terminal.append_to_history('press ctrl + c again to exit query mode')
            terminal.redraw()
            continue
        except:
            continue
        # escape = interrupt ----------------------------------------------------------
        if input_char == '\x1b':
            if ec_interrupt or terminal.command == '':
                break
            ec_interrupt = True
            terminal.reset_input_field()
            terminal.append_to_history('press escape again to exit query mode')
            terminal.redraw()
            continue
        # backspace, del --------------------------------------------------------------
        elif input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            terminal.delete_previous_char()
        elif input_char == curses.KEY_DC:
            terminal.delete_next_char()
        # submit ----------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            query = terminal.command.strip()
            if query == '':
                continue
            terminal.command_history.append(query)
            terminal.append_to_history('>>> ' + query)
            cursor = db_connection.cursor()
            try:
                cursor.execute(query)
            except sqlite3.Error as e:
                terminal.append_to_history(f'[sqlite error] {e}')
                terminal.reset_input_field()
                terminal.scroll = 0
                terminal.redraw()
                continue
            if f' {account.name}' not in query.lower():
                terminal.append_to_history( \
                '[warning] query does not target current account ({})'. \
                format(account.name))
            # SELECT command
            if re.match('^SELECT', query, re.IGNORECASE):
                db_items = cursor.fetchall()
                if len(db_items) == 0:
                    terminal.append_to_history('no results')
                else:
                    if len(db_items[0]) == 8:
                        custom_records = []
                        for (t_id, dt_str, amount_primary, amount_secondary,
                            category, subcategory, business, note) in db_items:
                            custom_records.append(
                                Record(
                                    datetime.strptime(
                                        dt_str,
                                        '%Y-%m-%d %H:%M:%S'
                                    ),
                                    account.currency_type(
                                        amount_primary,
                                        amount_secondary
                                    ),
                                    category, subcategory,
                                    business, note, t_id
                                )
                            )
                        terminal.windows[WinID.Main].refresh_table_records(
                            'custom sql query results', custom_records)
                    elif len(db_items[0]) < 8:
                        # try to parse the query
                        parse_success = False
                        match = re.match(r'SELECT ((?:(?:\w+\.)?\w+,?\s?)+) FROM',
                            query, re.IGNORECASE)
                        if match:
                            parsed_cols = [c.strip() 
                                for c in match.group(1).split(',')]
                            available_col_idx = []
                            parse_success = True
                            for col in parsed_cols:
                                if col not in table_map:
                                    parse_success = False
                                    break
                                available_col_idx.append(table_map[col])
                        if parse_success:
                            custom_records = []
                            for item in db_items:
                                # t_id, dt_str, amount_primary, amount_secondary,
                                # category, subcategory, business, note
                                record = [0, '1970-01-01 00:00:00', 0, 0] + [''] * 4
                                for i, c in enumerate(available_col_idx):
                                    record[c] = item[i]

                                custom_records.append(
                                    Record(
                                        datetime.strptime(
                                            record[1], '%Y-%m-%d %H:%M:%S'),
                                        account.currency_type(record[2], record[3]),
                                        record[4], record[5], record[6],
                                        record[7], record[0]
                                    )
                                )
                            terminal.windows[WinID.Main].refresh_table_records(
                                'custom sql query results', custom_records)
                        else:
                            terminal.append_to_history(
                                'unsupported select query, printing...')
                            for item in db_items:
                                item_list = [str(x) for x in item]
                                terminal.append_to_history(','.join(item_list))
                    else:
                        terminal.append_to_history(
                            'unexpected query response. investigate the code.')
            # other commands
            else:
                potential_table_update = True
                db_connection.commit()
            terminal.reset_input_field()
            terminal.scroll = 0
            terminal.redraw()
        # scrolling terminal ----------------------------------------------------------
        elif input_char == curses.KEY_PPAGE:
            terminal.scroll_page_up()
        elif input_char == curses.KEY_NPAGE:
            terminal.scroll_page_down()
        # scrolling table -------------------------------------------------------------
        elif input_char == KeyCombo.CTRL_UP:
            terminal.windows[WinID.Main].clist.move_selection_up()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_DOWN:
            terminal.windows[WinID.Main].clist.move_selection_down()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_PG_UP:
            terminal.windows[WinID.Main].clist.scroll_page_up()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_PG_DOWN:
            terminal.windows[WinID.Main].clist.scroll_page_down()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        # history surfing -------------------------------------------------------------
        elif input_char == curses.KEY_UP:
            terminal.command_history_up()
        elif input_char == curses.KEY_DOWN:
            terminal.command_history_down()
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
        # normal input ----------------------------------------------------------------
        elif input_char == '\t':
            # no suggestions in query mode yet
            continue
        else:
            terminal.insert_char(input_char)

    # restoring state, updating just to be safe
    if potential_table_update:
        account.query_transactions(account.full_query, True)
    terminal.windows[WinID.Main].refresh_table_records(org_table_label)
    terminal.windows[WinID.Main].disable_actions = False
    terminal.command_history = org_terminal_ch
    terminal.history_surf_index = org_terminal_hsi
    terminal.cmd_history_buffer = org_terminal_chb
    return ['query mode deactivated']