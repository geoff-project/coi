Spaces
======

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

    .. property:: np_random

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
