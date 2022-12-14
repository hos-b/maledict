import re
import curses
import sqlite3

from typing import Dict

from data.account import Account
from data.record import Record
from misc.statics import WinID, KeyCombo
from datetime import datetime


def sqlite(terminal, stdscr):
    # exception handling
    if terminal.windows[WinID.Main].account == None:
        return ["current account not set"]
    if stdscr is None:
        return ["cannot query in warmup mode"]

    account: Account = terminal.windows[WinID.Main].account
    db_connection = account.database.connection
    table_map: Dict[str, int] = account.database.table_map
    inv_table_map: Dict[int, str] = {v: k for k, v in table_map.items()}
    table_cols = [i[0] for i in sorted(table_map.items(), key = lambda x: x[1])]
    terminal.windows[WinID.Main].disable_actions = True
    potential_table_update = False
    query_history = []
    query_surf_index = 0
    query_history_buffer = ''
    old_table_label = terminal.windows[WinID.Main].table_label
    terminal.terminal_history.append("query mode activated")
    terminal.terminal_history.append(f"> column names: {', '.join(table_cols)}")
    terminal.terminal_history.append(
        f"> tables: {', '.join(account.database.list_tables())}")
    terminal.terminal_history.append(
        ">> action menu is disabled: deleting & updating has to be done via terminal"
    )
    terminal.terminal_history.append(
        ">> listed records only update on valid select queries")
    terminal.terminal_history.append(
        ">> ctrl + (up|down|pgup|pgdown) can be used to scroll up & down the table"
    )
    terminal.terminal_history.append(
        ">> sample query: SELECT * FROM <table> ORDER BY datetime(datetime) DESC;"
    )
    terminal.command = ''
    terminal.cursor_x = 0
    terminal.redraw()
    # start accepting input -----------------------------------------------------------
    kb_interrupt = False
    while True:
        try:
            input_char = stdscr.get_wch()
            kb_interrupt = False
        except KeyboardInterrupt:
            if kb_interrupt or terminal.command == '':
                break
            kb_interrupt = True
            terminal.command = ''
            terminal.cursor_x = 0
            terminal.terminal_history.append(
                'press ctrl + c again to exit query mode')
            terminal.redraw()
            continue
        except:
            continue
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            terminal.cursor_x = max(0, terminal.cursor_x - 1)
            if terminal.cursor_x == len(terminal.command) - 1:
                terminal.command = terminal.command[:terminal.cursor_x]
            else:
                terminal.command = terminal.command[:terminal.cursor_x] + \
                                terminal.command[terminal.cursor_x + 1:]
            terminal.redraw()
        elif input_char == curses.KEY_DC:
            if len(terminal.command) > 0 and terminal.cursor_x < len(
                    terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + \
                                terminal.command[terminal.cursor_x + 1:]
                terminal.redraw()
        # submit ----------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            query = terminal.command.strip()
            if query == '':
                continue
            query_history.append(query)
            terminal.terminal_history.append('>>> ' + query)
            cursor = db_connection.cursor()
            try:
                cursor.execute(query)
            except sqlite3.Exception as e:
                terminal.terminal_history.append(f'could not execute query: {e}')
                terminal.command = ''
                terminal.cursor_x = 0
                terminal.scroll = 0
                query_surf_index = 0
                terminal.redraw()
                continue
            if f' {account.name}' not in query:
                terminal.terminal_history.append( \
                'warning: query does not target current account ({})'. \
                format(account.name))
            # SELECT command
            if re.match('^SELECT', query, re.IGNORECASE):
                db_items = cursor.fetchall()
                if len(db_items) == 0:
                    terminal.terminal_history.append('no results')
                else:
                    if len(db_items[0]) == 8:
                        custom_records = []
                        for (t_id, dt_str, amount_primary, amount_secondary,
                            category, subcategory, business, note) in db_items:
                            custom_records.append(
                                Record(
                                    datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"),
                                    account.currency_type(amount_primary, amount_secondary),
                                    category, subcategory, business, note, t_id))
                        terminal.windows[WinID.Main].refresh_table_records(
                            'custom sql query results', custom_records)
                    elif len(db_items[0]) < 8:
                        # try to parse the query
                        parse_success = False
                        match = re.match(r'SELECT ((?:(?:\w+\.)?\w+,?\s?)+) FROM',
                            query, re.IGNORECASE)
                        if match:
                            parsed_cols = [c.strip() for c in match.group(1).split(',')]
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
                                record = [0, '1970-01-01 00:00:00', 0, 0, '', '', '', '']
                                for i, c in enumerate(available_col_idx):
                                    record[c] = item[i]

                                custom_records.append(
                                    Record(
                                        datetime.strptime(record[1], "%Y-%m-%d %H:%M:%S"),
                                        account.currency_type(record[2], record[3]),
                                        record[4], record[5], record[6], record[7], record[0]))
                            terminal.windows[WinID.Main].refresh_table_records(
                                'custom sql query results', custom_records)
                        else:
                            terminal.terminal_history.append(
                                'unsupported select query, printing...')
                            for item in db_items:
                                item_list = [str(x) for x in item]
                                terminal.terminal_history.append(','.join(item_list))
                    else:
                        terminal.terminal_history.append(
                            'unexpected query response. investigate the code.')
            # other commands
            else:
                potential_table_update = True
                db_connection.commit()
            terminal.command = ''
            terminal.cursor_x = 0
            terminal.scroll = 0
            query_surf_index = 0
            terminal.redraw()
        # scrolling terminal ----------------------------------------------------------
        elif input_char == curses.KEY_PPAGE:
            max_scroll = len(terminal.terminal_history) + 3 - terminal.w_height
            # if we can show more than history + 3 reserved lines:
            if max_scroll > 0:
                terminal.scroll = min(terminal.scroll + 1, max_scroll)
            terminal.redraw()
        elif input_char == curses.KEY_NPAGE:
            terminal.scroll = max(terminal.scroll - 1, 0)
            terminal.redraw()
        # scrolling table -------------------------------------------------------------
        elif input_char == KeyCombo.CTRL_PG_UP:
            terminal.windows[WinID.Main].clist.key_pgup()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_PG_DOWN:
            terminal.windows[WinID.Main].clist.key_pgdn()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_UP:
            terminal.windows[WinID.Main].clist.key_up()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_DOWN:
            terminal.windows[WinID.Main].clist.key_down()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        # history surfing -------------------------------------------------------------
        elif input_char == curses.KEY_UP:
            if len(query_history) != 0:
                terminal.scroll = 0
                # if we weren't surfing, save the current command in buffer
                if query_surf_index == 0:
                    query_history_buffer = terminal.command
                query_surf_index = min(query_surf_index + 1,
                                       len(query_history))
                terminal.command = query_history[-query_surf_index]
                terminal.cursor_x = len(terminal.command)
                terminal.redraw()
        elif input_char == curses.KEY_DOWN:
            if query_surf_index != 0:
                terminal.scroll = 0
                query_surf_index -= 1
                if query_surf_index == 0:
                    terminal.command = query_history_buffer
                    terminal.cursor_x = len(terminal.command)
                else:
                    terminal.command = query_history[-query_surf_index]
                    terminal.cursor_x = len(terminal.command)
                terminal.redraw()
        # cursor shift ----------------------------------------------------------------
        elif input_char == curses.KEY_LEFT:
            terminal.cursor_x = max(0, terminal.cursor_x - 1)
            terminal.redraw()
        elif input_char == curses.KEY_RIGHT:
            terminal.cursor_x = min(len(terminal.command),
                                    terminal.cursor_x + 1)
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_LEFT:
            cut_str = terminal.command[:terminal.cursor_x][::-1]
            while len(cut_str) != 0 and cut_str[0] == ' ':
                cut_str = cut_str[1:]
                terminal.cursor_x = max(0, terminal.cursor_x - 1)
            next_jump = cut_str.find(' ')
            if next_jump == -1:
                terminal.cursor_x = 0
            else:
                terminal.cursor_x = max(0, terminal.cursor_x - next_jump)
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
                terminal.cursor_x = min(terminal.cursor_x + next_jump,
                                        len(terminal.command))
                cut_str = terminal.command[terminal.cursor_x:]
            terminal.redraw()
        elif input_char == curses.KEY_HOME:
            terminal.cursor_x = 0
            terminal.redraw()
        elif input_char == curses.KEY_END:
            terminal.cursor_x = len(terminal.command)
            terminal.redraw()
        # normal input ----------------------------------------------------------------
        else:
            # some command that's not used
            if type(input_char) is int:
                terminal.terminal_history.append(
                    f'non standard input: {str(input_char)}')
                terminal.redraw()
                continue
            if input_char == ' ':
                # leading spaces don't count
                if len(terminal.command) == 0:
                    terminal.redraw()
                    continue
            if terminal.cursor_x == len(terminal.command):
                terminal.command = terminal.command[:terminal.
                                                    cursor_x] + input_char
            else:
                terminal.command = terminal.command[:terminal.cursor_x] + input_char \
                                 + terminal.command[terminal.cursor_x:]
            terminal.cursor_x += 1
            terminal.scroll = 0
            query_surf_index = 0
            terminal.redraw()

    # restoring state, updating just to be safe
    if potential_table_update:
        account.query_transactions(account.full_query, True)
    terminal.windows[WinID.Main].refresh_table_records(old_table_label)
    terminal.windows[WinID.Main].disable_actions = False
    return ["query mode deactivated"]