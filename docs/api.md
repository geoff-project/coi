# API Reference

## Common Optimization Interfaces

```{eval-rst}
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

.. class:: gym.Env

    Bases: :class:`cernml.coi.Problem`

    The main OpenAI Gym class. It encapsulates an environment with arbitrary
    behind-the-scenes dynamics. An environment can be partially or fully
    observed.

    The main API methods that users of this class need to know are:

    - :meth:`step()`
    - :meth:`reset()`
    - :meth:`~cernml.coi.Problem.render()`
    - :meth:`~cernml.coi.Problem.close()`
    - :meth:`seed()`

    And set the following attributes:

    .. attribute:: action_space

        The Space object corresponding to valid actions

    .. attribute:: observation_space

        The Space object corresponding to valid observations

    .. attribute:: reward_range

        A tuple corresponding to the min and max possible rewards

    .. note::
        A default reward range set to `[-inf,+inf]` already exists. Set
        it if you want a narrower range.

    The methods are accessed publicly as "step", "reset", etc ...

    .. method:: reset() -> numpy.ndarray

        Resets the environment to an initial state and returns an initial
        observation.

        Note that this function should not reset the environment’s random
        number generator(s); random variables in the environment’s state should
        be sampled independently between multiple calls to :meth:`reset()`. In
        other words, each call of :meth:`reset()` should yield an environment
        suitable for a new episode, independent of previous episodes.

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

        When end of
        episode is reached, you are responsible for calling :meth:`reset()`
        to reset this environment's state.
        Accepts an action and returns a tuple (observation, reward, done, info).

        :param action: An action provided by the agent.

        :return: A tuple of four elements:

            :observation:
                Agent's observation of the current environment.
            :reward:
                Amount of reward returned after previous action.
            :done:
                Whether the episode has ended, in which case further
                :meth:`step()` calls will return undefined results.
            :info:
                Contains auxiliary diagnostic information (helpful for
                debugging, and sometimes learning).

.. class:: gym.GoalEnv

    Bases: :class:`gym.Env`

    A goal-based environment. It functions just as any regular OpenAI Gym
    environment but it imposes a required structure on the
    :attr:`observation_space`. More concretely, the observation space is
    required to contain at least three elements, namely *observation*,
    *desired\_goal*, and *achieved\_goal*. Here, *desired\_goal* specifies the
    goal that the agent should attempt to achieve. *achieved\_goal* is the goal
    that it currently achieved instead. The *observation* contains the actual
    observations of the environment as per usual.

    .. method:: compute_reward(achieved_goal: numpy.ndarray, desired_goal: numpy.ndarray, info: dict) -> float

        Compute the step reward. This externalizes the reward function and
        makes it dependent on a desired goal and the one that was achieved. If
        you wish to include additional rewards that are independent of the
        goal, you can include the necessary values to derive it in *info* and
        compute it accordingly.

        :param achieved_goal: The goal that was achieved during execution.
        :param desired_goal: The desired goal that we asked the agent to
            attempt to achieve.
        :param info: An info dictionary with additional information.

        :return: The reward that corresponds to the provided achieved goal
            w.r.t. to the desired goal.

        .. note::

            The following should always hold true::

                ob, reward, done, info = env.step()
                assert reward == env.compute_reward(ob['achieved_goal'], ob['goal'], info)
```

## Spaces

