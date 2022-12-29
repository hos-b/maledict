import curses

from datetime import datetime
from typing import List

import data.config as cfg

from misc.statics import WinID
from ui.base import CursesWindow
from ui.elements.list import CursesList
from data.account import Account
from data.record import Record
from data.currency import Currency


class MainWindow(CursesWindow):

    def __init__(self, stdscr, w_x, w_y, w_width, w_height, windows: List[CursesWindow]):
        """
        initializes the main window. the main window holds the
        current account, which acts as a proxy between the ui
        and the database.
        """
        super().__init__(stdscr, w_x, w_y, w_width, w_height)
        # other stuff
        self.disable_actions = False
        self.account = None
        self.table_label = 'nothing'
        self.windows = windows
        # padding on the sides
        self.list_width = int(w_width - 2)
        self.list_height = int((3 / 4) * self.w_height)
        self.clist = CursesList(
            cfg.main.list_x_offset, cfg.main.list_y_offset,
            self.list_width, self.list_height, [],
            cfg.table.scrollbar_enable, ' | '.join(
                Record.columns()))
        # shown income, expense
        self.table_income: Currency = None
        self.table_expense: Currency = None

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
        redraws the main window
        """
        self.cwindow.erase()
        curses_attr = curses.A_NORMAL if self.focused else curses.A_DIM
        currency_sign = f' [ {self.account.currency_type.__name__}' \
                        f', {self.account.currency_type.symbol} ]' if self.account else ''
        account_str = self.account.name if self.account else 'not set'
        balance_str = self.account.balance.as_str(True) if self.account else '0.0'
        income_str = self.table_income.as_str(True) if self.table_income else '0.0'
        expense_str = self.table_expense.as_str(True) if self.table_expense else '0.0'
        numlen = max(len(income_str), len(expense_str))
        date_str = datetime.now().strftime('%d.%m.%Y')
        self.cwindow.addstr(1, 2, f'account: {account_str}{currency_sign}', curses_attr)
        self.cwindow.addstr(2, 2, f'date: {date_str}', curses_attr)
        self.cwindow.addstr(3, 2, f'balance: {balance_str}', curses_attr)
        self.cwindow.addstr(2, self.max_x - numlen - 25,
                            f'period income:  {income_str.rjust(numlen)}', curses_attr)
        self.cwindow.addstr(3, self.max_x - numlen - 25,
                            f'period expense: {expense_str.rjust(numlen)}', curses_attr)
        self.clist.redraw(self.cwindow, curses_attr)
        self.cwindow.addstr(8 + self.list_height, 3,
                            f'showing: {self.table_label}', curses_attr)
        self.cwindow.box()
        self.cwindow.refresh()

    def change_current_account(self, account: Account):
        """
        changes the account on the main window & refreshes the transaction
        table. if the account is set to none, the table is cleared.
        """
        self.account = account
        if self.account is None:
            self.clist.change_items([])
            self.table_label = 'nothing'
            self.table_income = account.currency_type(0, 0)
            self.table_expense = account.currency_type(0, 0)
        else:
            self.refresh_table_records('all transactions')

        self.redraw()

    def update_table_row(self, index: int):
        """
        updates the table at the given index. called after editing a
        record on the account object using update_transaction()
        """
        self.clist.items[index] = '   '.join(self.account.records[index]
                                       .to_str(self.icol, self.acol, self.ccol,
                                               self.sccol, self.pcol, self.ncol))

    def delete_table_row(self, index: int):
        """
        to be called after deleting a transaction from the account, it
        deletes the table row given its index. delta is the resulted
        difference in account balance.
        """
        self.clist.delete_item(index)
        self.redraw()

    def update_table_statistics(self, old_amount: Currency,
                                new_amount: Currency):
        """
        updates table income & table expense, called after add,
        edit or update.
        """
        # remove the old transaction
        if old_amount.is_expense():
            self.table_expense -= abs(old_amount)
        else:
            self.table_income -= old_amount
        # add the new transaction
        if new_amount.is_expense():
            self.table_expense += abs(new_amount)
        else:
            self.table_income += new_amount

    def refresh_table_records(self,
                              label: str,
                              custom_records: List[Record] = None):
        """
        refreshes the transaction table to show the latest changes from the
        the database. if custom records are provided, they will be displayed
        instead. transactions are converted to strings and cached so that a
        redraw() can be performed without having to recalculate each line.
        """
        str_records = []
        self.table_expense = self.account.currency_type(0, 0)
        self.table_income = self.account.currency_type(0, 0)
        # if not a custom query, just use the account records
        if custom_records is None:
            custom_records = self.account.records
        for record in custom_records:
            # fake LTR whitespace to enforce BiDi consistency
            str_records.append('\u2066   \u202c'.join(record.to_str_list()))
            if record.amount.is_income():
                self.table_income += record.amount
            else:
                self.table_expense += abs(record.amount)
        self.clist.change_items(str_records)
        self.table_label = label
        self.redraw()

    def loop(self, stdscr) -> str:
        """
        main window ui loop
        """
        while True:
            try:
                input_char = stdscr.getch()
            except KeyboardInterrupt:
                return curses.KEY_F50

            if CursesWindow.is_exit_sequence(input_char):
                return input_char
            if input_char == curses.KEY_UP:
                self.clist.move_selection_up()
                self.redraw()
            elif input_char == curses.KEY_DOWN:
                self.clist.move_selection_down()
                self.redraw()
            elif input_char == curses.KEY_PPAGE:
                self.clist.scroll_page_up()
                self.redraw()
            elif input_char == curses.KEY_NPAGE:
                self.clist.scroll_page_down()
                self.redraw()
            elif input_char == ord('\n') or input_char == curses.KEY_ENTER:
                # actions are disabled in query mode
                if not self.disable_actions:
                    idx, _ = self.clist.get_selected_item()
                    self.windows[WinID.Action].transaction_id = \
                        self.account.records[idx].transaction_id
                    return curses.KEY_F60
