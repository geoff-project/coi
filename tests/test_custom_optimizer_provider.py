# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the inheritance behavior of `CustomOptimizerProvider`."""

import typing as t

from cernml import coi

if t.TYPE_CHECKING:
    from cernml.optimizers import Optimizer


class DirectSubclass(coi.CustomOptimizerProvider):
    # pylint: disable = too-few-public-methods
    @classmethod
    def get_optimizers(cls) -> t.Mapping[str, "Optimizer"]:
        return super().get_optimizers()


class IndirectSubclass:
    # pylint: disable = too-few-public-methods
    @classmethod
    def get_optimizers(cls) -> t.Mapping[str, "Optimizer"]:
        return {}


class NotASubclass:
    # pylint: disable = too-few-public-methods
    def get_optimizers(self) -> t.Mapping[str, "Optimizer"]:
        return {}


def test_custom_optimizer_provider_defaults() -> None:
    problem = DirectSubclass()
    # pylint: disable = use-implicit-booleaness-not-comparison
    assert isinstance(problem, coi.CustomOptimizerProvider)
    assert problem.get_optimizers() == {}


def test_is_protocol() -> None:
    problem = IndirectSubclass()
    assert isinstance(problem, coi.CustomOptimizerProvider)
    assert not isinstance(int, coi.CustomOptimizerProvider)


def test_protocol_checks_classmethod() -> None:
    problem = NotASubclass()
    assert not isinstance(problem, coi.CustomOptimizerProvider)
