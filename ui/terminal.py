import yaml
import curses

import defined_tasks
from ui.base import CursesWindow
from data.sqlite_proxy import SQLiteProxy
from misc.utils import variadic_equals_or
import time
#pylint: disable=E1101



class TerminalWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height, \
                 overview_window: CursesWindow, database: SQLiteProxy):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.command = ''
        self.terminal_history = []
        self.command_history = []
        self.scroll = 0

        # settings
        self.overview_window = overview_window
        self.current_account = ''
        
        # prediction stuff
        self.expense_mode = False
        self.prediction = ''
        self.pred_candidates = []
        self.last_tab_press = time.time()
        
        # 
        self.cmd_history_index = 0
        self.cmd_history_buffer = ''

        # loading command yaml file
        with open('config/commands.yaml') as file:    
            self.command_dict = yaml.load(file, Loader=yaml.FullLoader)

        self.database = database        

        self.redraw()

    def focus(self, enable: bool):
        """
        externally called to enable or disable focus on this window.
        it changes the focus flag used in all draw functions.
        """
        self.focused = enable
        curses.curs_set(int(enable))
        if enable:
            self.cwindow.move(1, 6 + len(self.command))
        self.redraw()

    def redraw(self):
        """
        redraws the window based on input, focus flag and predictions.
        """
        self.cwindow.clear()
        # not using first or last line, 1 reserved for current command
        visible_history = min(len(self.terminal_history), self.w_height - 3)
        visible_history += self.scroll
        # disable cursor if scrolling
        curses.curs_set(int(self.scroll == 0 and self.focused))

        curses_attr = curses.A_NORMAL if self.focused else curses.A_DIM
        for i in range (self.w_height - 2):
            if visible_history == 0:
                self.cwindow.addstr(i + 1, 2, ">>> ", curses_attr)
                self.cwindow.addstr(i + 1, 6, self.command, curses_attr)
                break
            self.cwindow.addstr(i + 1, 2, self.terminal_history[-visible_history], curses_attr)
            visible_history -= 1
        self.cwindow.box()
        self.cwindow.refresh()
    
    def parse_and_execute(self) -> str:
        """
        parses and executes the task currently written in the terminal.
        """
        cmd_parts = self.command.split(' ')
        parsed = ''
        current_lvl = self.command_dict
        task_id = -1
        # looking for all commands?
        if len(cmd_parts) == 1 and \
            variadic_equals_or(cmd_parts[0], 'help', '?'):
            return 'available commands: ' + ', '.join(self.command_dict.keys())
        # parsing the command 
        while len(cmd_parts) != 0:
            parsed += cmd_parts[0] + ' ' 
            if cmd_parts[0] not in current_lvl:
                return f"could not find command {parsed}"
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
                return 'available commands: ' + ', '.join(current_lvl.keys())

        # looking for help at last level?
        if len(cmd_parts) == 1 and \
            variadic_equals_or(cmd_parts[0], 'help', '-h', '--help', '?'):
            return current_lvl['desc'] + f", args: {current_lvl['args']}"
        # wrong number of args
        elif len(cmd_parts) != len(current_lvl['args']):
            return f"invalid number of args: {current_lvl['args']}"
        # actually doing the task
        if task_id == 101:
            return defined_tasks.add.account(self.database, cmd_parts[0], cmd_parts[1])
        elif task_id == 201:
            return defined_tasks.list.accounts(self.database)
        elif task_id == 301:
            msg, found = defined_tasks.set.account(self.database, cmd_parts[0])
            if found:
                self.current_account = cmd_parts[0]
            return msg
        elif task_id == 501:
            return defined_tasks.delete.account(self.database, cmd_parts[0])
        elif task_id == 100001:
            self.database.connection.commit()
            self.database.db_close()
            exit()
        elif task_id == 100002:
            self.terminal_history = []
            self.scroll = 0
        else:
            return "don't know how to do this task yet"

    def loop(self, stdscr) -> str:
        """
        main loop for capturing input and updating the window.
        """
        while True:
            input_char = stdscr.getch()
            # if should switch window
            if CursesWindow.is_exit_sequence(input_char):
                return input_char
            # backspace -------------------------------------------------------------------
            elif input_char == curses.KEY_BACKSPACE:
                if len(self.command) != 0:
                    self.command = self.command[:-1]
                    self.redraw()
            # execute ---------------------------------------------------------------------
            elif input_char == curses.KEY_ENTER or input_char == ord('\n'):
                if self.command != '':
                    self.command_history.append(self.command)
                    self.terminal_history.append(">>> " + self.command)
                    self.terminal_history.append(self.parse_and_execute())
                self.command = ''
                self.cmd_history_index = 0
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
            # history surfing -------------------------------------------------------------
            elif input_char == curses.KEY_UP:
                if len(self.command_history) != 0:
                    self.scroll = 0
                    # if we weren't surfing, save the current command in buffer
                    if self.cmd_history_index == 0:
                        self.cmd_history_buffer = self.command
                    self.cmd_history_index = min(self.cmd_history_index + 1,
                                                 len(self.command_history))
                    self.command = self.command_history[-self.cmd_history_index]
                    self.redraw()
            elif input_char == curses.KEY_DOWN:
                if self.cmd_history_index != 0:
                    self.scroll = 0
                    self.cmd_history_index -= 1
                    if self.cmd_history_index == 0:
                        self.command = self.cmd_history_buffer
                    else:
                        self.command = self.command_history[-self.cmd_history_index]
                    self.redraw()
            # do predictions --------------------------------------------------------------
            elif input_char == ord('\t'):
                pred_candidates, pred_index = self.update_predictions()
                # nothing to predict
                if len(pred_candidates) == 0:
                    continue
                if self.expense_mode:
                    pass
                else:
                    # complete the command at the current level
                    if len(pred_candidates) == 1:
                        self.cmd_history_index = 0
                        self.command = self.command[:pred_index] + self.pred_candidates[0]
                        self.redraw()
                    # check double tab
                    elif (time.time() - self.last_tab_press) < 0.3:
                        self.terminal_history.append(">>> " + self.command)
                        self.terminal_history.append(' | '.join(self.pred_candidates))
                        self.redraw()
                    self.last_tab_press = time.time()
            # normal input ----------------------------------------------------------------
            # elif input_char == curses.KEY_:
            # normal input ----------------------------------------------------------------
            elif input_char <= 256:
                if input_char == ord(' '):
                    # leading spaces don't count
                    if len(self.command) == 0:
                        continue
                self.command += chr(input_char)
                self.cmd_history_index = 0
                self.scroll = 0
            
            # redraw is required for all cases
            self.redraw()

    def update_predictions(self) -> (list, int):
        """
        provides a list of predictions based on the current command
        and the index at which the prediction should be inserted
        """
        cmd_parts = self.command.split(' ')
        pred_index = 0
        for i in reversed(range(len(self.command))):
            if self.command[i] == ' ':
                pred_index = i + 1
        # if only one word has been written, add empty string to catch 'else'
        if len(cmd_parts) == 1:
            cmd_parts.append('')
        self.pred_candidates = []
        if self.expense_mode:
            pass
        else:
            current_lvl = self.command_dict
            # parsing the command 
            while len(cmd_parts) != 0:
                # go one level deeper, if the segment is complete and correct
                if cmd_parts[0] in current_lvl:
                    # too deep
                    if 'task-id' in current_lvl[cmd_parts[0]]:
                        break
                    current_lvl = current_lvl[cmd_parts[0]]
                    cmd_parts.pop(0)
                else:
                    for candidate in current_lvl.keys():
                        if candidate.startswith(cmd_parts[0]):
                            self.pred_candidates.append(candidate)
                    break
            self.pred_candidates.sort(key=len)
        return self.pred_candidates, pred_index
