.. SPDX-FileCopyrightText: 2020 - 2025 CERN
.. SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Making an Optimization Configurable via GUI
===========================================

.. currentmodule:: cernml.coi

This section introduces a few useful, but less common interfaces defined by Gym
and the COI.

.. digraph:: control_flow
    :caption: Fig. 1: Sequence diagram of the Configurable API.

    newrank = true;
    node[
        shape=box,
        fontname="Open Sans",
        style="rounded, filled",
        fillcolor="white",
    ];

    subgraph cluster_user {
        label = "User";
        configure[label="Configure problem"];
        present[label="Present current values"];
        modify[label="Modify values"];
        submit[label="Submit new values"];
        end[label="Present success/failure"];
    }

    subgraph cluster_host {
        label = "Host";
        get_config[fontname="Courier New", label="problem.get_config()"];
        get_field_values[fontname="Courier New", label="config.get_field_values()"];
        validate[fontname="Courier New", label="config.validate_all(values)"];
        apply_config[fontname="Courier New", label="problem.apply_config(validated)"];
        return_host[fontname="Courier New", label="return", shape=plaintext];
    }

    subgraph cluster_plugin {
        label = "Plugin";
        make_config[fontname="Courier New", label="Config().add(…).add(…)"];
        return_config[fontname="Courier New", label="return config", shape=plaintext];
        use_config[fontname="Courier New", label="self.field = validated.field"];
        return_none[fontname="Courier New", label="return", shape=plaintext];
    }

    { rank=same; configure; get_config; make_config; }
    { rank=same; present; get_field_values; return_config; }
    { rank=same; submit; validate; }
    { rank=same; apply_config; use_config; }
    { rank=same; end; return_host; return_none; }

    configure -> get_config -> make_config;
    make_config -> return_config;
    return_config -> get_field_values -> present [style=dashed];
    present -> modify -> submit;
    submit -> validate;
    validate -> apply_config;
    apply_config -> use_config;
    use_config -> return_none;
    return_none -> return_host -> end [style=dashed];

Some `Problem` classes have several parameters that determine certain details
of how they are solved. A typical configurable parameter of environments is the
*reward objective*, i.e. the minimum reward for a step upon which an episode is
considered solved.

While these parameters can be set through the initializer, this has the problem
that it is difficult to annotate them with limits, invariants, etc.

The `Configurable` API provides a uniform way for problem authors to declare
parameters of their class that can be modified ahead of an optimization run. It
also allows specifying certain variants for each parameter. Host applications
can use this interface to present a configuration dialog to the user.

Basic Usage
-----------

Implementing the `Configurable` interface generally follows a three-step
process:

1. Define your configurable parameters in :meth:`~object.__init__()`.
2. Implement `~Configurable.get_config()` and return a `Config` object. This
   declares your configurable parameters and their invariants.
3. Implement `~Configurable.apply_config()`, which receives a `ConfigValues`
   object. Transfer each value into your object. Apply any further checks and
   raise an exception if any fail.

Take this class for example:

.. code-block:: python

    >>> from cernml import coi
    ...
    >>> class ExampleEnv(coi.Configurable):
    ...
    ...     # Step 0: Optionally accept the parameter in __init__().
    ...     def __init__(self, *, action_scale=1.0):
    ...         # Step 1: Define parameter in __init__().
    ...         self.action_scale = action_scale
    ...
    ...     def get_config(self):
    ...         # Step 2: Add parameter to the `Config` returned from
    ...         #     `get_config()`.
    ...         config = coi.Config()
    ...         config.add(
    ...             'action_scale',
    ...             self.action_scale,
    ...             label='Action scale (mrad)',
    ...             range=(0.0, 2.0),
    ...             default=1.0,
    ...         )
    ...         return config
    ...
    ...     def apply_config(self, values):
    ...         # Step 3: Transfer it from `values` to your env. Apply any
    ...         #     additional checks that are necessary.
    ...         if 0.0 < values.action_scale < 0.1:
    ...             raise coi.BadConfig(
    ...                 f"config 'action_scale' must be either 0.0 or "
    ...                 f"greater than 0.1: {values.action_scale!r}"
    ...             )
    ...         self.action_scale = values.action_scale
    ...
    >>> env = ExampleEnv()
    >>> isinstance(env, coi.Configurable)
    True

A host application may use this interface as follows:

.. code-block:: python

    >>> env = ExampleEnv()
    >>> config = env.get_config()
    >>> # Present configs to the user.
    >>> config.get_field_values()
    {'action_scale': 1.0}
    >>> # Transfer a user choice back to the env.
    >>> values = config.validate_all({"action_scale": 1.5})
    >>> values
    namespace(action_scale=1.5)
    >>> env.apply_config(values)
    >>> env.action_scale
    1.5

If either the validation or the application step fails, the host receives
an exception it can catch and show to the user:

.. code-block:: python

    >>> config.validate_all({"action_scale": 2.5})
    Traceback (most recent call last):
    ...
    BadConfig: invalid value for action_scale: 2.5
    >>> values = config.validate_all({"action_scale": 0.05})
    >>> env.apply_config(values)
    Traceback (most recent call last):
    ...
    BadConfig: config 'action_scale' must be either 0.0 or greater than 0.1:
    0.05
    >>> env.action_scale
    1.5

Nested Usage
------------

If your class consists of **multiple configurable components**, you can combine
their individual configs via `Config.extend()` as long as the names don't
overlap:

.. code-block:: python
    :emphasize-lines: 27-31

    >>> class Kicker(coi.Configurable):
    ...     def __init__(self) -> None:
    ...         self.scale = 0.1
    ...
    ...     def get_config(self) -> coi.Config:
    ...         return coi.Config().add("scale", self.scale)
    ...
    ...     def apply_config(self, values: coi.ConfigValues) -> None:
    ...         self.scale = values.scale
    ...
    >>> class LossMonitor(coi.Configurable):
    ...     def __init__(self) -> None:
    ...         self.min_reading = 1.0
    ...
    ...     def get_config(self) -> coi.Config:
    ...         return coi.Config().add("min_reading", self.min_reading)
    ...
    ...     def apply_config(self, values: coi.ConfigValues) -> None:
    ...         self.min_reading = values.min_reading
    ...
    >>> class Problem(coi.Configurable):
    ...     def __init__(self) -> None:
    ...         self.kicker = Kicker()
    ...         self.monitor = LossMonitor()
    ...
    ...     def get_config(self) -> coi.Config:
    ...         return (
    ...             coi.Config()
    ...             .extend(self.kicker.get_config())
    ...             .extend(self.monitor.get_config())
    ...         )
    ...
    ...     def apply_config(self, values: coi.ConfigValues) -> None:
    ...         self.kicker.apply_config(values)
    ...         self.monitor.apply_config(values)
    ...
    >>> problem = Problem()
    >>> config = problem.get_config()
    >>> config
    <Config: ['scale', 'min_reading']>
    >>> values = {'scale': 0.0, 'min_reading': 0.0}
    >>> values = config.validate_all(values)
    >>> problem.apply_config(values)
    >>> problem.kicker.scale
    0.0
    >>> problem.monitor.min_reading
    0.0
