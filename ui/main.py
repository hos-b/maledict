import curses

from ui.base import CursesWindow
from ui.elements.list import CursesList

from data.sqlite_proxy import SQLiteProxy
from data.account import Account
from data.record import Record
from datetime import date, datetime

#pylint: disable=E1101

class MainWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height):
        """
        initializes the main window. the main window holds the
        current account, which acts as a proxy between the ui
        and the database.
        """
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.account = None
        self.showing = 'nothing'
        # padding on the sides
        self.list_width = int(w_width - 2)
        self.list_height = int((3 / 4) * self.w_height)
        self.clist = CursesList(5, 5, self.list_width, self.list_height, [], \
                                ' | '.join(Record.columns(10, 22, 22, 22, 35)))
        self.redraw()
    
    def focus(self, enable: bool):
        """
        overwriting base due to the extra element
        """
        self.focused = enable
        self.clist.focused = enable
        self.redraw()

    def redraw(self):
        """
        redraws the actions menu
        """
        self.cwindow.clear()
        curses_attr = curses.A_NORMAL if self.focused else curses.A_DIM
        account_str = self.account.name if self.account else 'not set'
        balance = self.account.balance if self.account else 0.0
        date_str = datetime.now().strftime("%d.%m.%Y")
        self.cwindow.addstr(1, 5, f"account: {account_str}", curses_attr)
        self.cwindow.addstr(2, 5, f"date: {date_str}", curses_attr)
        self.cwindow.addstr(3, 5, f"balance: {balance:.2f}", curses_attr)
        self.clist.redraw(self.cwindow, curses_attr)
        self.cwindow.addstr(7 + self.list_height, 5, f"showing: {self.showing}", curses_attr)
        self.cwindow.box()
        self.cwindow.refresh()

    def change_current_account(self, account: Account):
        """
        changes the account on the main window & refreshes the transaction
        table. if the account is set to none, the table is cleared.
        """
        self.account = account
        if self.account is None:
            self.clist.items = []
            self.clist.index = 0
            self.showing = 'nothing'
        else:
            self.refresh_table_records('all transactions')

        self.redraw()
    
    def refresh_table_records(self, label: str):
        """
        refreshes the transaction table to show the latest changes from
        the database.
        """
        str_records = []
        for record in self.account.records:
            str_records.append('   '.join(record.to_str(10, 22, 22, 22, 35)))
        # del self.clist.items
        self.clist.items = str_records
        self.clist.index = 0
        self.clist.scroll = 0
        self.showing = label
        self.redraw()

    def loop(self, stdscr) -> str:
        """
        main window ui loop
        """
        while True:
            input_char = stdscr.getch()
            if CursesWindow.is_exit_sequence(input_char):
                return input_char
            if input_char == curses.KEY_UP:
                self.clist.key_up()
                self.redraw()
            elif input_char == curses.KEY_DOWN:
                self.clist.key_down()
                self.redraw()
            elif input_char == curses.KEY_PPAGE:
                self.clist.key_pgup()
                self.redraw()
            elif input_char == curses.KEY_NPAGE:
                self.clist.key_pgdn()
                self.redraw()
            elif input_char == ord('\n') or input_char == curses.KEY_ENTER:
                # opt_idx, opt_str = self.clist.key_enter()
                # TODO: add functionalities
                return curses.KEY_F60

