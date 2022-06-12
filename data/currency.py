from __future__ import annotations

from abc import ABC
from copy import copy


def sign(num):
    if num > 0:
        return 1
    elif num < 0:
        return -1
    return 0


class Currency(ABC):
    _secondary_limit: int = 0
    _max_secondary_width: int = 0
    _seperator = '.'

    def __init__(self, prim, sec) -> None:
        if sec >= self._secondary_limit:
            raise ValueError(
                f'{self.__class__.__name__} must have a decimal part smaller than {self._secondary_limit}'
            )
        sp = sign(prim)
        ss = sign(sec)
        if sp != ss and sp * ss != 0:
            raise ValueError(
                f'sign of the given parameters {prim}, {sec} do not match')
        self._primary: int = prim
        self._secondary: int = sec

    @classmethod
    def from_str(cls, cu_string: str) -> Currency:
        try:
            sgn = sign(float(cu_string))
        except:
            raise ValueError(
                f'{cu_string} is not a valid value for {cls.__name__}')
        parts = cu_string.split(cls._seperator)
        if len(parts) == 1:
            parts.append('0')
        elif len(parts) == 2:
            if len(parts[1]) > cls._max_secondary_width:
                raise ValueError(
                    f'{cu_string} is not a valid value for {cls.__name__}')
            # add missing trailing zeros, if any
            if not parts[1].startswith('0'):
                parts[1] = parts[1] + '0' * (cls._max_secondary_width -
                                             len(parts[1]))
        else:
            raise ValueError(
                f'{cu_string} is not a valid value for {cls.__name__}')
        return cls(int(parts[0]), int(parts[1]) * sgn)

    def as_str(self, zero_pad: bool = False):
        if self._secondary == 0:
            if zero_pad:
                return f'{self._primary}{self._seperator}{"0" * self._max_secondary_width}'
            return str(self._primary)
        else:
            return f'{self._primary}{self._seperator}{str(abs(self._secondary)).rjust(self._max_secondary_width, "0")}'

    def is_expense(self) -> bool:
        if self._primary == 0:
            return self._secondary < 0
        return self._primary < 0

    def is_income(self) -> bool:
        if self._primary == 0:
            return self._secondary > 0
        return self._primary > 0

    def __verify_type(self, op: str, other):
        if not isinstance(other, type(self)):
            raise TypeError(
                f'unsupported operand type(s) for {op}: {self.__class__.__name__} '
                f'and {other.__class__.__name__}')

    def __str__(self):
        return self.as_str(True)

    def __repr__(self) -> str:
        return self.as_str(True)

    def __neg__(self):
        sls = self._primary * self._secondary_limit + self._secondary
        sls = -sls
        new_obj = copy(self)
        new_obj._primary = int(sls / self._secondary_limit)
        new_obj._secondary = (abs(sls) % self._secondary_limit) * sign(sls)
        return new_obj

    def __abs__(self):
        sls = abs(self._primary * self._secondary_limit + self._secondary)
        new_obj = copy(self)
        new_obj._primary = int(sls / self._secondary_limit)
        new_obj._secondary = (abs(sls) % self._secondary_limit) * sign(sls)
        return new_obj

    def __add__(self, other: Currency):
        self.__verify_type('+', other)
        sls = self._primary * self._secondary_limit + self._secondary
        ots = other._primary * other._secondary_limit + other._secondary
        sum_sec = sls + ots
        new_obj = copy(other)
        new_obj._primary = int(sum_sec / self._secondary_limit)
        new_obj._secondary = (abs(sum_sec) %
                              self._secondary_limit) * sign(sum_sec)
        return new_obj

    def __iadd__(self, other: Currency):
        self.__verify_type('+', other)
        sls = self._primary * self._secondary_limit + self._secondary
        ots = other._primary * other._secondary_limit + other._secondary
        sum_sec = sls + ots
        self._primary = int(sum_sec / self._secondary_limit)
        self._secondary = (abs(sum_sec) %
                           self._secondary_limit) * sign(sum_sec)
        return self

    def __sub__(self, other: Currency):
        self.__verify_type('-', other)
        sls = self._primary * self._secondary_limit + self._secondary
        ots = -(other._primary * other._secondary_limit + other._secondary)
        sum_sec = sls + ots
        new_obj = copy(other)
        new_obj._primary = int(sum_sec / self._secondary_limit)
        new_obj._secondary = (abs(sum_sec) %
                              self._secondary_limit) * sign(sum_sec)
        return new_obj

    def __isub__(self, other: Currency):
        self.__verify_type('-', other)
        sls = self._primary * self._secondary_limit + self._secondary
        ots = -(other._primary * other._secondary_limit + other._secondary)
        sum_sec = sls + ots
        self._primary = int(sum_sec / self._secondary_limit)
        self._secondary = (abs(sum_sec) %
                           self._secondary_limit) * sign(sum_sec)
        return self

    def __lt__(self, other: Currency):
        self.__verify_type('<', other)
        if abs(self._primary) < abs(other._primary):
            return True
        if abs(self._primary) == abs(other._primary) and abs(
                self._secondary) < abs(other._secondary):
            return True
        return False

    def __gt__(self, other: Currency):
        self.__verify_type('>', other)
        if abs(self._primary) > abs(other._primary):
            return True
        if abs(self._primary) == abs(other._primary) and abs(
                self._secondary) > abs(other._secondary):
            return True
        return False

    def __eq__(self, other: Currency):
        self.__verify_type('==', other)
        return abs(self._primary) == abs(other._primary) and abs(
            self._secondary) == abs(other._secondary)

    def __ne__(self, other: Currency):
        self.__verify_type('!=', other)
        return abs(self._primary) != abs(other._primary) or abs(
            self._secondary) != abs(other._secondary)

    def __le__(self, other: Currency):
        return self < other or self == other

    def __ge__(self, other: Currency):
        return self > other or self == other

    @classmethod
    def from_float(cls, value: float) -> Currency:
        sgn = sign(value)
        value = abs(value)
        prm = int(value)
        sec = int(round((value - prm) * cls._secondary_limit))
        return cls(prm * sgn, sec * sgn)

    @property
    def float_value(self):
        return round(self._primary + self._secondary / self._secondary_limit,
                     self._max_secondary_width)

    @float_value.setter
    def float_value(self, value):
        sgn = sign(value)
        value = abs(value)
        self._primary = int(value)
        self._secondary = int(
            round((value - self._primary) * self._secondary_limit))
        self._primary *= sgn
        self._secondary *= sgn


class Euro(Currency):

    _secondary_limit: int = 100
    _max_secondary_width: int = 2

    def __init__(self, euro, cent) -> None:
        super().__init__(euro, cent)

    @property
    def euros(self):
        return self._primary

    @euros.setter
    def euros(self, value):
        if not isinstance(value, int):
            raise ValueError('expected integer value for euros')
        self._primary = value
        if sign(self._secondary) != sign(value):
            self._secondary *= sign(value)

    @property
    def cents(self):
        return self._secondary

    @cents.setter
    def cents(self, value):
        if not isinstance(value, int):
            raise ValueError('expected integer value for cents')
        if value >= 100:
            raise ValueError('cents must be smaller than 100')
        sc = sign(value)
        sp = sign(self._primary)
        if sc != sp and sc * sp != 0:
            raise ValueError('cents\' sign must match euros')
        self._secondary = value
