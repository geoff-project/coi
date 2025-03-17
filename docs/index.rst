.. SPDX-FileCopyrightText: 2020 - 2024 CERN
.. SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

COI — Common Optimization Interfaces
====================================

*Geoff* (Generic Optimization Framework & Frontend) is the project of bringing
numerical optimization, machine learning and reinforcement learning to the
operation of particle accelerators. It consists of several packages, usually
under the prefix "cernml".

This package defines *Common Optimization Interfaces* that facilitate using
numerical optimization and reinforcement learning (RL) on the same optimization
problems. This makes it possible to unify both approaches into a generic
optimization application.

**To get started**, please read :doc:`guide/quickstart`.

The :doc:`cernml-coi-utils <utils:index>` package provides many additional
features that complement the COIs.

This repository can be found online on CERN's Gitlab_.

.. _Gitlab: https://gitlab.cern.ch/geoff/cernml-coi/

.. toctree::
    :maxdepth: 2

    tutorials/index
    guide/index
    examples/index
    api/index
    roadmap
    changelog
