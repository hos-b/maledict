# Maledict
ncurses-based expense tracker

## requirements
- python
- sqlite3

## bugs
won't fit perfectly in all [small] windows because `window.getmaxyx()` always retuns larger dimensions than the actual screen size, at least on i3. won't fix.