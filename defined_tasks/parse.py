import csv
import curses
from parser.mk_parser import MKParser
from parser.maledict_parser import MaledictParser
from misc.statics import WinID

def mkcsv(terminal, stdscr, file_path: str, translate_categories: str) -> list:
    """
    parses the given file and tranlsate the categories if requested.
    not that for the translation, the function takes control of the
    terminal until it's done. for this period, history surfing, tab
    completion and window switching is disabled.
    """
    # exception handling
    if terminal.windows[WinID.Main].account == None:
        return ['current account not set']
    if stdscr is None:
        return ['cannot parse mkcsv in warmup mode']

    # tanslate categories ?
    translate_mode = False
    translate_categories = translate_categories.lower()
    if translate_categories in ['1', 'y', 'true', 'yes', 'ye', 't', 'yy', 'fuck']:
        translate_mode = True
    elif translate_categories in ['0', 'n', 'false', 'no', 'f', 'ff']:
        translate_mode = False
    else:
        return [f'expected boolean, got {translate_categories}']

    # start parsing
    parser = MKParser()
    msg_list = []
    try:
        with open(file_path, newline='\n') as csvfile:
            datareader = csv.reader(csvfile, delimiter=';')
            line_number = 0
            for row in datareader:
                line_number += 1
                if line_number < 12:
                    continue
                success, msg = parser.parse_row(row)
                if not success:
                    msg_list.append(f'line {line_number}: {msg}')
    except FileNotFoundError:
        return [f'could not find {file_path}']
    except:
        return [f'error while reading {file_path}']
    msg_list.append(f'parsed {len(parser.records)} records, skipped {len(msg_list)}')

    if len(parser.categories) == 0:
        return ['the .csv file has no categories to translate']
    if len(parser.subcategories) == 0:
        return ['the .csv file has no subcategories to translate']

    if translate_mode:
        cats = list(parser.categories.keys())
        subcats = list(parser.subcategories.keys())
        terminal.terminal_history.append(f'enter replacement for category {cats[0]}:')
        terminal.cursor_x = 0
        terminal.command = ''
        terminal.redraw()

    read_input = translate_mode
    while read_input:
        input_char = stdscr.get_wch()
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            if len(terminal.command) != 0:
                terminal.cursor_x = max(0, terminal.cursor_x - 1)
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
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            if terminal.command != '':
                terminal.terminal_history.append('>>> ' + terminal.command)
                if len(cats) > 0:
                    if ';' in terminal.command > 0:
                        terminal.terminal_history.append('nope')
                    else:
                        parser.categories[cats[0]] = terminal.command
                        cats.pop(0)
                    if len(cats) > 0:
                        terminal.terminal_history.append(f'enter replacement '
                                                         f'for category {cats[0]}:')
                    else:
                        terminal.terminal_history.append(f'enter replacement '
                                                         f'for subcategory {subcats[0]}:')
                elif len(cats) == 0 and len(subcats) > 0:
                    if ';' in terminal.command > 0:
                        terminal.terminal_history.append('nope')
                    else:
                        parser.subcategories[subcats[0]] = terminal.command
                        subcats.pop(0)
                    if len(subcats) > 0:
                        terminal.terminal_history.append(f'enter replacement '
                                                         f'for subcategory {subcats[0]}:')
                    else:
                        read_input = False
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
        else:
            if input_char == ' ':
                # leading spaces don't count
                if len(terminal.command) == 0:
                    continue
            if terminal.cursor_x == len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + input_char
            else:
                terminal.command = terminal.command[:terminal.cursor_x] + input_char \
                                 + terminal.command[terminal.cursor_x:]
            terminal.cursor_x += 1
            terminal.cmd_history_index = 0
            terminal.scroll = 0
            terminal.redraw()

    terminal.windows[WinID.Main].account.commit_parser(parser, translate_mode)
    terminal.windows[WinID.Main].refresh_table_records('all')
    return msg_list

def maledict(terminal, stdscr, file_path: str, translate_categories: str) -> list:
    """
    parses the given file and tranlsate the categories if requested.
    not that for the translation, the function takes control of the
    terminal until it's done. for this period, history surfing, tab
    completion and window switching is disabled.
    """
    # exception handling
    if terminal.windows[WinID.Main].account == None:
        return ['current account not set']
    if stdscr is None:
        return ['cannot parse mkcsv in warmup mode']

    # tanslate categories ?
    translate_mode = False
    translate_categories = translate_categories.lower()
    if translate_categories in ['1', 'y', 'true', 'yes', 'ye', 't', 'yy', 'fuck']:
        translate_mode = True
    elif translate_categories in ['0', 'n', 'false', 'no', 'f', 'ff']:
        translate_mode = False
    else:
        return [f'expected boolean, got {translate_categories}']

    # start parsing
    parser = MaledictParser()
    msg_list = []
    try:
        with open(file_path, newline='\n') as csvfile:
            datareader = csv.reader(csvfile, delimiter=',')
            line_number = 0
            for row in datareader:
                line_number += 1
                success, msg = parser.parse_row(row)
                if not success:
                    msg_list.append(f'line {line_number}: {msg}')
    except FileNotFoundError:
        return [f'could not find {file_path}']
    except:
        return [f'error while reading {file_path}']
    msg_list.append(f'parsed {len(parser.records)} records, skipped {len(msg_list)}')

    if len(parser.categories) == 0:
        return ['the .csv file has no categories to translate']
    if len(parser.subcategories) == 0:
        return ['the .csv file has no subcategories to translate']

    if translate_mode:
        cats = list(parser.categories.keys())
        subcats = list(parser.subcategories.keys())
        terminal.terminal_history.append(f'enter replacement for category {cats[0]}:')
        terminal.cursor_x = 0
        terminal.command = ''
        terminal.redraw()

    read_input = translate_mode
    while read_input:
        input_char = stdscr.get_wch()
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            if len(terminal.command) != 0:
                terminal.cursor_x = max(0, terminal.cursor_x - 1)
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
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            if terminal.command != '':
                terminal.terminal_history.append('>>> ' + terminal.command)
                if len(cats) > 0:
                    if ';' in terminal.command > 0:
                        terminal.terminal_history.append('nope')
                    else:
                        parser.categories[cats[0]] = terminal.command
                        cats.pop(0)
                    if len(cats) > 0:
                        terminal.terminal_history.append(f'enter replacement '
                                                         f'for category {cats[0]}:')
                    else:
                        terminal.terminal_history.append(f'enter replacement '
                                                         f'for subcategory {subcats[0]}:')
                elif len(cats) == 0 and len(subcats) > 0:
                    if ';' in terminal.command > 0:
                        terminal.terminal_history.append('nope')
                    else:
                        parser.subcategories[subcats[0]] = terminal.command
                        subcats.pop(0)
                    if len(subcats) > 0:
                        terminal.terminal_history.append(f'enter replacement '
                                                         f'for subcategory {subcats[0]}:')
                    else:
                        read_input = False
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
        else:
            if input_char == ' ':
                # leading spaces don't count
                if len(terminal.command) == 0:
                    continue
            if terminal.cursor_x == len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + input_char
            else:
                terminal.command = terminal.command[:terminal.cursor_x] + input_char \
                                 + terminal.command[terminal.cursor_x:]
            terminal.cursor_x += 1
            terminal.cmd_history_index = 0
            terminal.scroll = 0
            terminal.redraw()

    terminal.windows[WinID.Main].account.commit_parser(parser, translate_mode)
    terminal.windows[WinID.Main].refresh_table_records('all')
    return msg_list