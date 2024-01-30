# SPDX-FileCopyrightText: 2020-2023 CERN
# SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Definition of the `CustomOptimizerProvider` interface."""

import typing as t
from abc import ABCMeta, abstractmethod

from ._abc_helpers import check_methods as _check_class_methods

if t.TYPE_CHECKING:
    import cernml.optimizers


class CustomOptimizerProvider(metaclass=ABCMeta):
    """Interface for optimization problems with custom optimizers."""

    @classmethod
    @abstractmethod
    def get_optimizers(cls) -> t.Mapping[str, "cernml.optimizers.Optimizer"]:
        """Return the custom optimizers offered by this problem.

        The return value is a mapping from optimizer name to optimizer.
        The name should be sufficiently unique and follow the format of
        other, registered optimization algorithms.
        """
        return {}

    @classmethod
    def __subclasshook__(cls, other: type) -> t.Any:
        if cls is CustomOptimizerProvider:
            return _check_class_methods(other, "get_optimizers")
        return NotImplemented
