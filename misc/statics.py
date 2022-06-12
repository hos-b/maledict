from enum import IntEnum

# global ints

class WinID(IntEnum):
    Main = 0
    Action = 1
    Terminal = 2


# keyboard shortcuts
__layout = 2
__CTRL_LEFT_1 = 545
__CTRL_RIGHT_1 = 560
__CTRL_UP_1 = 566
__CTRL_DOWN_1 = 525
__CTRL_PG_UP_1 = 555
__CTRL_PG_DOWN_1 = 550

__CTRL_LEFT_2 = 546
__CTRL_RIGHT_2 = 561
__CTRL_UP_2 = 567
__CTRL_DOWN_2 = 526
__CTRL_PG_UP_2 = 556
__CTRL_PG_DOWN_2 = 551

if __layout == 1:
    _CTRL_LEFT = __CTRL_LEFT_1
    _CTRL_RIGHT = __CTRL_RIGHT_1
    _CTRL_PG_UP = __CTRL_PG_UP_1
    _CTRL_UP = __CTRL_UP_1
    _CTRL_DOWN = __CTRL_DOWN_1
    _CTRL_PG_DOWN = __CTRL_PG_DOWN_1
else:
    _CTRL_LEFT = __CTRL_LEFT_2
    _CTRL_RIGHT = __CTRL_RIGHT_2
    _CTRL_PG_UP = __CTRL_PG_UP_2
    _CTRL_UP = __CTRL_UP_2
    _CTRL_DOWN = __CTRL_DOWN_2
    _CTRL_PG_DOWN = __CTRL_PG_DOWN_2

class KeyCombo(IntEnum):
    CTRL_LEFT: int = _CTRL_LEFT
    CTRL_RIGHT: int = _CTRL_RIGHT
    CTRL_PG_UP: int = _CTRL_PG_UP
    CTRL_UP: int = _CTRL_UP
    CTRL_DOWN: int = _CTRL_DOWN
    CTRL_PG_DOWN: int = _CTRL_PG_DOWN