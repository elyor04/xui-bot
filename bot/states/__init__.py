"""Finite-state-machine state groups used by multi-step flows."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class CreateClient(StatesGroup):
    inbounds = State()
    email = State()
    quota = State()
    days = State()
    comment = State()
    confirm = State()


class FindClient(StatesGroup):
    email = State()


class ExtendClient(StatesGroup):
    days = State()


class SetQuota(StatesGroup):
    gb = State()


class SetExpiry(StatesGroup):
    days = State()


class SetIpLimit(StatesGroup):
    count = State()


class SetTgId(StatesGroup):
    waiting = State()


class SelectTimezone(StatesGroup):
    waiting = State()
