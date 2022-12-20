import re
import os
import yaml
import time
import curses

from typing import Union, List

import defined_tasks

from data.sqlite_proxy import SQLiteProxy
from misc.statics import WinID, KeyCombo
from ui.base import CursesWindow

class TerminalWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height, \
                 windows: list, database: SQLiteProxy, conf: dict):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)

        # good stuff
        self.vscroll = 0
        self.cursor_x = 0
        self.windows = windows
        self.database = database
        self.conf = conf

        # prediction stuff
        self.shadow_string = ''
        self.shadow_index = 0
        self.last_tab_press = time.time()

        # pending actions
        self.pending_action = None
        self.pending_tr_id = None

        # history stuff
        self.command = ''
        # alphanumeric + dot
        self.cmd_regex = re.compile('[\w\.]+')
        self.print_history = []
        self.command_history = []
        self.history_surf_index = 0
        self.cmd_history_buffer = ''

        # revere video text
        self.reverse_text_enable = False
        self.rtext_start = 0
        self.rtext_end = 0

        # loading command yaml file
        cmd_yaml_path = os.path.join(os.path.dirname(__file__),
                                     '../config/commands.yaml')
        with open(cmd_yaml_path) as file:
            self.command_dict = yaml.load(file, Loader=yaml.FullLoader)
        try:
            cmd_history_path = os.path.join(os.path.dirname(__file__),
                                            '../database/.command_history')
            f = open(cmd_history_path, 'r')
            for line in f:
                self.command_history.append(line.strip())
        except FileNotFoundError:
            self.append_to_history('could not open command history file')
        if self.conf['warm-up']:
            self.warmup()
        self.redraw()

    def redraw(self):
        """
        redraws the window based on input, focus flag and predictions.
        """
        self.cwindow.erase()
        # not using first or last line, 1 reserved for current command
        visible_history = min(len(self.print_history), self.w_height - 3)
        visible_history += self.vscroll
        # disable cursor if scrolling
        curses.curs_set(int(self.vscroll == 0 and self.focused and 
            not self.reverse_text_enable))
        curses_attr = curses.A_NORMAL if self.focused else curses.A_DIM
        for i in range (self.w_height - 2):
            if visible_history == 0:
                self.cwindow.addstr(i + 1, 2, '>>> ', curses_attr)
                if self.shadow_string != '':
                    self.cwindow.addstr(i + 1, 6 + self.shadow_index, 
                        self.shadow_string, curses.A_DIM)
                if self.reverse_text_enable:
                    pre = self.command[:self.rtext_start]
                    mid = self.command[self.rtext_start:self.rtext_end]
                    pos = self.command[self.rtext_end:]
                    self.cwindow.addstr(i + 1, 6, pre, curses_attr)
                    self.cwindow.addstr(i + 1, 6 + len(pre), mid,
                        curses_attr | curses.A_STANDOUT)
                    self.cwindow.addstr(i + 1, 6 + len(pre) + len(mid),
                        pos, curses_attr)
                else:
                    self.cwindow.addstr(i + 1, 6, self.command, curses_attr)
                self.cwindow.move(i + 1, self.cursor_x + 6)
                break
            self.cwindow.addstr(i + 1, 2, self.print_history[-visible_history],
                curses_attr)
            visible_history -= 1
        self.cwindow.box()
        self.cwindow.refresh()

    def parse_and_execute(self, stdscr) -> List[str]:
        """
        parses and executes the task currently written in the terminal.
        it returns a string per terminal output line (list of str). all
        exception handling regarding the correctly entered commands are
        to be done inside their individual files, not here.
        """
        # start with full command & retain only the final args
        cmd_args = self.cmd_regex.findall(self.command)
        parsed = ''
        current_lvl = self.command_dict
        task_id = -1
        # looking for all commands?
        if len(cmd_args) == 1 and re.match(r'(help|\?)', cmd_args[0]):
            return ['available commands: ' + ', '.join(self.command_dict.keys())]
        # parsing the command
        while len(cmd_args) != 0:
            parsed += cmd_args[0] + ' '
            if cmd_args[0] not in current_lvl:
                return [f'unknown command: {parsed}']
            # go one level deeper
            current_lvl = current_lvl[cmd_args[0]]
            cmd_args.pop(0)
            # if at leaf node
            if 'task-id' in current_lvl:
                task_id = current_lvl['task-id']
                break
            # offer help at current level
            elif len(cmd_args) == 0 or re.match(r'^(help|\?)$', cmd_args[0]):
                return ['available commands: ' + ', '.join(current_lvl.keys())]

        # looking for help at last level?
        if len(cmd_args) == 1 and re.match(r'^(help|\?|--help|-h)$', cmd_args[0]):
            return [current_lvl['desc'] + f", args: {current_lvl['args']}"]
        # wrong number of args
        elif len(cmd_args) != len(current_lvl['args']):
            args = [f'[{key}: {value}]' for key, value in current_lvl['args'].items()]
            return [f"invalid number of args ({len(cmd_args)}): {', '.join(args)}"]
        # actually doing the task
        if task_id == 101:
            return defined_tasks.add.account(self.database, *cmd_args)
        elif task_id == 102:
            return defined_tasks.add.expense(self, stdscr)
        elif task_id == 201:
            return defined_tasks.list.accounts(self.database)
        elif task_id == 301:
            return defined_tasks.set.account(self, *cmd_args)
        elif task_id == 401:
            return defined_tasks.parse.mkcsv(self, stdscr, *cmd_args)
        elif task_id == 402:
            return defined_tasks.parse.maledict(self, stdscr, *cmd_args)
        elif task_id == 501:
            return defined_tasks.delete.account(self, *cmd_args)
        elif task_id == 502:
            return defined_tasks.delete.expense(self.windows[WinID.Main], *cmd_args)
        elif 600 <= task_id < 700:
            return defined_tasks.show.records(task_id, current_lvl['sql-query'], cmd_args, self.windows[WinID.Main])
        elif task_id == 701:
            return defined_tasks.export.csv(self.windows[WinID.Main].account, *cmd_args)
        elif task_id == 801:
            return defined_tasks.edit.expense(self, stdscr, *cmd_args)
        elif task_id == 901:
            return defined_tasks.query.sqlite(self, stdscr)
        elif task_id == 100001:
            self.database.connection.commit()
            self.database.db_close()
            self.write_command_history(self.conf['command_history_file_length'])
            exit()
        elif task_id == 100002:
            self.print_history.clear()
            self.vscroll = 0
            return []
        else:
            return ["don't know how to do this task yet"]

    def loop(self, stdscr) -> str:
        """
        main loop for capturing input and updating the window.
        """
        # take care of pending commands & return focus
        if self.submit_pending_command(stdscr):
            return curses.KEY_F1
        kb_interrupt = False
        while True:
            try:
                input_char = stdscr.get_wch()
                kb_interrupt = False
            except KeyboardInterrupt:
                if kb_interrupt or self.command == '':
                    return curses.KEY_F50
                self.reset_input_field()
                self.history_surf_index = 0
                self.vscroll = 0
                kb_interrupt = True
                self.append_to_history('press ctrl-c again to exit maledict')
                self.redraw()
                continue
            except:
                continue
            # if should switch window
            if CursesWindow.is_exit_sequence(input_char):
                return input_char
            # backspace, del --------------------------------------------------------------
            elif input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
                self.delete_previous_char()
            elif input_char == curses.KEY_DC:
                self.delete_next_char()
            # execute ---------------------------------------------------------------------
            elif input_char == curses.KEY_ENTER or input_char == '\n':
                if self.command != '':
                    self.command_history.append(self.command)
                    self.command_history = self.command_history \
                                         [-self.conf['command_history_buffer_length']:]
                    self.append_to_history('>>> {}', self.command)
                    self.append_to_history(self.parse_and_execute(stdscr))
                self.history_surf_index = 0
                self.vscroll = 0
                self.reset_input_field()
                self.redraw()
            # scrolling -------------------------------------------------------------------
            elif input_char == KeyCombo.CTRL_UP:
                self.scroll(+1)
            elif input_char == KeyCombo.CTRL_DOWN:
                self.scroll(-1)
            elif input_char == curses.KEY_PPAGE:
                self.scroll_page_up()
            elif input_char == curses.KEY_NPAGE:
                self.scroll_page_down()
            # cursor shift ----------------------------------------------------------------
            elif input_char == curses.KEY_LEFT:
                self.cursor_move_left()
            elif input_char == curses.KEY_RIGHT:
                self.cursor_move_right()
            elif input_char == KeyCombo.CTRL_LEFT:
                self.cursor_jump_left()
            elif input_char == KeyCombo.CTRL_RIGHT:
                self.cursor_jump_right()
            elif input_char == curses.KEY_HOME:
                self.cursor_jump_start()
            elif input_char == curses.KEY_END:
                self.cursor_jump_end()
            # history surfing -------------------------------------------------------------
            elif input_char == curses.KEY_UP:
                self.command_history_up()
            elif input_char == curses.KEY_DOWN:
                self.command_history_down()
            # do predictions --------------------------------------------------------------
            elif input_char == '\t':
                p_candidates, p_offset = self.get_command_predictions()
                # nothing to predict
                if len(p_candidates) == 0:
                    continue
                # complete the command at the current level
                if len(p_candidates) == 1:
                    self.command += p_candidates[0] if p_candidates[0] == ' ' \
                        else p_candidates[0][p_offset:] + ' '
                    self.cursor_x = len(self.command)
                    self.redraw()
                # check double tab
                elif (time.time() - self.last_tab_press) < 0.3:
                    self.append_to_history('>>> {}', self.command)
                    self.append_to_history(' | '.join(p_candidates))
                    self.redraw()
                self.last_tab_press = time.time()
            # normal input ----------------------------------------------------------------
            else:
                self.insert_char(input_char)

    def get_command_predictions(self) -> List[str]:
        """
        provides a list of predictions based on the current command
        and the index at which the prediction should be inserted.
        the state indicates the stage in expense mode.
        """
        current_cmd = self.command[:self.cursor_x]
        cmd_args = self.cmd_regex.findall(current_cmd)
        pred_candidates = []
        current_lvl = self.command_dict
        pred_offset = 0
        # parsing the command
        while len(cmd_args) != 0:
            # go one level deeper, if the segment is complete and correct
            if cmd_args[0] in current_lvl:
                # too deep, no predictions
                if 'task-id' in current_lvl[cmd_args[0]]:
                    break
                current_lvl = current_lvl[cmd_args[0]]
                if len(cmd_args) == 1:
                    # predict space if missing
                    if not current_cmd.endswith(' '):
                        pred_candidates.append(' ')
                    # predict possible continuations
                    else:
                        pred_candidates += list(current_lvl.keys())
                cmd_args.pop(0)
            else:
                pred_offset = len(cmd_args[0])
                for candidate in current_lvl.keys():
                    if candidate.startswith(cmd_args[0]):
                        pred_candidates.append(candidate)
                break
        pred_candidates.sort(key=len)
        return pred_candidates, pred_offset

    def write_command_history(self, count = 20):
        """
        write last x commands to ./database/.command_history
        """
        end = len(self.command_history)
        begin = max(0, end - count)
        cmd_history_path = os.path.join(os.path.dirname(__file__),
                                        '../database/.command_history')
        with open(cmd_history_path, 'w') as f:
            for i in range(begin, end):
                f.write(f'{self.command_history[i]}\n')

    def warmup(self):
        """
        loads a text file in ./database/.maledictrc and executes all
        the commands inside.
        """
        commands_to_run = []
        try:
            warmup_path = os.path.join(os.path.dirname(__file__),
                                       '../database/.maledictrc')
            f = open(warmup_path, 'r')
            for line in f:
                line = line.strip()
                if line != '':
                    commands_to_run.append(line)
        except FileNotFoundError:
            self.append_to_history('could not find warmup file')
        except Exception:
            self.append_to_history('could not open warmup file')

        for cmd in commands_to_run:
            try:
                self.command = cmd
                self.append_to_history(self.parse_and_execute(None))
                self.command = ''
            except Exception as e:
                self.append_to_history(f'could not run warmup commands `{cmd}`: {e}')
                self.command = ''
                break

    def submit_pending_command(self, stdscr) -> bool:
        """
        pending commands set by the action window are performed here.
        returns True if the focus should afterwards be given to the
        main window (and not remain on the terminal).
        """
        if self.pending_action:
            # edit action
            if self.pending_action == 'EDIT':
                self.append_to_history(
                    defined_tasks.edit.expense(self, stdscr,
                                               hex(self.pending_tr_id)))
            # delete action
            elif self.pending_action == 'DELETE':
                self.append_to_history(
                    defined_tasks.delete.expense(self.windows[WinID.Main],
                                                 hex(self.pending_tr_id)))
            elif self.pending_action.startswith('FIND SIMILAR'):
                query_pre = 'SELECT g2.* FROM {} g1, {} g2 WHERE g1.transaction_id = {}'
                query_cond = ''
                query_post = 'ORDER BY datetime(g2.datetime) DESC;'
                if self.pending_action.endswith('(AMOUNT)'):
                    query_cond = ' AND g2.amount_primary = g1.amount_primary' \
                                 ' AND g2.amount_secondary = g1.amount_secondary '
                elif self.pending_action.endswith('(BUSINESS)'):
                    query_cond = ' AND g2.business = g1.business '
                elif self.pending_action.endswith('(CATEGORY)'):
                    query_cond = ' AND g2.category = g1.category' \
                                 ' AND g2.subcategory = g1.subcategory '
                sql_query = query_pre + query_cond + query_post
                self.append_to_history(
                    defined_tasks.show.records(666, sql_query, [self.pending_tr_id],
                                               self.windows[WinID.Main]))
            # reset
            self.history_surf_index = 0
            self.vscroll = 0
            self.pending_action = None
            self.pending_tr_id = None
            self.redraw()
            return True
        return False

    def reset_input_field(self):
        """
        clears the command line and resets the cursor.
        """
        self.command = ''
        self.cursor_x = 0

    def append_to_history(self, strings: Union[str, list], *args):
        """
        appends the given string to the terminal history.
        it also accepts an arg list for string formatting.
        if the argument is a list, all elements are appended.
        """
        if isinstance(strings, str):
            self.print_history.append(strings.format(*args))
        elif isinstance(strings, list):
            self.print_history += strings

    def scroll(self, up_down: int, reserved_lines = 3):
        """
        scrolls print history up or down by a number.
        """
        if up_down == +1:
            # if we can show more than history + 3 reserved lines:
            max_scroll = len(self.print_history) + \
                reserved_lines - self.w_height
            if max_scroll > 0:
                self.vscroll = min(self.vscroll + 1, max_scroll)
        elif up_down == -1:
            self.vscroll = max(self.vscroll - 1, 0)
        else:
            raise NotImplementedError('nah')
        self.redraw()
            
    def scroll_page_up(self, reserved_lines = 3):
        """
        goes one page up in the print history
        """
        # if we can show more than history + 3 reserved lines:
        max_scroll = len(self.print_history) + \
            reserved_lines - self.w_height
        if max_scroll > 0:
            self.vscroll = min(self.vscroll + 1, max_scroll)
        self.redraw()

    def scroll_page_down(self):
        """
        goes one page down in the print history
        """
        self.vscroll = max(self.vscroll - 1, 0)
        self.redraw()

    def cursor_move_left(self, start_offset: int = 0):
        """
        self explanatory
        """
        self.cursor_x = max(start_offset, self.cursor_x - 1)
        self.redraw()

    def cursor_move_right(self):
        """
        self explanatory
        """
        self.cursor_x = min(len(self.command), self.cursor_x + 1)
        self.redraw()

    def cursor_jump_left(self, start_offset: int = 0):
        """
        moves the cursor to the beginning of current word.
        """
        cut_str = self.command[:self.cursor_x][::-1]
        while len(cut_str) != 0 and cut_str[0] == ' ':
            cut_str = cut_str[1:]
            self.cursor_x = max(start_offset, self.cursor_x - 1)
        next_jump = cut_str.find(' ')
        if next_jump == -1:
            self.cursor_x = start_offset
        else:
            self.cursor_x = max(start_offset, self.cursor_x - next_jump)
        self.redraw()

    def cursor_jump_right(self):
        """
        moves the cursor to the end of the current word.
        """
        cut_str = self.command[self.cursor_x:]
        while len(cut_str) != 0 and cut_str[0] == ' ':
            cut_str = cut_str[1:]
            self.cursor_x = min(self.cursor_x + 1, len(self.command))
        next_jump = cut_str.find(' ')
        if next_jump == -1:
            self.cursor_x = len(self.command)
        else:
            self.cursor_x = min(self.cursor_x + next_jump, len(self.command))
        self.redraw()

    def cursor_jump_start(self, start_offset: int = 0):
        """
        moves cursor to the beginning of the line.
        """
        self.cursor_x = start_offset
        self.redraw()

    def cursor_jump_end(self):
        """
        moves cursor to the end of the line.
        """
        self.cursor_x = len(self.command)
        self.redraw()

    def command_history_up(self):
        """
        goes to the previous item in the command history.
        """
        if len(self.command_history) == 0:
            return
        self.vscroll = 0
        # if we weren't surfing, save the current command in buffer
        if self.history_surf_index == 0:
            self.cmd_history_buffer = self.command
        self.history_surf_index = min(self.history_surf_index + 1,
                                        len(self.command_history))
        self.command = self.command_history[-self.history_surf_index]
        self.cursor_x = len(self.command)
        self.redraw()

    def command_history_down(self):
        """
        goes to the next item in the command history.
        """
        if self.history_surf_index == 0:
            return
        self.vscroll = 0
        self.history_surf_index -= 1
        if self.history_surf_index == 0:
            self.command = self.cmd_history_buffer
            self.cursor_x = len(self.command)
        else:
            self.command = self.command_history[-self.history_surf_index]
            self.cursor_x = len(self.command)
        self.redraw()

    def delete_previous_char(self, start_offset: int = 0, redraw: bool = True):
        """
        backspace key implementation
        """
        if len(self.command) == 0:
            return
        self.cursor_x = max(start_offset, self.cursor_x - 1)
        if self.cursor_x == len(self.command) - 1:
            self.command = self.command[:self.cursor_x]
        else:
            self.command = self.command[:self.cursor_x] + \
                            self.command[self.cursor_x + 1:]
        if redraw:
            self.redraw()

    def delete_next_char(self, redraw: bool = True):
        """
        delete key implementation.
        """
        if len(self.command) == 0 or self.cursor_x == len(self.command):
            return
        self.command = self.command[:self.cursor_x] + \
                        self.command[self.cursor_x + 1:]
        if redraw:
            self.redraw()
    
    def insert_char(self, input_char, redraw: bool = True):
        """
        appends a character at the current cursor location
        given its code.
        """
        # ignore unused key combinations
        if type(input_char) is int:
            return
        # ignore leading spaces
        if input_char == ' ' and len(self.command) == 0:
            return
        if self.cursor_x == len(self.command):
            self.command = self.command[:self.cursor_x] + input_char
        else:
            self.command = self.command[:self.cursor_x] + input_char + \
                            self.command[self.cursor_x:]
        self.cursor_x += 1
        self.history_surf_index = 0
        self.vscroll = 0
        if redraw:
            self.redraw()