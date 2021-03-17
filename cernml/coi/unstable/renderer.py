"""Sketch of a ``Renderer`` interface for the COI."""
import typing as t

from matplotlib import pyplot
from matplotlib.figure import Figure

from ..mpl_utils import MatplotlibFigures


class Renderer:
    """Interface for types that facilitate Matplotlib rendering.

    This is an abstract base class. You should use a concrete
    implementation, e.g. :py:class:`SimpleRenderer`.
    """

    @staticmethod
    def make_figure(mode: str) -> Figure:
        """Helper method to create the correct kind of figure."""
        func = {"human": pyplot.figure, "matplotlib_figures": Figure}[mode]
        return func()

    def update(self, mode: str) -> t.Optional[MatplotlibFigures]:
        """Update the renderer's figures and return them.

        On the first call, this should initialize the renderer's
        figures. On all subsequent calls, it should reuse the figures
        and update their contents.

        Args:
            mode: The render mode. This should be either ``"human"`` or
                ``"matplotlib_figures"``.

        Returns:
            None if the render mode is ``"human"``. Otherwise, a
            sequence of all figures managed by this renderer.
        """
        raise NotImplementedError()


class SimpleRenderer(Renderer):
    """Renderer that manages a single figure.

    Args:
        update: A callback that fills the renderer's figure. Called like
            ``update(figure)``. The return value is ignored.
        title: If passed, a figure title that is used in the return
            value of ``renderer.update("matplotlib_figures")``. Unused
            in other render modes. In particular, this does not add a
            title to the figure's contents. For this, consider using
            :py:meth:`Figure.suptitle()` instead.

    This renderer should be preferred, as it is the simplest to use. It
    manages a single figure and passes it to a callback every time
    :py:meth:`update()` is called.

    If you need to do non-trivial set up for your figure, consider using
    :py:meth:`from_generator()`. For an even more concise wrapper, see
    the :py:class:`render_generator` descriptor.

    Example::

        >>> from typing import Iterator
        >>> from cernml import coi
        >>> from cernml.coi.mpl_utils import Figure
        >>> class SomePoints(coi.Problem):
        ...     metadata = {"render.modes": ["human", "matplotlib_figures"]}
        ...     def __init__(self):
        ...         self.data = np.random.uniform(size=10)
        ...         self.renderer = SimpleRenderer.from_generator(self.iter_updates)
        ...
        ...     def render(mode):
        ...         if mode in self.metadata["render.modes"]:
        ...             return self.renderer.update(mode)
        ...         return super().render(mode)
        ...
        ...     def iter_updates(self, fig: Figure) -> Iterator[None]:
        ...         # Initialization, executed on the first call to
        ...         # ``render()``.
        ...         axes = fig.subplots()
        ...         [points] = axes.plot(self.data, "o")
        ...         while True:
        ...             # Suspension point. Here, control returns to
        ...             # ``render()``. On the second call to
        ...             # ``render()``, execution continues here.
        ...             yield
        ...             # Update the plot and yield again.
        ...             points.set_ydata(self.data)
    """

    Self = t.TypeVar("Self", bound="SimpleRenderer")
    Callback = t.Callable[[Figure], None]
    Generator = t.Generator[None, Figure, None]

    def __init__(self, update: Callback, title: t.Optional[str] = None) -> None:
        self.figure: t.Optional[Figure] = None
        self._update = update
        self._title = title

    def update(self, mode: str) -> t.Optional[MatplotlibFigures]:
        if self.figure is None:
            self.figure = self.make_figure(mode)
        self._update(self.figure)
        if mode == "human":
            # In human mode, we must manually update our figure to
            # ensure that the results of `self._update` become visible.
            self.figure.show(warn=False)
            # Use draw_idle() to actually postpone drawing until the
            # next GUI pause. In `matplotlib_figures` mode, we return
            # our figure to the caller, so they are free to call draw()
            # themselves.
            self.figure.canvas.draw_idle()
            return None
        if mode == "matplotlib_figures":
            if self._title is None:
                return (self.figure,)
            return ((self._title, self.figure),)
        raise KeyError(mode)

    @classmethod
    def from_generator(
        cls: t.Type[Self],
        func: t.Callable[[Figure], Generator],
        title: t.Optional[str] = None,
    ) -> Self:
        """Create a simple renderer from a generator.

        A generator is a function that contains ``yield`` instead of
        ``return``. You can use this to make state management in your
        callback easier. See the class docstring for an example.
        """
        iterator = None

        def callback(figure: Figure) -> None:
            nonlocal iterator
            if iterator is None:
                iterator = func(figure)
                next(iterator)
            else:
                iterator.send(figure)

        return cls(callback, title=title)


T = t.TypeVar("T")  # pylint: disable=invalid-name


class render_generator(t.Generic[T]):
    """Decorator wrapper for `SimpleRenderer`.

    This is a convenience wrapper around
    :py:meth:`SimpleRenderer.from_generator()`. It automatically manages
    a :py:class:`SimpleRenderer` for you. Calling the decorated method
    will call ``renderer.update()`` instead. This keeps your ``render()``
    implementation short and avoids duplicate code in your plotting
    logic.

    For a less magical interface, see the :py:class:`SimpleRenderer`
    class itself.

    Example::

        >>> from cernml import coi
        >>> class SomePoints(coi.Problem):
        ...     metadata = {"render.modes": ["human", "matplotlib_figures"]}
        ...
        ...     def __init__(self):
        ...         self.data = np.random.uniform(size=10)
        ...
        ...     def render(mode):
        ...         if mode in self.metadata["render.modes"]:
        ...             # Manages a `SimpleRenderer` in the background and
        ...             # actually calls `renderer.update(mode)` on it.
        ...             return self.update_figure(mode)
        ...         return super().render(mode)
        ...
        ...     @render_generator
        ...     def update_figure(self, fig):
        ...         # Executed on the first call to ``render()``.
        ...         axes = fig.subplots()
        ...         [points] = axes.plot(self.data, "o")
        ...         while True:
        ...             # Return to ``render()``. When ``render()`` is
        ...             # called again, resume execution here.
        ...             yield
        ...             points.set_y_data(self.data)
    """

    # pylint: disable = too-few-public-methods
    # pylint: disable = invalid-name

    def __init__(self, func: t.Callable[[T, Figure], SimpleRenderer.Generator]) -> None:
        self.func = func
        self.__doc__ = func.__doc__
        self.attrname: t.Optional[str] = None
        self.renderer: t.Optional[SimpleRenderer] = None

    def _make_renderer(self, instance: T) -> SimpleRenderer:
        bound_method = lambda fig: self.func(instance, fig)
        return SimpleRenderer.from_generator(bound_method)

    def __set_name__(self, owner: t.Type[T], name: str) -> None:
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise TypeError(
                f"cannot assign the samer renderer to two different "
                f"names ({self.attrname!r} and {name!r})"
            )

    def __get__(
        self, instance: T, owner: t.Optional[t.Type[T]] = None
    ) -> t.Callable[[str], t.Optional[MatplotlibFigures]]:
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError(
                "cannot use renderer instance without calling __set_name__ on it"
            )
        if self.renderer is None:
            self.renderer = self._make_renderer(instance)
        return self.renderer.update
