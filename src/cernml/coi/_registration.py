"""The registry used by CERNML-COI."""

from typing import Any, Callable, Mapping, Optional, Union

from gym.envs.registration import EnvRegistry, EnvSpec

registry = EnvRegistry()


def register(
    id: str,
    *,
    entry_point: Union[str, Callable],
    nondeterministic: bool = False,
    max_episode_steps: Optional[int] = None,
    kwargs: Optional[Mapping[str, Any]] = None,
) -> None:
    """Register a new environment in the global registry.

    Args:
        id: The ID under which the environment can be looked up again.
            It should adhere to one of the two following formats::

                (env-name)-v(version)
                (module):(env-name)-v(version)

            where *module* is the name of the defining module (may
            contain periods), *env-name* is the name and *version* is a
            non-negative integer.

    Keyword Args:
        entry_point: Either a callable or a string of the following
            format::

                (module):(name)

            that points to a callable. Upon instantiation, this callable
            will be called as ``entry_point(**kwargs)``, i.e. it is
            guaranteed not to be called with any positional arguments.

        nondeterministic: A flag that should be True if an environment
            behaves non-deterministically *even after* seeding.

        max_episode_steps: The maximum number of steps after which an
            episode is forcefully ended. If this parameter is not None,
            the return value of *entry_point* is wrapped in a
            :class:`gym.wrappers.TimeLimit` upon instantiation.

        kwargs: Any further arguments that should be passed to
            *entry_point*. This should contain all required arguments so
            that a call ``make(the_id)`` will always succeed.

    Note:
        After instantiating a registered problem, the registry spec of
        an object will be added to it as ``obj.unwrapped.spec``. That
        means whatever object is returned by *entry_point* *must* have
        an attribute `~Problem.unwrapped` that points to itself or any
        wrapped problem.
    """
    # pylint: disable = invalid-name, redefined-builtin
    registry.register(
        id,
        entry_point=entry_point,
        nondeterministic=nondeterministic,
        max_episode_steps=max_episode_steps,
        kwargs=kwargs,
    )


def make(id: str, **kwargs: Any) -> Any:
    """Instantiate a registered environment.

    Args:
        id: The name under which the environment has been registered.

    All further keyword arguments are forwarded to the environment
    constructor.

    Returns:
        The instantiated object.
    """
    # pylint: disable = invalid-name, redefined-builtin
    return registry.make(id, **kwargs)


def spec(id: str) -> EnvSpec:
    """Return the spec of a registered environment.

    Args:
        id: The name under which the environment has been registered.

    Returns:
        An :class:`~gym.envs.registration.EnvSpec` object that contains
        the arguments with which the problem has been registered.

    Raises:
        gym.error.Error: if the given environment cannot be found.
    """
    # pylint: disable = invalid-name, redefined-builtin
    return registry.spec(id)
