import os
import yaml
import curses
from typing import Tuple

import defined_tasks
import misc.statics as statics
from ui.base import CursesWindow
from data.sqlite_proxy import SQLiteProxy
from misc.string_manip import variadic_equals_or
import time
#pylint: disable=E1101

class TerminalWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height, \
                 windows: list, database: SQLiteProxy, conf: dict):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)

        # good stuff
        self.scroll = 0
        self.cursor_x = 0
        self.windows = windows
        self.database = database
        self.conf = conf

        # prediction stuff
        self.shadow_string = ''
        self.shadow_index = 0
        self.last_tab_press = time.time()

        # pending actions
        self.pending_action = -1
        self.pending_tr_id = -1

        # history stuff
        self.command = ''
        self.terminal_history = []
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
            self.terminal_history.append("could not open command history file")
        if self.conf['warm-up']:
            self.warmup()
        self.redraw()

    def redraw(self):
        """
        redraws the window based on input, focus flag and predictions.
        """
        self.cwindow.erase()
        # not using first or last line, 1 reserved for current command
        visible_history = min(len(self.terminal_history), self.w_height - 3)
        visible_history += self.scroll
        # disable cursor if scrolling
        curses.curs_set(int(self.scroll == 0 and self.focused and not self.reverse_text_enable))

        curses_attr = curses.A_NORMAL if self.focused else curses.A_DIM
        for i in range (self.w_height - 2):
            if visible_history == 0:
                self.cwindow.addstr(i + 1, 2, ">>> ", curses_attr)
                if self.shadow_string != '':
                    self.cwindow.addstr(i + 1, 6 + self.shadow_index, self.shadow_string, curses.A_DIM)
                if self.reverse_text_enable:
                    pre = self.command[:self.rtext_start]
                    mid = self.command[self.rtext_start:self.rtext_end]
                    pos = self.command[self.rtext_end:]
                    self.cwindow.addstr(i + 1, 6, pre, curses_attr)
                    self.cwindow.addstr(i + 1, 6 + len(pre), mid, curses_attr | curses.A_STANDOUT)
                    self.cwindow.addstr(i + 1, 6 + len(pre) + len(mid), pos, curses_attr)
                else:
                    self.cwindow.addstr(i + 1, 6, self.command, curses_attr)
                self.cwindow.move(i + 1, self.cursor_x + 6)
                break
            self.cwindow.addstr(i + 1, 2, self.terminal_history[-visible_history], curses_attr)
            visible_history -= 1
        self.cwindow.box()
        self.cwindow.refresh()

    def parse_and_execute(self, stdscr) -> list:
        """
        parses and executes the task currently written in the terminal.
        it returns a string per terminal output line (list of str). all
        exception handling regarding the correctly entered commands are
        to be done inside their individual files, not here.
        """
        cmd_parts = self.command.strip().split(' ')
        parsed = ''
        current_lvl = self.command_dict
        task_id = -1
        # looking for all commands?
        if len(cmd_parts) == 1 and \
            variadic_equals_or(cmd_parts[0], 'help', '?'):
            return ['available commands: ' + ', '.join(self.command_dict.keys())]
        # parsing the command
        while len(cmd_parts) != 0:
            parsed += cmd_parts[0] + ' '
            if cmd_parts[0] not in current_lvl:
                return [f"unknown command: {parsed}"]
            # go one level deeper
            current_lvl = current_lvl[cmd_parts[0]]
            cmd_parts.pop(0)
            # if at leaf node
            if 'task-id' in current_lvl:
                task_id = current_lvl['task-id']
                break
            # offer help at current level
            elif len(cmd_parts) == 0 or \
                variadic_equals_or(cmd_parts[0], 'help', '?'):
                return ['available commands: ' + ', '.join(current_lvl.keys())]

        # looking for help at last level?
        if len(cmd_parts) == 1 and \
            variadic_equals_or(cmd_parts[0], 'help', '-h', '--help', '?'):
            return [current_lvl['desc'] + f", args: {current_lvl['args']}"]
        # wrong number of args
        elif len(cmd_parts) != len(current_lvl['args']):
            args = args = [f'[{key}: {value}]' for key, value in current_lvl['args'].items()]
            return [f"invalid number of args: {', '.join(args)}"]
        # actually doing the task
        if task_id == 101:
            return defined_tasks.add.account(self.database, cmd_parts[0], cmd_parts[1])
        elif task_id == 102:
            return defined_tasks.add.expense(self, stdscr)
        elif task_id == 201:
            return defined_tasks.list.accounts(self.database)
        elif task_id == 301:
            return defined_tasks.set.account(self, cmd_parts[0])
        elif task_id == 401:
            return defined_tasks.parse.mkcsv(self, stdscr, cmd_parts[0], cmd_parts[1])
        elif task_id == 402:
            return defined_tasks.parse.maledict(self, stdscr, cmd_parts[0], cmd_parts[1])
        elif task_id == 501:
            return defined_tasks.delete.account(self, cmd_parts[0])
        elif task_id == 502:
            return defined_tasks.delete.expense(self.windows[statics.WMAIN], cmd_parts[0])
        elif 600<= task_id < 700:
            return defined_tasks.show.records(task_id, current_lvl['sql-query'], cmd_parts, self.windows[statics.WMAIN])
        elif task_id == 701:
            return defined_tasks.export.csv(self.windows[0].account, cmd_parts[0])
        elif task_id == 801:
            return defined_tasks.edit.expense(self, stdscr, cmd_parts[0])
        elif task_id == 901:
            return defined_tasks.query.sqlite(self, stdscr)
        elif task_id == 100001:
            self.database.connection.commit()
            self.database.db_close()
            self.write_command_history(self.conf['command_history_file_length'])
            exit()
        elif task_id == 100002:
            self.terminal_history.clear()
            self.scroll = 0
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
                self.command = ''
                self.cursor_x = 0
                self.history_surf_index = 0
                self.scroll = 0
                kb_interrupt = True
                self.terminal_history.append('press ctrl-c again to exit maledict')
                self.redraw()
                continue
            except:
                continue
            # if should switch window
            if CursesWindow.is_exit_sequence(input_char):
                return input_char
            # backspace, del --------------------------------------------------------------
            elif input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
                if len(self.command) != 0:
                    self.cursor_x = max(0, self.cursor_x - 1)
                    if self.cursor_x == len(self.command) - 1:
                        self.command = self.command[:self.cursor_x]
                    else:
                        self.command = self.command[:self.cursor_x] + \
                                       self.command[self.cursor_x + 1:]
                    self.redraw()
            elif input_char == curses.KEY_DC:
                if len(self.command) != 0 and self.cursor_x < len(self.command):
                    self.command = self.command[:self.cursor_x] + \
                                    self.command[self.cursor_x + 1:]
                    self.redraw()
            # execute ---------------------------------------------------------------------
            elif input_char == curses.KEY_ENTER or input_char == '\n':
                if self.command != '':
                    self.command_history.append(self.command)
                    self.command_history = self.command_history\
                                         [-self.conf['command_history_buffer_length']:]
                    self.terminal_history.append(">>> " + self.command)
                    self.terminal_history += self.parse_and_execute(stdscr)
                self.command = ''
                self.history_surf_index = 0
                self.cursor_x = 0
                self.scroll = 0
                self.redraw()
            # scrolling -------------------------------------------------------------------
            elif input_char == curses.KEY_PPAGE:
                max_scroll = len(self.terminal_history) + 3 - self.w_height
                # if we can show more than history + 3 reserved lines:
                if max_scroll > 0:
                    self.scroll = min(self.scroll + 1, max_scroll)
                self.redraw()
            elif input_char == curses.KEY_NPAGE:
                self.scroll = max(self.scroll - 1, 0)
                self.redraw()
            # cursor shift ----------------------------------------------------------------
            elif input_char == curses.KEY_LEFT:
                self.cursor_x = max(0, self.cursor_x - 1)
                self.redraw()
            elif input_char == curses.KEY_RIGHT:
                self.cursor_x = min(len(self.command), self.cursor_x + 1)
                self.redraw()
            elif input_char == statics.CTRL_LEFT:
                cut_str = self.command[:self.cursor_x][::-1]
                while len(cut_str) != 0 and cut_str[0] == ' ':
                    cut_str = cut_str[1:]
                    self.cursor_x = max(0, self.cursor_x - 1)
                next_jump = cut_str.find(' ')
                if next_jump == -1:
                    self.cursor_x = 0
                else:
                    self.cursor_x = max(0, self.cursor_x - next_jump)
                self.redraw()
            elif input_char == statics.CTRL_RIGHT:
                cut_str = self.command[self.cursor_x:]
                while len(cut_str) != 0 and cut_str[0] == ' ':
                    cut_str = cut_str[1:]
                    self.cursor_x = min(self.cursor_x + 1, len(self.command))
                next_jump = cut_str.find(' ')
                if next_jump == -1:
                    self.cursor_x = len(self.command)
                else:
                    self.cursor_x = min(self.cursor_x + next_jump, len(self.command))
                    cut_str = self.command[self.cursor_x:]
                self.redraw()
            elif input_char == curses.KEY_HOME:
                self.cursor_x = 0
                self.redraw()
            elif input_char == curses.KEY_END:
                self.cursor_x = len(self.command)
                self.redraw()
            # history surfing -------------------------------------------------------------
            elif input_char == curses.KEY_UP:
                if len(self.command_history) != 0:
                    self.scroll = 0
                    # if we weren't surfing, save the current command in buffer
                    if self.history_surf_index == 0:
                        self.cmd_history_buffer = self.command
                    self.history_surf_index = min(self.history_surf_index + 1,
                                                 len(self.command_history))
                    self.command = self.command_history[-self.history_surf_index]
                    self.cursor_x = len(self.command)
                    self.redraw()
            elif input_char == curses.KEY_DOWN:
                if self.history_surf_index != 0:
                    self.scroll = 0
                    self.history_surf_index -= 1
                    if self.history_surf_index == 0:
                        self.command = self.cmd_history_buffer
                        self.cursor_x = len(self.command)
                    else:
                        self.command = self.command_history[-self.history_surf_index]
                        self.cursor_x = len(self.command)
                    self.redraw()
            # do predictions --------------------------------------------------------------
            elif input_char == '\t':
                p_candidates, p_insert_index, i_str = self.get_command_predictions()
                # nothing to predict
                if len(p_candidates) == 0:
                    continue
                # complete the command at the current level
                if len(p_candidates) == 1:
                    pre_str = self.command[:p_insert_index]
                    post_str = self.command[p_insert_index + len(i_str):]
                    post_str = ' ' if (post_str == '' and \
                                       not p_candidates[0].endswith(' ')) \
                                   else post_str
                    self.command = pre_str + p_candidates[0] + post_str
                    self.cursor_x = min(p_insert_index + len(p_candidates[0]) + 1, \
                                        len(self.command))
                    self.redraw()
                # check double tab
                elif (time.time() - self.last_tab_press) < 0.3:
                    self.terminal_history.append(">>> " + self.command)
                    self.terminal_history.append(' | '.join(p_candidates))
                    self.redraw()
                self.last_tab_press = time.time()
            # normal input ----------------------------------------------------------------
            else:
                # some command that's not used
                if type(input_char) is int:
                    continue
                # ignore leading spaces
                if input_char == ' ':
                    if len(self.command) == 0:
                        continue
                if self.cursor_x == len(self.command):
                    self.command = self.command[:self.cursor_x] + input_char
                else:
                    self.command = self.command[:self.cursor_x] + input_char + \
                                   self.command[self.cursor_x:]
                self.cursor_x += 1
                self.history_surf_index = 0
                self.scroll = 0
                self.redraw()

    def get_command_predictions(self, state = None) -> Tuple[list, int]:
        """
        provides a list of predictions based on the current command
        and the index at which the prediction should be inserted.
        the state indicates the stage in expense mode.
        """
        # two spaces are not allowed
        if self.command.count('  ') > 0:
            return [], 0, None
        incomplete_str = None
        current_cmd = self.command[:self.cursor_x]
        cmd_parts = current_cmd.split(' ')
        pred_insertion_idx = 0
        for i in reversed(range(len(current_cmd))):
            if self.command[i] == ' ':
                pred_insertion_idx = i + 1
                break
        pred_candidates = []
        current_lvl = self.command_dict
        # parsing the command
        while len(cmd_parts) != 0:
            # go one level deeper, if the segment is complete and correct
            if cmd_parts[0] in current_lvl:
                # too deep, no predictions
                if 'task-id' in current_lvl[cmd_parts[0]]:
                    break
                current_lvl = current_lvl[cmd_parts[0]]
                # no space after segment? add it
                if len(cmd_parts) == 1:
                    return [cmd_parts[0] + ' '], pred_insertion_idx, cmd_parts[0]
                cmd_parts.pop(0)
            else:
                incomplete_str = cmd_parts[0]
                for candidate in current_lvl.keys():
                    if candidate.startswith(cmd_parts[0]):
                        pred_candidates.append(candidate)
                break
        pred_candidates.sort(key=len)
        return pred_candidates, pred_insertion_idx, incomplete_str

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
                f.write(f"{self.command_history[i]}\n")

    def warmup(self):
        """
        loads a text file in ./database/.warmup and executes all
        the commands inside.
        """
        try:
            warmup_path = os.path.join(os.path.dirname(__file__),
                                       '../database/.warmup')
            f = open(warmup_path, 'r')
            for line in f:
                line = line.strip()
                if line != '':
                    self.command = line
                    self.terminal_history += self.parse_and_execute(None)
                    self.command = ''
        except FileNotFoundError:
            self.terminal_history.append("could not open warmup file")

    def submit_pending_command(self, stdscr) -> bool:
        """
        pending commands set by the action window are performed here.
        returns True if the focus should afterwards be given to the
        main window (and not remain on the terminal).
        """
        pending = self.pending_action != -1
        if pending:
            # edit action
            if self.pending_action == 0:
                self.terminal_history += \
                    defined_tasks.edit.expense(self, stdscr, \
                                               hex(self.pending_tr_id))
            # delete action
            elif self.pending_action == 1:
                self.terminal_history += \
                    defined_tasks.delete.expense(self.windows[statics.WMAIN], \
                                                 hex(self.pending_tr_id))

            # reset
            self.command = ''
            self.history_surf_index = 0
            self.cursor_x = 0
            self.scroll = 0
            self.pending_action = -1
            self.pending_tr_id = -1
            self.redraw()
        return pending
