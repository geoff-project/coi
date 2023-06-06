..
    SPDX-FileCopyrightText: 2020-2023 CERN
    SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

The Configurable Interface
==========================

.. autoclass:: cernml.coi.Configurable
    :show-inheritance:

    .. automethod:: get_config
    .. automethod:: apply_config

.. autoclass:: cernml.coi.Config
    :show-inheritance:

    .. automethod:: add
    .. automethod:: extend
    .. automethod:: validate
    .. automethod:: validate_all
    .. automethod:: fields
    .. automethod:: get_field_values

.. autoclass:: cernml.coi.Config.Field
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.ConfigValues

.. autoexception:: cernml.coi.BadConfig

.. autoexception:: cernml.coi.DuplicateConfig
