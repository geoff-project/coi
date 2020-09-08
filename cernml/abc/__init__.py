#!/usr/bin/env python3
"""Interfaces for common optimization between DESY and CERN accelerators."""

from .env_checker import check_env
from .machine import Machine
from .optenv import OptEnv, OptGoalEnv, Optimizable
from .sepenv import (
    SeparableEnv,
    SeparableGoalEnv,
    SeparableOptEnv,
    SeparableOptGoalEnv,
)

__version__ = "0.1.0"
