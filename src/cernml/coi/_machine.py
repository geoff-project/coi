# SPDX-FileCopyrightText: 2020-2023 CERN
# SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""An enum of all the possible CERN accelerating machines."""

from enum import Enum


class Machine(Enum):
    """Enum of the various accelerators at CERN.

    This enum should be used by environments in their
    `~Problem.metadata` dictionary to declare which accelerator they
    pertain to. This can be used to filter a collection of environments
    for only those that are interesting to a certain group of operators.

    This list is intentionally left incomplete. If you wish to use this
    API at a machine that is not listed in this enum, please contact the
    developers to have it included.

    In the same vein, if you match a `Machine` against a list of enum
    members, you should be prepared that new machines may be added in
    the future.

        >>> # Bad:
        >>> def get_proper_value_for(machine):
        ...     return {
        ...         Machine.LINAC_2: 1.0,
        ...         Machine.LINAC_3: 4.0,
        ...         Machine.LINAC_4: 3.0,
        ...     }[machine]
        >>> get_proper_value_for(Machine.LINAC_4)
        3.0
        >>> # Oops! ISOLDE was added in cernml-coi v0.7.1.
        >>> get_proper_value_for(Machine.ISOLDE)
        Traceback (most recent call last):
        ...
        KeyError: <Machine.ISOLDE: 'ISOLDE'>
        >>> # Better:
        >>> def get_proper_value_for(machine):
        ...     some_reasonable_default = 0.0
        ...     return {
        ...         Machine.LINAC_2: 1.0,
        ...         Machine.LINAC_3: 4.0,
        ...         Machine.LINAC_4: 3.0,
        ...     }.get(machine, some_reasonable_default)
        >>> get_proper_value_for(Machine.ISOLDE)
        0.0

    Of course, if there is *no* reasonable default for an unknown
    machine, raising an exception may still be your best bet.
    """

    NO_MACHINE = "no machine"
    LINAC_2 = "Linac2"
    LINAC_3 = "Linac3"
    LINAC_4 = "Linac4"
    LEIR = "LEIR"
    PS = "PS"  # pylint: disable=invalid-name
    PSB = "PSB"
    SPS = "SPS"
    AWAKE = "AWAKE"
    LHC = "LHC"
    ISOLDE = "ISOLDE"
    AD = "AD"  # pylint: disable=invalid-name
    ELENA = "ELENA"
