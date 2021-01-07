import curses

from ui.static import WACTION
from ui.base import CursesWindow
from ui.elements.list import CursesList

from data.sqlite_proxy import SQLiteProxy
from data.account import Account
from data.record import Record
from datetime import date, datetime

#pylint: disable=E1101

class MainWindow(CursesWindow):
    def __init__(self, stdscr, w_x, w_y, w_width, w_height, windows: list):
        """
        initializes the main window. the main window holds the
        current account, which acts as a proxy between the ui
        and the database.
        """
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        self.account = None
        self.showing = 'nothing'
        self.windows = windows
        # padding on the sides
        self.list_width = int(w_width - 2)
        self.list_height = int((3 / 4) * self.w_height)
        self.clist = CursesList(2, 5, self.list_width, self.list_height, [], \
                                ' | '.join(Record.columns(7, 10, 20, 20, 22, 36)))
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
        self.cwindow.addstr(1, 2, f"account: {account_str}", curses_attr)
        self.cwindow.addstr(2, 2, f"date: {date_str}", curses_attr)
        self.cwindow.addstr(3, 2, f"balance: {balance:.2f}", curses_attr)
        self.clist.redraw(self.cwindow, curses_attr)
        self.cwindow.addstr(8 + self.list_height, 3, f"showing: {self.showing}", curses_attr)
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

    def update_table_row(self, index: int):
        """
        updates the table at the given index. called after editing a
        record
        """
        self.clist.items[index] = '   '.join(self.account.records[index]
                                       .to_str(index, 7, 10, 20, 20, 22, 36))

    def delete_table_row(self, index: int):
        """
        to be called after deleting a transaction from the account.
        this is a duplicate of refresh_table_records because the 
        elements need to be reindexed when one is deleted.
        """
        str_records = []
        for idx, record in enumerate(self.account.records):
            str_records.append('   '.join(record.to_str(idx, 7, 10, 20, 20, 22, 36)))
        self.clist.items = str_records
        self.clist.index = max(0, index - 1)
        self.redraw()

    def refresh_table_records(self, label: str):
        """
        refreshes the transaction table to show the latest changes from
        the database.
        """
        str_records = []
        for idx, record in enumerate(self.account.records):
            str_records.append('   '.join(record.to_str(idx, 7, 10, 20, 20, 22, 36)))
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
                self.windows[WACTION].expense_list_index, _ = self.clist.key_enter()
                return curses.KEY_F60

