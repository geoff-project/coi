#!/usr/bin/env python
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
    kwargs: Optional[Mapping[str, Any]] = None
):
    """Register a new environment in the global registry.

    Args:
        id: The ID under which the environment can be looked up again. It
            should adhere to the following format:

                (module):(env-name)-v(version)

            where _module_ is the name of the defining module (may contain
            periods), _env-name_ is the name and _version_ is a non-negative
            integer.

    Keyword-only args:
        entry_point: Either a callable or a string of the following format:

                (module):(name)

            that points to a callable. Upon instantiation, this callable will
            be called as `entry_point(**kwargs)`, i.e. it is guaranteed not to
            be called with any positional arguments.

            Upon instantiation, the registry spec of an object will be added to
            it as `obj.unwrapped.spec`. That means whatever object is returned
            by `entry_point` _must_ have an attribute `unwrapped` that points
            to itself or its core attribute. (like `gym.Env.unwrapped`)
        nondeterministic: A flag that should be True if an environment behaves
            non-deterministically _even after_ seeding.
        max_episode_steps: The maximum number of steps after which an episode
            is forcefully ended. If this parameter is not None, the return
            value of `entry_point` is wrapped in a `gym.wrappers.TimeLimit`
            upon instantiation.
        kwargs: Any further arguments that should be passed to `entry_point`.
            This should contain all required arguments of `entry_point` so that
            a call `make(the_id)` will always succeed.
    """
    # pylint: disable = invalid-name, redefined-builtin
    return registry.register(
        id,
        entry_point=entry_point,
        nondeterministic=nondeterministic,
        max_episode_steps=max_episode_steps,
        kwargs=kwargs,
    )


def make(id: str, **kwargs) -> Any:
    """Instantiate a registered environment.

    Args:
        id: The name under which the environment has been registered.

    All further keyword arguments are forwarded to the environment constructor.

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
        An `EnvSpec` object that contains the arguments with which the
        environment has been registered.

    Raises:
        gym.error.Error if the given environment cannot be found.
    """
    # pylint: disable = invalid-name, redefined-builtin
    return registry.spec(id)
