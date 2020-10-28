#!/usr/bin/env python
"""Provide `Problem`, the most fundamental API of this package."""

import abc

__all__ = ["Problem"]


class Problem(metaclass=abc.ABCMeta):
    """Abstract base class of all problems.

    You should not derive from this class. Derive from one of the actual
    interface classes like `gym.Env` or `cernml.coi.SingleOptimizable`. This
    class exists for two purposes:

    - define which parts of the interfaces are common to all of them;
    - provide an easy way to test whether an interface is compatible with the
      generic optimization framework.

    This is an _abstract_ base class. This means even classes that don't
    inherit from it may be considered a subclass. To be considered a subclass,
    a class must merely:
    - provide a method `render()`,
    - provide a property `unwrapped`,
    - provide a class attribute `metadata` that is a mapping with at least the
      keys `render.modes` and `cern.machines`.
    """

    # Subclasses should make `metadata` just a regular dict. This is a mapping
    # proxy to prevent accidental mutation through inheritance.
    metadata = {
        "render.modes": [],
        "cern.machines": [],
    }

    @property
    def unwrapped(self):
        """Return the core problem.

        If this class is a wrapper around another problem, it should return
        that problem (recursively, if the wrapped problem is a wrapper itself).
        Otherwise, it should return itself.
        """
        return self

    @abc.abstractmethod
    def render(self, mode="human", **kwargs):
        """Render the environment.

        The set of supported modes varies per environment. (And some
        environments do not support rendering at all.) By convention, if mode
        is:
        - human: render to the current display or terminal and return nothing.
          Usually for human consumption.
        - rgb_array: Return an numpy.ndarray with shape (x, y, 3), representing
          RGB values for an x-by-y pixel image, suitable for turning into a
          video.
        - ansi: Return a string (str) or StringIO.StringIO containing a
          terminal-style text representation. The text can include newlines and
          ANSI escape sequences (e.g. for colors).

        Note:
            Make sure that your class's metadata 'render.modes' key includes
            the list of supported modes. It's recommended to call super()
            in implementations to use the functionality of this method.

        Args:
            mode (str): the mode to render with

        Example:

            class MyEnv(Env):
                metadata = {'render.modes': ['human', 'rgb_array']}
                def render(self, mode='human'):
                    if mode == 'rgb_array':
                        # return RGB frame suitable for video
                        return np.array(...)
                    elif mode == 'human':
                        # pop up a window and render
                        ...
                    else:
                        # just raise an exception
                        super(MyEnv, self).render(mode=mode)
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, other):
        if cls is Problem:
            return _check_methods(other, "metadata", "render", "unwrapped")
        return NotImplemented


def _check_methods(C, *methods):
    # pylint: disable = invalid-name
    mro = C.__mro__
    for method in methods:
        for B in mro:
            if method in B.__dict__:
                if B.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True
