#!/usr/bin/env python3
"""Interfaces for common optimization between DESY and CERN accelerators."""

from .optenv import OptEnv, OptGoalEnv, OptimizeMixin
from .sepenv import (
    SeparableEnv,
    SeparableGoalEnv,
    SeparableOptEnv,
    SeparableOptGoalEnv,
)

__version__ = "0.0.1"
