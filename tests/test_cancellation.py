"""Test the cancellation module.

This module does not need to be thorough. Most coverage is achieved
through the doctests in :mod:`cernml.coi.cancellation` itself.
"""

# pylint: disable = missing-class-docstring, missing-function-docstring

from cernml.coi import cancellation


def test_basic() -> None:
    source = cancellation.TokenSource()
    token = source.token
    assert not source.cancellation_requested
    assert not token.cancellation_requested
    assert source.can_reset_cancellation
    source.cancel()
    assert source.cancellation_requested
    assert token.cancellation_requested
    assert not source.can_reset_cancellation
    token.complete_cancellation()
    assert source.cancellation_requested
    assert token.cancellation_requested
    assert source.can_reset_cancellation
    source.reset_cancellation()
    assert not source.cancellation_requested
    assert not token.cancellation_requested
    assert source.can_reset_cancellation
