# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provide `Problem`, the most fundamental API of this package."""

import typing as t
from abc import ABCMeta
from types import MappingProxyType

import numpy as np
from gymnasium.envs.registration import EnvSpec
from gymnasium.utils import seeding

from ._abc_helpers import AttrCheckProtocol
from ._machine import Machine

if t.TYPE_CHECKING:
    from typing_extensions import Self

__all__ = (
    "BaseProblem",
    "HasNpRandom",
    "Problem",
)


class HasNpRandom(t.Protocol):
    """Protocol for classes that manage their own RNG.

    This abstracts out the `gymnasium.Env.np_random` property. The
    `Problem` protocol does not depend on it, but the :term:`abstract
    base class` `BaseProblem` subclasses it as a mixin for convenience.
    """

    _np_random: np.random.Generator | None = None

    @property
    def np_random(self) -> np.random.Generator:
        """Returns the environment's internal :attr:`_np_random`.

        if `_np_random` is not set yet, this will initialize it with
        a random seed.

        Returns:
            Instances of `np.random.Generator`
        """
        if self._np_random is None:
            self._np_random, _ = seeding.np_random()
        return self._np_random

    @np_random.setter
    def np_random(self, value: np.random.Generator) -> None:
        self._np_random = value


@t.runtime_checkable
class Problem(AttrCheckProtocol, t.Protocol):
    """Root protocol for all optimization problems.

    Do not not directly subclass this protocol. Instead, derive from one
    of its subclasses like `~gym.Env` or `SingleOptimizable`. This class
    exists for two purposes:

    - define which parts of the interfaces are common to all of them;
    - provide an easy way to test whether an interface is compatible
      with the generic optimization framework.

    This is a `~typing.Protocol`. This means even classes that don't
    inherit from it may be considered a subclass. To be considered
    a subclass, a class must merely:

    - provide the methods `render()`, `close()` and
      `get_wrapper_attr()`;
    - provide a dynamic property `unwrapped`;
    - provide the attributes `render_mode` and `spec`.

    Attributes:
        metadata: Capabilities and behavior of this problem.

            This must be a class-level constant attribute. It must be a
            mapping with string-type keys. Instances must not
            dynamically modify or overwrite this dict. It communicates
            fundamental properties of the class and how a host
            application can use it.

            The following keys are defined and understood by this
            package:

            ``"render.modes"``
                The render modes that the optimization problem
                understands. Standard render modes are documented under
                `render()`.
            ``"cern.machine"``
                The accelerator that an optimization problem is
                associated with. This must be a value of type `Machine`.
            ``"cern.japc"``
                A boolean flag indicating that the problem's constructor
                expects an argument named *japc* of type
                :class:`~pyjapc.PyJapc`. Enable it if your class
                performs any machine communication via JAPC. Do not
                create your own :class:`~pyjapc.PyJapc` instance. Among
                other things, this ensures that the correct timing
                selector is set.
            ``"cern.cancellable"``
                A boolean flag indicating that the problem's constructor
                expects an argument named *cancellation_token* of type
                `~cernml.coi.cancellation.Token`. Enable it if your
                class ever enters any long-running loops that the user
                may want to interrupt. A classic example is the
                acquisition and validation of cycle-bound data.

            Additionally, all keys that start with ``"cern."`` are
            reserved for future use.
        render_mode: TODO
        spec: TODO
    """

    # Subclasses should make `metadata` just a regular dict. This is
    # a mapping proxy here to prevent accidental mutation through
    # inheritance.
    metadata: dict[str, t.Any] = t.cast(
        dict[str, t.Any],
        MappingProxyType(
            {
                "render.modes": [],
                "cern.machine": Machine.NO_MACHINE,
                "cern.japc": False,
                "cern.cancellable": False,
            }
        ),
    )

    render_mode: str | None = None
    spec: EnvSpec | None = None

    def close(self) -> None:
        """Perform any necessary cleanup.

        This method may be overridden to perform cleanup that does not
        happen automatically. Examples include stopping JAPC
        subscriptions or canceling any spawned threads. By default, this
        method does nothing.

        After this method has been called, no further methods may be
        called on the problem, with the following exceptions:

        - `unwrapped` must continue to behave as expected;
        - calling `close()` again should do nothing.
        """

    @property
    def unwrapped(self) -> "Problem":
        """Return the core problem.

        By default, this just returns *self*. However, if this class
        is a wrapper around another problem (which might, in turn, also
        be a wrapper), it should return that problem recursively.

        This exists to support the :class:`gym.Wrapper` design pattern.

        Example:

            >>> class Concrete(Problem):
            ...     pass
            >>> class Wrapper(Problem):
            ...     def __init__(self, wrapped):
            ...         self._wrapped = wrapped
            ...     @property
            ...     def unwrapped(self):
            ...         # Note the recursion.
            ...         return self._wrapped.unwrapped
            >>> inner = Concrete()
            >>> outer = Wrapper(inner)
            >>> inner.unwrapped is inner
            True
            >>> outer.unwrapped is inner
            True
        """
        return self

    def render(self) -> t.Any:
        """Render the environment.

        Args:
            mode: the mode to render with. Must be a member of
                ``self.metadata["render.modes"]``.

        The set of supported modes varies. Some problems do not support
        rendering at all. The following modes have a standardized
        meaning:

        ``"human"``
            Render to the current display or terminal and return
            nothing. Usually for human consumption. Valid
            implementations open a Matplotlib or Pyglet window and
            return immediately.
        ``"rgb_array"``
            Return an numpy.ndarray with shape ``(x, y, 3)``,
            representing RGB values for an *x*-by-*y* pixel image,
            suitable for turning into a video.
        ``"ansi"``
            Return a `str` or `io.StringIO` containing a terminal-style
            text representation. The text can include newlines and ANSI
            escape sequences (e.g. for colors).
        ``"matplotlib_figures"``
            Render to one or more :class:`~matplotlib.figure.Figure`
            objects. This should return all figures whose contents have
            changed. The following return types are allowed:

            - a single :class:`~matplotlib.figure.Figure` object;
            - an iterable of bare :class:`~matplotlib.figure.Figure`
              objects or 2-tuples of `str` and
              :class:`~matplotlib.figure.Figure` or both;
            - a mapping with `str` keys and
              :class:`~matplotlib.figure.Figure` values.

            Strings are interpreted as window titles for their
            associated figure.

        Example:

            >>> from gymnasium import Env
            >>> class MyEnv(Env):
            ...     metadata = {'render.modes': ['human', 'rgb_array']}
            ...     def render(self, mode='human'):
            ...         if mode == 'rgb_array':
            ...             # Return RGB frame suitable for video.
            ...             return np.array(...)
            ...         if mode == 'human':
            ...             # Pop up a window and render.
            ...             pyplot.plot(...)
            ...             pyplot.show()
            ...             return None
            ...         # just raise an exception
            ...         return super().render(mode)

        Note:
            Make sure to declare all modes that you support in the
            ``"render.modes"`` key of your `metadata`. It's recommended
            to call `super` in implementations to use the functionality
            of this method.
        """
        # pylint: disable = unused-argument
        # Make PyLint realize that this method is not abstract. We do
        # allow people to not override this method in their subclass.
        # However, PyLint thinks that any method that raises
        # NotImplementedError should be overridden.
        assert True
        raise NotImplementedError

    def get_wrapper_attr(self, name: str) -> t.Any:
        """Gets the attribute `name` from the environment."""
        return getattr(self, name)


