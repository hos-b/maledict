# Maledict
ncurses-based expense tracker

## requirements
- python

## bugs
won't fit perfectly in all [small] windows because `window.getmaxyx()` always returns larger dimensions than the actual screen size, at least on i3. won't fix.
resizing doesn't work for the same reason

## adding new commands
- add the command to `config/commands.yaml`
- add the code to `defined_tasks/<command name>.py`
- import the submodule in `defined_tasks/__init__.py` if necessary
- add the necessary if condition to `ui/terminal.py` in `parse_and_execute()`
