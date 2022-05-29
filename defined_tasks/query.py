import curses

from data.account import Account
from data.record import Record
import misc.statics as statics
from datetime import datetime


def sqlite(terminal, stdscr):
    # exception handling
    if terminal.windows[statics.WMAIN].account == None:
        return ["current account not set"]
    if stdscr is None:
        return ["cannot query in warmup mode"]

    account: Account = terminal.windows[statics.WMAIN].account
    db_connection = account.database.connection
    terminal.windows[statics.WMAIN].disable_actions = True
    potential_table_update = False
    query_mode = True
    query_history = []
    query_surf_index = 0
    query_history_buffer = ''
    showing_bak = terminal.windows[statics.WMAIN].table_label
    terminal.terminal_history.append("query mode activated")
    terminal.terminal_history.append(
        "> column names: transaction_id(primary key), datetime, "
        "amount, category, subcategory, business, note")
    terminal.terminal_history.append(
        f"> tables: {account.database.list_tables()}")
    terminal.terminal_history.append(
        ">> action menu is disabled: deleting & updating has to be done via terminal"
    )
    terminal.terminal_history.append(
        ">> listed records only update on valid select queries")
    terminal.terminal_history.append(
        ">> ctrl + (up|down|pgup|pgdown) can be used to scroll up & down the table"
    )
    terminal.terminal_history.append(
        ">> sample query: SELECT * FROM table ORDER BY datetime(datetime) DESC;"
    )
    terminal.command = ''
    terminal.cursor_x = 0
    terminal.redraw()
    # start accepting input -----------------------------------------------------------
    kb_interrupt = False
    while query_mode:
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
            if query[-1] != ';' or query.count(';') > 1:
                terminal.terminal_history.append(
                    'no semicolons! (or too many)')
                terminal.command = ''
                terminal.cursor_x = 0
                terminal.scroll = 0
                query_surf_index = 0
                terminal.redraw()
                continue
            cursor = db_connection.cursor()
            try:
                cursor.execute(query)
            except:
                terminal.terminal_history.append('could not execute query')
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
            if query.lower().startswith('select '):
                db_items = cursor.fetchall()
                custom_records = []
                if len(db_items) > 0 and len(db_items[0]) == 7:
                    for (t_id, dt_str, amount_primary, amount_secondary,
                         category, subcategory, business, note) in db_items:
                        custom_records.append(
                            Record(
                                datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"),
                                account.currency_type(amount_primary,
                                                      amount_secondary),
                                category, subcategory, business, note, t_id))
                    terminal.windows[statics.WMAIN].refresh_table_records( \
                        'custom sql query results', custom_records)
                elif len(db_items) > 0 and len(db_items[0]) < 7:
                    terminal.terminal_history.append(
                        'unsupported select query, printing...')
                    for item in db_items:
                        item_list = [str(x) for x in item]
                        terminal.terminal_history.append(','.join(item_list))
                elif len(db_items) == 0:
                    terminal.terminal_history.append('no results')
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
        elif input_char == statics.CTRL_PG_UP:
            terminal.windows[statics.WMAIN].clist.key_pgup()
            terminal.windows[statics.WMAIN].redraw()
            terminal.redraw()
        elif input_char == statics.CTRL_PG_DOWN:
            terminal.windows[statics.WMAIN].clist.key_pgdn()
            terminal.windows[statics.WMAIN].redraw()
            terminal.redraw()
        elif input_char == statics.CTRL_UP:
            terminal.windows[statics.WMAIN].clist.key_up()
            terminal.windows[statics.WMAIN].redraw()
            terminal.redraw()
        elif input_char == statics.CTRL_DOWN:
            terminal.windows[statics.WMAIN].clist.key_down()
            terminal.windows[statics.WMAIN].redraw()
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
        elif input_char == statics.CTRL_LEFT:
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
        elif input_char == statics.CTRL_RIGHT:
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
    terminal.windows[statics.WMAIN].refresh_table_records(showing_bak)
    terminal.windows[statics.WMAIN].disable_actions = False
    return ["query mode deactivated"]