```{eval-rst}
.. class:: gym.spaces.Space(shape=None, dtype=None)

    Bases: :class:`object`

    Defines the observation and action spaces, so you can write generic code
    that applies to any Env. For example, you can choose a random action.

    .. warning::

        Custom observation and action spaces can inherit from this class.
        However, most use cases should be covered by the existing space classes
        (e.g. :class:`~gym.spaces.Box`, :class:`~gym.spaces.Discrete`, etc.),
        and container classes (:class:`~gym.spaces.Tuple` and
        :class:`~gym.spaces.Dict`). Note that parametrized probability
        distributions (through the :meth:`sample()` method), and batching
        functions (in :class:`gym.vector.VectorEnv`), are only well-defined for
        instances of spaces provided in gym by default. Moreover, some
        implementations of Reinforcement Learning algorithms might not handle
        custom spaces properly. Use custom spaces with care.

    .. method:: contains(x)

        Return boolean specifying if *x* is a valid member of this space

    .. method:: from_jsonable(sample_n)

        Convert a JSONable data type to a batch of samples from this space.

    .. method:: sample()

        Randomly sample an element of this space. Can be uniform or non-uniform
        sampling based on boundedness of space.

    .. method:: seed(seed=None)

        Seed the PRNG of this space.

    .. method:: to_jsonable(sample_n)

        Convert a batch of samples from this space to a JSONable data type.

    .. method:: np_random
        :property:

        Lazily seed the rng since this is expensive and only needed if sampling
        from this space.

.. class:: gym.spaces.Box(low, high, shape=None, dtype=<class 'numpy.float32'>)

    Bases: :class:`gym.spaces.Space`

    A (possibly unbounded) box in ℝⁿ. Specifically, a Box represents the
    Cartesian product of *n* closed intervals. Each interval has the form of
    one of [*a*, *b*], (-∞, *b*], [*a*, ∞), or (-∞, ∞).

    There are two common use cases:

    - Identical bound for each dimension::

        >>> Box(low=-1.0, high=2.0, shape=(3, 4), dtype=np.float32)
        Box(3, 4)

    - Independent bound for each dimension::

        >>> Box(low=np.array([-1.0, -2.0]), high=np.array([2.0, 4.0]))
        Box(2,)

      If *shape* or *dtype* are not specified in this case, they are deduced
      from the *low* and *high* arrays.

.. class:: gym.spaces.Dict(spaces=None, **kwargs)

    Bases: :class:`gym.spaces.Space`

    A dictionary of simpler spaces.

    Example usage::

        self.observation_space = spaces.Dict({
            "position": spaces.Discrete(2),
            "velocity": spaces.Discrete(3)
        })

    Example usage (nested)::

        self.nested_observation_space = spaces.Dict({
            "sensors": spaces.Dict({
                "position": spaces.Box(low=-100, high=100, shape=(3,)),
                "velocity": spaces.Box(low=-1, high=1, shape=(3,)),
                "front_cam": spaces.Tuple((
                    spaces.Box(low=0, high=1, shape=(10, 10, 3)),
                    spaces.Box(low=0, high=1, shape=(10, 10, 3)),
                )),
                "rear_cam": spaces.Box(low=0, high=1, shape=(10, 10, 3)),
            }),
            "ext_controller": spaces.MultiDiscrete((5, 2, 2)),
            "inner_state":spaces.Dict({
                "charge": spaces.Discrete(100),
                "system_checks": spaces.MultiBinary(10),
                "job_status": spaces.Dict({
                    "task": spaces.Discrete(5),
                    "progress": spaces.Box(low=0, high=100, shape=()),
                })
            })
        })
```

## Configuration of Problems

```{eval-rst}
.. autoclass:: cernml.coi.Configurable
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.Config
    :members: add, validate, validate_all
    :show-inheritance:
```

## Problem Registry

```{eval-rst}
.. autofunction:: cernml.coi.register

.. autofunction:: cernml.coi.make

.. autofunction:: cernml.coi.spec

.. autodata:: cernml.coi.registry

.. autoclass:: gym.envs.registration.EnvRegistry
    :members:
    :show-inheritance:
```

## Separable Environments

```{eval-rst}
.. autoclass:: cernml.coi.SeparableEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SeparableGoalEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.OptEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.OptGoalEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SeparableOptEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SeparableOptGoalEnv
    :members:
    :show-inheritance:
```

## Problem checkers

```{eval-rst}
.. autofunction:: cernml.coi.check

.. autofunction:: cernml.coi.checkers.check_problem

.. autofunction:: cernml.coi.checkers.check_single_optimizable

.. autofunction:: cernml.coi.checkers.check_env
```

## Matplotlib Utilities

The following functions and types are only available if the
[Matplotlib](https://matplotlib.org/) is importable.

```{eval-rst}
.. autofunction:: cernml.coi.mpl_utils.iter_matplotlib_figures

.. autoclass:: cernml.coi.unstable.renderer.Renderer
    :members:
    :show-inheritance:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autoclass:: cernml.coi.unstable.renderer.SimpleRenderer
    :members:
    :show-inheritance:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autodecorator:: cernml.coi.unstable.renderer.render_generator

    .. warning::
        This decorator is considered *unstable* and may change arbitrarily
        between minor releases.
```

## Cancellation

```{eval-rst}
.. automodule:: cernml.coi.unstable.cancellation
    :members:

    .. warning::
        This module is considered *unstable* and may change arbitrarily
        between minor releases.
```

## PyJapc Utilities

The following functions and types are only available if
[PyJapc](https://gitlab.cern.ch/scripting-tools/pyjapc) is importable.

```{eval-rst}
.. autofunction:: cernml.coi.unstable.japc_utils.monitoring

    .. warning::
        This function is considered *unstable* and may change arbitrarily
        between minor releases.

.. autofunction:: cernml.coi.unstable.japc_utils.subscriptions

    .. warning::
        This function is considered *unstable* and may change arbitrarily
        between minor releases.

.. autofunction:: cernml.coi.unstable.japc_utils.subscribe_stream

    .. warning::
        This function is considered *unstable* and may change arbitrarily
        between minor releases.

.. autoclass:: cernml.coi.unstable.japc_utils.ParamStream
    :members:
    :inherited-members:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autoclass:: cernml.coi.unstable.japc_utils.ParamGroupStream
    :members:
    :inherited-members:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autoclass:: cernml.coi.unstable.japc_utils.Header
    :members:
    :undoc-members:
    :show-inheritance:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autoexception:: cernml.coi.unstable.japc_utils.StreamError

    .. warning::
        This exception is considered *unstable* and may change arbitrarily
        between minor releases.

.. autoexception:: cernml.coi.unstable.japc_utils.JavaException

    .. warning::
        This exception is considered *unstable* and may change arbitrarily
        between minor releases.
```
