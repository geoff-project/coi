# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Check the reseeding behavior of `reset()` and `get_initial_params()`."""

import typing as t
import warnings

import numpy as np

from ._generic import bump_warn_arg


class ReseedFn(t.Protocol):  # pragma: no cover
    """Type of callback functions accepted by `assert_reseet()`."""

    def __call__(self, *, seed: t.Optional[int] = None) -> object: ...


def assert_reseed(
    problem: object,
    reseed: ReseedFn,
    warn: int = True,
    *,
    test_seed: t.Optional[int] = None,
) -> None:
    """Check correct seeding behavior of the given function.

    The *reseed* function should be a bound method of the given
    *problem*. This assertion checks that *reseed* changes the seed if
    called with an integer seed; and that it doesn't change the seed if
    called with None.
    """
    warn = bump_warn_arg(warn)
    fn_name = _fn_name(reseed)
    seed = _get_seed(problem, warn=warn)
    if seed is None:
        return
    reseed(seed=None)
    seed_after_no_reseed = _get_seed(problem, warn=warn)
    # If `_get_seed()` is successful once, we expect it to be
    # successful every time.
    assert seed is not None
    assert seed == seed_after_no_reseed, (
        f"env.np_random seed changed even though {fn_name}() "
        f"was called with seed=None; make sure not to reseed your "
        f"environment unconditionally; {seed} != {seed_after_no_reseed}"
    )
    if test_seed is None:
        test_seed = int(np.random.default_rng().integers(1 << 16))
    reseed(seed=test_seed)
    actual_seed = _get_seed(problem, warn=warn)
    assert actual_seed is not None
    assert actual_seed == test_seed, (
        f"env.np_random is not seeded with the expected value; "
        f"don't forget to call super().{fn_name}(seed=seed) in your "
        f"own {fn_name}() implementation; {actual_seed} != {test_seed}"
    )


def _fn_name(function: object) -> str:
    return getattr(function, "__name__", None) or repr(function)


def _get_seed(problem: object, warn: int = True) -> t.Optional[int]:
    """Attempt to fetch the RNG seed from the problem.

    It's important to always start out from *problem* (and not bind the
    RNG once and repeatedly fetch its seed), because
    `gymnasium.utils.seeding.np_random()` creates a new generator every
    time.
    """
    rng: t.Optional[np.random.Generator] = getattr(problem, "np_random", None)
    if rng is None:
        return None
    if not isinstance(rng, np.random.Generator):
        if warn:
            warnings.warn(
                f"problem's `np_random` property should be a "
                f"`numpy.random.Generator`, not {rng!r}",
                stacklevel=warn,
            )
        return None
    seed_seq = rng.bit_generator.seed_seq
    seed: t.Optional[int] = getattr(seed_seq, "entropy", None)
    if seed is None:
        if warn:
            warnings.warn(
                f"Cannot determine RNG seed: "
                f"{rng!r}.bit_generator.seed_seq = {seed_seq!r} "
                f"doesn't have the expected attribute 'entropy'",
                stacklevel=warn,
            )
        return None
    return seed
