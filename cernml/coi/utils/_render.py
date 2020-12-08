#!/usr/bin/env python

"""Utilities for `Problem.render()`."""

import typing as t

from matplotlib.figure import Figure

FigureWithTitle = t.Tuple[str, Figure]
FigureSpec = t.Union[Figure, FigureWithTitle]
FiguresCollection = t.Union[t.Mapping[str, Figure], t.Iterable[FigureSpec]]


def iter_matplotlib_figures(figures: FiguresCollection) -> t.Iterator[FigureWithTitle]:
    """Iterate over the result of `Problem(mode='matplotlib_figures')`.

    Problem authors are given a lot of freedom in what they return from
    `render()`. This method unifies all possible return types of
    `render() and always returns an iterator over title-figure tuples.
    If a figure does not have a title, the empty string is yielded.

    Examples:

        >>> class Figure:
        ...     def __repr__(self) -> str:
        ...         return "Figure()"
        ...
        >>> def print_matplotlib_figures(figures):
        ...     for t, f in iter_matplotlib_figures(figures):
        ...         print(f"{t!r}: {f!r}")
        ...
        >>> # Lists of figures:
        >>> print_matplotlib_figures([Figure(), Figure()])
        '': Figure()
        '': Figure()
        >>> # Arbitrary iterables of figures:
        >>> print_matplotlib_figures(Figure() for _ in range(3))
        '': Figure()
        '': Figure()
        '': Figure()
        >>> # Lists of title-figure tuples OR figures:
        >>> print_matplotlib_figures([["Foo", Figure()], ("Bar", Figure()), Figure()])
        'Foo': Figure()
        'Bar': Figure()
        '': Figure()
        >>> # Mappings from titles to figures:
        >>> print_matplotlib_figures({"Foo": Figure(), "Bar": Figure()})
        'Foo': Figure()
        'Bar': Figure()
    """
    if hasattr(figures, "items"):
        yield from iter(t.cast(t.Mapping[str, Figure], figures).items())
    else:
        for item in figures:
            # Check if `item` is iterable. If yes, attempt to unpack.
            # This is faster than catching `TypeError` by a factor of
            # eight.
            if hasattr(item, "__iter__") or hasattr(item, "__getitem__"):
                title, figure = t.cast(t.Tuple[str, Figure], item)
            else:
                title, figure = "", item
            yield title, figure
