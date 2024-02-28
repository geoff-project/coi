# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Definition of the `CustomOptimizerProvider` interface."""

import typing as t
from abc import abstractmethod

from ._abc_helpers import AttrCheckProtocol

if t.TYPE_CHECKING:
    import cernml.optimizers


@t.runtime_checkable
class CustomOptimizerProvider(AttrCheckProtocol, t.Protocol):
    """Interface for optimization problems with custom optimizers.

    This protocol gives subclasses of `SingleOptimizable` and
    `FunctionOptimizable` the opportunity to dynamically define
    specialized optimization algorithms that are tailored to the
    problem. Host applications are expected to check the presence of
    this interface and, if possible, call `get_optimizers()` before
    presenting a list of optimization algorithms to the user.

    Optimizers provided by this protocol should themselves follow the
    protocol defined by :class:`~cernml.optimizers.Optimizer`. Beware
    that that protocol is defined in a separate package, which can be
    installed with one of these lines:

    .. code-block:: shell-session

        $ pip install cernml-coi-optimizers  # The concrete package
        $ pip install cernml-coi[optimizers] # as extra of this package
        $ pip install cernml-coi[all]        # as part of all extras

    This is an :term:`std:abstract base class`. This means even classes
    that don't inherit from it may be considered a subclass. To be
    considered a subclass, a class must merely provide
    a `std:classmethod` (*not* a `std:staticmethod` or regular instance
    :term:`std:method`!) with the name ``get_optimizers``.

    Custom optimizers may also be provided through an :doc:`entry point
    <pkg:specifications/entry-points>`. Entry points in the group
    ``cernml.custom_optimizers`` that have the same name as the
    *registered* name of the optimization problem (not the class name!)
    must point to either a subclass of `CustomOptimizerProvider`, or
    a function that acts as the `get_optimizers()` method of such
    a subclass. A host application may load and invoke such an entry
    point if and only if the user selects an optimization problem with
    a matching name.
    """

    @classmethod
    @abstractmethod
    def get_optimizers(cls) -> t.Mapping[str, "cernml.optimizers.Optimizer"]:
        """Return the custom optimizers offered by this problem.

        The return value is a mapping from optimizer name to optimizer.
        The name should follow the format of other, registered
        optimizers and not conflict with any of their names.

        Custom optimizers with the same name may be returned by
        different optimization problems and may be different from each
        other.
        """
        return {}
