# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the cancellation module.

This module does not need to be thorough. Most coverage is achieved
through the doctests in `cernml.coi.cancellation` itself.
"""

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
