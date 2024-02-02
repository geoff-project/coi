..
    SPDX-FileCopyrightText: 2016 OpenAI (https://openai.com)
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: MIT AND (GPL-3.0-or-later OR EUPL-1.2+)

Common Optimization Interfaces
==============================

.. autoclass:: cernml.coi.Constraint

.. autoclass:: cernml.coi.Machine
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: cernml.coi.Problem
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SingleOptimizable
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.FunctionOptimizable
    :members:
    :show-inheritance:

.. class:: gym.Env
   :canonical: gym.core.Env

    Bases: `cernml.coi.Problem`

    The main OpenAI Gym class. It encapsulates an environment with arbitrary
    behind-the-scenes dynamics. An environment can be partially or fully
    observed.

    The main API methods that users of this class need to know are:

    - `step()`
    - `reset()`
    - `~cernml.coi.Problem.render()`
    - `~cernml.coi.Problem.close()`
    - `seed()`

    And set the following attributes:

    .. attribute:: action_space

        The Space object corresponding to valid actions

    .. attribute:: observation_space

        The Space object corresponding to valid observations

    .. attribute:: reward_range

        A tuple corresponding to the min and max possible rewards

    .. note::
        A default reward range set to ``[-inf,+inf]`` already exists. Set
        it if you want a narrower range.

    The methods are accessed publicly as "step", "reset", etc ...

    .. method:: reset() -> numpy.ndarray

        Resets the environment to an initial state and returns an initial
        observation.

        Note that this function should not reset the environment’s random
        number generator(s); random variables in the environment’s state should
        be sampled independently between multiple calls to `reset()`. In other
        words, each call of `reset()` should yield an environment suitable for
        a new episode, independent of previous episodes.

        :return: The initial observation.

    .. method:: seed(seed=None) -> List[int]

        Sets the seed for this env’s random number generator(s).

        .. note::
            Some environments use multiple pseudorandom number generators. We
            want to capture all such seeds used in order to ensure that there
            aren't accidental correlations between multiple generators.


        :return: The list of seeds used in this env's random number generators.
            The first value in the list should be the "main" seed, or the value
            which a reproducer should pass to 'seed'. Often, the main seed
            equals the provided 'seed', but this won't be true if *seed=None*,
            for example.

    .. method:: step(action: numpy.ndarray) -> Tuple[numpy.ndarray, float, bool, dict]

        Run one timestep of the environment's dynamics.

        When end of episode is reached, you are responsible for calling
        `reset()` to reset this environment's state. Accepts an action and
        returns a tuple (observation, reward, done, info).

        :param action: An action provided by the agent.

        :return: A tuple of four elements:

            :observation:
                Agent's observation of the current environment.
            :reward:
                Amount of reward returned after previous action.
            :done:
                Whether the episode has ended, in which case further
                `step()` calls will return undefined results.
            :info:
                Contains auxiliary diagnostic information (helpful for
                debugging, and sometimes learning).

.. class:: gym.Wrapper

   Wraps the environment to allow a modular transformation.

   This class is the base class for all wrappers. The subclass could override
   some methods to change the behavior of the original environment without
   touching the original code.

   .. note::
      Don’t forget to call ``super().__init__(env)`` if the subclass overrides
      ``__init__()``.
