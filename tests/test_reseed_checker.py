# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the assert_reseed() function."""

from __future__ import annotations

import warnings
from contextlib import nullcontext as doesnt_raise
from unittest.mock import Mock, call

import numpy as np
import pytest

from cernml.coi.checkers._reseed import assert_reseed


def test_works() -> None:
    obj = Mock()
    obj.np_random.mock_add_spec(np.random.Generator)

    def reseed(seed: int | None = None) -> None:
        if seed is not None:
            obj.np_random.bit_generator.seed_seq.entropy = seed

    assert_reseed(obj, reseed)


def test_always_reseed() -> None:
    obj = Mock()
    obj.np_random.mock_add_spec(np.random.Generator)

    def reseed(seed: int | None = None) -> None:
        obj.np_random.bit_generator.seed_seq.entropy = Mock()

    with pytest.raises(AssertionError, match="seed changed.*called with seed=None"):
        assert_reseed(obj, reseed)


def test_never_reseed() -> None:
    obj = Mock()
    obj.np_random.mock_add_spec(np.random.Generator)
    with pytest.raises(AssertionError, match="not seeded with the expected value"):
        assert_reseed(obj, Mock())


def test_given_test_seed() -> None:
    obj = Mock()
    obj.np_random.mock_add_spec(np.random.Generator)

    def reseed(seed: int | None = None) -> None:
        if seed is not None:
            obj.np_random.bit_generator.seed_seq.entropy = seed

    reseed = Mock(name="reseed", wraps=reseed)
    test_seed = Mock(name="test_seed")
    assert_reseed(obj, reseed, test_seed=test_seed)
    assert reseed.call_args_list == [call(seed=None), call(seed=test_seed)]


def test_no_rng() -> None:
    obj = Mock(np_random=None)
    reseed = Mock()
    assert_reseed(obj, reseed)
    reseed.assert_not_called()


@pytest.mark.parametrize("warn", [False, True])
def test_warn_bad_rng(warn: bool) -> None:
    obj = Mock()
    reseed = Mock()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with (
            pytest.raises(UserWarning, match="should be a `numpy.random.Generator`")
            if warn
            else doesnt_raise()
        ):
            assert_reseed(obj, reseed, warn=warn)


@pytest.mark.parametrize("warn", [False, True])
def test_warn_bad_entropy(warn: bool) -> None:
    obj = Mock()
    obj.np_random.mock_add_spec(np.random.Generator)
    obj.np_random.bit_generator.seed_seq.entropy = None
    reseed = Mock()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with (
            pytest.raises(UserWarning, match="doesn't have .* 'entropy'")
            if warn
            else doesnt_raise()
        ):
            assert_reseed(obj, reseed, warn=warn)
