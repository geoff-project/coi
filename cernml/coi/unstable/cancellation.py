"""This module is deprecated. Use cernml.coi.cancellation instead."""

import warnings

from ..cancellation import CancelledError, CannotReset, Token, TokenSource

__all__ = [
    "CancelledError",
    "CannotReset",
    "Token",
    "TokenSource",
]

warnings.warn(
    "cernml.coi.unstable.cancellation is deprecated. "
    "Please use cernml.coi.cancellation instead.",
    DeprecationWarning,
    stacklevel=2,
)