@Problem.register
class BaseProblem(HasNpRandom, metaclass=ABCMeta):
    """ABC that implements the `Problem` protocol.

    Subclassing this :term:`abstract base class` instead of `Problem`
    directly comes with a few advantages for convenience:

    - an `~object.__init__()` method that ensures that the `render_mode`
      attribute is set correctly;
    - :term:`context manager` methods that ensure that `close()` is
      called when using the problem in a :keyword:`with` statement;
    - the attribute `~HasNpRandom.np_random` as an exclusive and
      seedable `~numpy.random` number generator.

    To check whether an object satisfies the `Problem` protocol, use the
    dedicated function `is_problem()`. Alternatively, you may also call
    ``isinstance(obj.unwrapped, Problem)``. Do not use this class for
    such checks!

    Equivalent base classes also exist for the other interfaces.

    See Also:
        `BaseFunctionOptimizable`, `BaseSingleOptimizable`, `Env`
    """

    # pylint: disable = missing-function-docstring
    metadata: dict[str, t.Any] = t.cast(
        dict[str, t.Any],
        MappingProxyType(
            {
                "render.modes": [],
                "cern.machine": Machine.NO_MACHINE,
                "cern.japc": False,
                "cern.cancellable": False,
            }
        ),
    )
    render_mode: str | None = None
    spec: EnvSpec | None = None

    def __init__(self, render_mode: str | None = None) -> None:
        if render_mode is not None:
            modes = self.metadata.get("render.modes", ())
            if render_mode not in modes:
                raise ValueError(
                    f"invalid render mode: expected one of {modes}, "
                    f"got {render_mode!r}"
                )
        self.render_mode = render_mode

    def __enter__(self) -> "Self":
        return self

    # pylint: disable = useless-return
    def __exit__(self, *args: object) -> bool | None:
        self.close()
        return None

    # pylint: enable = useless-return

    def close(self) -> None:
        return None

    def render(self) -> t.Any:
        assert True
        raise NotImplementedError

    @property
    def unwrapped(self) -> Problem:
        return self

    def get_wrapper_attr(self, name: str) -> t.Any:
        return getattr(self, name)
