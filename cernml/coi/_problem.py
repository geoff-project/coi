#!/usr/bin/env python
"""Provide `Problem`, the most fundamental API of this package."""

from abc import ABCMeta
from types import MappingProxyType
from typing import Any, Mapping

from ._abc_helpers import check_methods as _check_methods


class Problem(metaclass=ABCMeta):
    """Abstract base class of all problems.

    You should not derive from this class. Derive from one of the actual
    interface classes like :py:class:`gym.Env` or
    :py:class:`SingleOptimizable`. This class exists for two purposes:

    - define which parts of the interfaces are common to all of them;
    - provide an easy way to test whether an interface is compatible
      with the generic optimization framework.

    This is an *abstract* base class. This means even classes that don't
    inherit from it may be considered a subclass. To be considered a
    subclass, a class must merely:

    - provide a method :py:meth:`render()`,
    - provide a property :py:attr:`unwrapped`,
    - provide a class attribute :py:attr:`metadata` that is a
      mapping with at least the keys `"render.modes"` and
      `"cern.machines"`.

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
                :py:meth:`render()`.
            ``"cern.machine"``
                The accelerator that an optimization problem is
                associated with. This must be a value of type
                :py:class:`Machine`.
            ``"cern.japc"``
                A boolean flag indicating whether the problem's
                constructor expects an argument named ``japc`` of type
                :py:class:`pyjapc.PyJapc`.

            Additionally, all keys that start with ``"cern."`` are
            reserved for future use.
    """

    # Subclasses should make `metadata` just a regular dict. This is a
    # mapping proxy to prevent accidental mutation through inheritance.
    metadata: Mapping[str, Any] = MappingProxyType(
        {
            "render.modes": [],
            "cern.machines": [],
        }
    )

    @property
    def unwrapped(self) -> "Problem":
        """Return the core problem.

        By default, this just returns ``self``. However, if this class
        is a wrapper around another problem (which might, in turn, also
        be a wrapper), it should return that problem recursively.

        Example:

            >>> class Concrete(Problem):
            ...     pass
            >>> class Wrapper(Problem):
            ...     def __init__(self, wrapped):
            ...         self._wrapped = wrapped
            ...     @property
            ...     def unwrapped(self):
            ...         return self._wrapped.unwrapped
            >>> inner = Concrete()
            >>> outer = Wrapper(inner)
            >>> inner.unwrapped is inner
            True
            >>> outer.unwrapped is inner
            True
        """
        return self

    def render(self, mode: str = "human") -> Any:
        """Render the environment.

        Args:
            mode: the mode to render with. Must be a member of
                ``self.metadata["render.modes"]``.

        The set of supported modes varies. Some problems do not support
        rendering at all. The following modes are understood by this
        package:

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
            Return a ``str`` or ``io.StringIO`` containing a
            terminal-style text representation. The text can include
            newlines and ANSI escape sequences (e.g. for colors).
        ``"matplotlib_figures"``
            Render to one or more `matplotlib.figure.Figure` objects.
            This should return all figures whose contents have changed.
            The following return types are allowed:

            - a list containing :py:class`Figure` objects and ``(str,
              Figure)`` tuples;
            - a mapping with ``str`` keys and :py:class:`Figure` values.

            Strings are interpreted as window titles for their
            associated figure.

        Example:

            >>> from gym import Env
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
            ``"render.modes"`` key of your :py:attr:`metadata`. It's
            recommended to call ``super()`` in implementations to use
            the functionality of this method.
        """
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, other: type) -> Any:
        if cls is Problem:
            return _check_methods(other, "metadata", "render", "unwrapped")
        return NotImplemented
