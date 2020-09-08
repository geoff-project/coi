#!/usr/bin/env python
"""An enum of all the possible machines an environment can pertain to."""

from enum import Enum

__all__ = ['Machine']


class Machine(Enum):
    """Enum of the various accelerators at CERN.

    This enum should be used by environments in their `metadata` dictionary to
    declare which accelerator they pertain to. This can be used to filter a
    collection of environments for only those that are interesting to a certain
    group of operators.

    This list is intentionally left incomplete. If you wish to use this API at
    a machine that is not listed in this enum, please contact the developers to
    have it included.
    """
    NoMachine = 'no machine'
    Linac2 = 'Linac2'
    Linac3 = 'Linac3'
    Linac4 = 'Linac4'
    Leir = 'Leir'
    PS = 'PS'
    PSB = 'PSB'
    SPS = 'SPS'
    Awake = 'AWAKE'
    LHC = 'LHC'
