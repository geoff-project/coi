# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = abstract-method
# pylint: disable = missing-class-docstring
# pylint: disable = missing-function-docstring
# pylint: disable = redefined-outer-name

"""Test the inheritance behavior of `CustomOptimizerProvider`."""

import typing as t

import pytest

from cernml import coi
from cernml.optimizers import Optimizer


class DirectSubclass(coi.CustomOptimizerProvider):
    # pylint: disable = too-few-public-methods
    @classmethod
    def get_optimizers(cls) -> t.Mapping[str, Optimizer]:
        return super().get_optimizers()


class IndirectSubclass:
    # pylint: disable = too-few-public-methods
    @classmethod
    def get_optimizers(cls) -> t.Mapping[str, Optimizer]:
        return {}


@pytest.mark.parametrize("subclass", [DirectSubclass, IndirectSubclass])
def test_custom_optimizer_provider_defaults(
    subclass: t.Type[coi.CustomOptimizerProvider],
) -> None:
    problem = subclass()
    # pylint: disable = assignment-from-none
    # pylint: disable = use-implicit-booleaness-not-comparison
    assert isinstance(problem, coi.CustomOptimizerProvider)
    assert problem.get_optimizers() == {}
    assert not isinstance(int, coi.CustomOptimizerProvider)
