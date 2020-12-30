import curses
from ui.static import min_window_x, min_window_y
from ui.base import CursesWindow
import yaml
#pylint: disable=E1101

def variadic_equals_or(first: str, *argv):  
    for arg in argv:  
        if first == arg:
            return True
    return False

class TerminalWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height):
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.command = ''
        self.history = []
        self.scroll = 0

        # settings
        self.account_name = ''

        # prediction stuff
        self.segment = 0
        self.prediction = ''
        self.pred_start = 0

        self.redraw()

        # loading command yaml file
        with open('config/commands.yaml') as file:    
            self.command_dict = yaml.load(file, Loader=yaml.FullLoader)


    def focus(self, enable: bool):
        self.focused = enable
        curses.curs_set(int(enable))
        if enable:
            self.cwindow.move(1, 6 + len(self.command))
        self.redraw()

    def redraw(self):
        self.cwindow.clear()
        # not using first or last line, 1 reserved for current command
        visible_history = min(len(self.history), self.w_height - 3)
        visible_history += self.scroll
        # disable cursor if scrolling
        curses.curs_set(int(self.scroll == 0 and self.focused))

        curses_attr = curses.A_NORMAL if self.focused else curses.A_DIM
        for i in range (self.w_height - 2):
            if visible_history == 0:
                self.cwindow.addstr(i + 1, 2, ">>> ", curses_attr)
                self.cwindow.addstr(i + 1, 6, self.command, curses_attr)
                break
            self.cwindow.addstr(i + 1, 2, self.history[-visible_history], curses_attr)
            visible_history -= 1
        self.cwindow.box()
        self.cwindow.refresh()
    
    def do_task(self, command: str) -> str:
        """
        performs tasks defined in the yaml file.
        """
        cmd_parts = command.split(' ')
        parsed = ''
        current_lvl = self.command_dict
        task_id = -1
        # looking for all commands?
        if len(cmd_parts) == 1 and \
            variadic_equals_or(cmd_parts[0], 'help', '?'):
            help_str = 'available commands: '
            for key in self.command_dict:
                help_str += key + ' '
            return help_str

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
            elif len(cmd_parts) == 0 or \
                variadic_equals_or(cmd_parts[0], 'help', '?'):
                help_str = 'available commands: '
                for key in current_lvl:
                    help_str += key + ' '
                return help_str

        # help or wrong number of args
        if len(cmd_parts) == 1 and \
            variadic_equals_or(cmd_parts[0], 'help', '-h', '--help', '?'):
            return current_lvl['desc'] + f", args: {current_lvl['args']}"
        elif len(cmd_parts) != len(current_lvl['args']):
            return f"invalid number of args: {current_lvl['args']}"
        # actually doing the task
        return current_lvl['desc'] + f", args: {current_lvl['args']}"

    def loop(self, stdscr) -> str:
        while True:
            input_str = stdscr.getkey()
            # if should switch window
            if CursesWindow.is_exit_sequence(input_str):
                return input_str
            # backspace ------------------------------------------------
            elif input_str == 'KEY_BACKSPACE':
                if len(self.command) != 0:
                    self.command = self.command[:-1]
                    self.redraw()
            # submit ---------------------------------------------------
            elif (input_str == '\n' or input_str == 'KEY_ENTER'):
                if self.command != '':
                    self.history.append(">>> " + self.command)
                    ret_str = self.do_task(self.command)
                    if ret_str != '':
                        self.history.append(ret_str)
                self.command = ''
                self.segment = 0
                self.redraw()
                # TODO: perform task
            # scrolling ------------------------------------------------
            elif input_str == 'KEY_UP':
                max_scroll = len(self.history) + 3 - self.w_height
                # if we can show more than history + 3 reserved lines:
                if max_scroll > 0:
                    self.scroll = min(self.scroll + 1, max_scroll)
                self.redraw()
            elif input_str == 'KEY_DOWN':
                self.scroll = max(self.scroll - 1, 0)
                self.redraw()
            # do predictions -------------------------------------------
            elif input_str == '\t':
                pass
            # normal input ---------------------------------------------
            elif len(input_str) == 1:
                self.scroll = 0
                if input_str == ' ':
                    # leading spaces don't count
                    if len(self.command) == 0:
                        continue
                    self.segment += 1
                    self.pred_start = len(input_str)
                self.command += input_str
                self.redraw()
