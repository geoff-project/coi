..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Roadmap
=========

This page lists features that have been considered desirable for the Geoff
project and which are either being worked on or which will (at *some* point) be
worked on. As an open-source project, Geoff welcomes any external
contributions, so please feel free to reach out to the maintainers if you'd
like to see one of these features implemented!

Optimization:

- multi-objective optimization with support for PyMoo_ (or possibly DEAP_?)
- more comprehensive support for Bayesian optimization; support for Botorch_
- using recorded optimization runs to bootstrap a Bayesian optimizer
- better support for `Stable Baselines 3`_

Infrastructure:

- Configurable API based on Pydantic_ with less boilerplate and more
  declarative restrictions on the valid inputs
- plugin support for custom widgets in Configurable API
- support for recording, saving and loading optimization runs
- support for reloading specific points in an optimization run
- Memento_ API to restore initial or other points
- GUI independent of `CERN-specific widgets <accwidgets_>`_
- official publication

.. _PyMoo: https://pypi.org/project/pymoo/
.. _DEAP: https://pypi.org/project/deap/
.. _Botorch: https://pypi.org/project/botorch/
.. _Stable Baselines 3: https://pypi.org/project/stable-baselines3/
.. _Pydantic: https://pypi.org/project/pydantic/
.. _Memento: https://en.wikipedia.org/wiki/Memento_pattern
.. _accwidgets:
   https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets/
