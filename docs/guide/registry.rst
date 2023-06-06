..
    SPDX-FileCopyrightText: 2020-2023 CERN
    SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Making Your Code Findable
=========================

This package provides an *registry* similar to the one provided by Gym itself.
Every optimization problem that wants to be usable in a generic context should
register itself to it. The usage is as follows:

.. code-block:: python

    from cernml.coi import OptEnv, register

    class MyEnv(OptEnv):
        ...

    register('mypackage:MyEnv-v0', entry_point=MyEnv)

This makes your environment known to "the world" and an environment management
application that imports your package knows how to find and interact with your
environment.
