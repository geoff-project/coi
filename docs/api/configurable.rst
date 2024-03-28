..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

The Configurable Interface
==========================

.. automodule:: cernml.coi.configurable
    :no-members:

.. currentmodule:: cernml.coi

.. autoclass:: Configurable

.. autoclass:: Config
    :exclude-members: Field

.. autoclass:: cernml.coi.Config.Field

.. autoclass:: ConfigValues

.. autoexception:: BadConfig

.. autoexception:: DuplicateConfig

Advanced Configurable Features
------------------------------

.. currentmodule:: cernml.coi.configurable

.. autofunction:: deduce_type

.. autoclass:: StrSafeBool
    :special-members: __call__

.. data:: AnyBool
    :type: typing.TypeVar

    The generic type variable of `StrSafeBool`. Must be either `bool` or
    `numpy.bool_`.
