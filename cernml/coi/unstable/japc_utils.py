"""Provide :class:`ParamStream`."""

import abc
import contextlib
import datetime
import functools
import logging
import threading
import typing as t
import warnings
from collections import deque

if t.TYPE_CHECKING:
    # pylint: disable=import-error, unused-import
    from pyjapc import PyJapc

    from . import cancellation

LOG = logging.getLogger(__name__)

warnings.warn(
    "cernml.coi.unstable.japc_utils is deprecated. "
    "Please install cernml-coi-utils and use cernml.japc_utils",
    DeprecationWarning,
)


class StreamError(Exception):
    """A logical error while operating on a stream."""


class JavaException(Exception):
    """An error occurred on the Java side."""


class Header(dict):
    """Convenience wrapper around the JAPC header.

    This is a dict for all intents and purposes, but also allows
    attribute access to the most common fields.
    """

    # pylint: disable = missing-function-docstring

    @property
    def acquisition_stamp(self) -> datetime.datetime:
        return self["acqStamp"]

    @property
    def cycle_stamp(self) -> datetime.datetime:
        return self["cycleStamp"]

    @property
    def set_stamp(self) -> datetime.datetime:
        return self["setStamp"]

    @property
    def selector(self) -> str:
        return self["selector"]

    @property
    def is_first_update(self) -> bool:
        return self["isFirstUpdate"]

    @property
    def is_immediate_update(self) -> bool:
        return self["isImmediateUpdate"]


T = t.TypeVar("T")  # pylint: disable=invalid-name
_OneOrList = t.Union[T, t.List[T]]
_Item = _OneOrList[t.Tuple[object, Header]]
_Event = t.Union[_Item, JavaException]


def _unwrap_event(event: _Event) -> _Item:
    if isinstance(event, JavaException):
        raise event
    return event


@contextlib.contextmanager
def subscriptions(japc: "PyJapc") -> "PyJapc":
    """Return a context manager for :class:`PyJapc`.

    The returned context manager simply starts all subscriptions when
    entering its context and stops all subscriptions when leaving it. It
    is neither reentrant nor reusable.

    Usage:

        >>> from pyjapc import PyJapc
        >>> def main():
        ...     japc = PyJapc()
        ...     ... # Subscribe to various parameters.
        ...     with subscriptions(japc):
        ...         ... # Subscriptions are active here.
        ...     ... # Subscriptions are stopped here.
    """
    japc.startSubscriptions()
    try:
        yield japc
    finally:
        japc.stopSubscriptions()


@contextlib.contextmanager
def monitoring(handle: T) -> t.Iterator[T]:
    """Return a context manager for JAPC subscription handles.

    The returned context manager simply starts monitoring the handle
    when entering its context and stops when leaving it. It is neither
    reentrant nor reusable.

    Usage:

        >>> from pyjapc import PyJapc
        >>> def main():
        ...     japc = PyJapc()
        ...     handle = japc.subscribeParam(...)
        ...     with monitoring(handle):
        ...         ... # Subscription is active here.
        ...     ... # Subscription are stopped here.
    """
    # Avoid annotating Java types; bringing them into scope is more of a
    # headache than it gains us.
    t.cast(t.Any, handle).startMonitoring()
    try:
        yield handle
    finally:
        t.cast(t.Any, handle).stopMonitoring()


class _BaseStream(metaclass=abc.ABCMeta):
    """A synchronized PyJapc subscription handle.

    Do not instantiate this class yourself. Use :func:`subscribe_stream`
    instead.

    This class contains the common logic of :class:`ParamStream` and
    :class:`ParamGroupStream`. The subclasses only contain thin wrapper
    methods that perform some type casting. The whole reason for this
    setup is to communicate via types whether a stream may return an
    object or a list of objects.
    """

    Self = t.TypeVar("Self", bound="_BaseStream")

    def __init__(
        self,
        japc: "PyJapc",
        name: t.Union[str, t.Iterable[str]],
        *,
        token: t.Optional["cancellation.Token"],
        maxlen: t.Optional[int],
        **kwargs: t.Any,
    ) -> None:
        self._handle = japc.subscribeParam(
            name,
            onValueReceived=self._on_value,
            onException=self._on_exception,
            getHeader=True,
            **kwargs,
        )
        self._queue: t.Deque[_Event] = deque(maxlen=maxlen)
        # If we get a token, we reuse its condition variable. This is
        # the only reasonable way to wait for _either_ a cancellation
        # _or_ a new JAPC event.
        self._token = token
        self._condition = token.wait_handle if token else threading.Condition()

    def __enter__(self: Self) -> Self:
        self.start_monitoring()
        return self

    def __exit__(self, *args: t.Any) -> None:
        self.stop_monitoring()

    @property
    def token(self) -> t.Optional["cancellation.Token"]:
        """The stream's cancellation token, if any.

        While the stream is inactive (``self.monitoring is False``), the
        token may be replaced. This may be useful to restart the stream
        after a cancellation.

        Raises:
            StreamError: If attempting to set the token while the stream
                is monitoring its parameter. This is to prevent
                hard-to-track-down deadlocks in which the stream waits
                on a stale token.
        """
        return self._token

    @token.setter
    def token(self, token: t.Optional["cancellation.Token"]) -> None:
        if self.monitoring:
            raise StreamError("cannot change cancellation token while monitoring")
        # See comment in __init__(). We need to keep token and condition
        # variable in sync to not miss any events.
        self._token = token
        self._condition = token.wait_handle if token else threading.Condition()

    @property
    def monitoring(self) -> bool:
        """True if this stream is receiving values, False otherwise."""
        return self._handle.isMonitoring()

    def start_monitoring(self) -> None:
        """Start receiving values on this stream."""
        self._handle.startMonitoring()

    def stop_monitoring(self) -> None:
        """Stop receiving values on this stream."""
        self._handle.stopMonitoring()

    def clear(self) -> None:
        """Empty the queue."""
        with self._condition:
            self._queue.clear()

    @contextlib.contextmanager
    def locked(self) -> t.Iterator[None]:
        """Return a context manager that locks this stream.

        Locking the stream may prevent `TOC/TOU
        <https://en.wikipedia.org/wiki/Time-of-check_to_time-of-use>`_
        errors. While the stream is locked, no new items can be enqueued
        by the subscription handler. You should lock the stream only for
        short periods of time; blocking the subscription handler for too
        long risks that data gets lost.

        However, you *may* call :meth:`wait_next()` while the stream is
        locked. It automatically releases the lock while waiting.

        The returned context manager is neither reentrant nor reusable
        nor meaningful. Call this method again to get new or nested
        locks.

        Example:

            >>> def take_newest(
            ...     stream: ParamStream
            ... ) -> t.Tuple[object, Header]:
            ...     '''Return the latest value, discard all others.'''
            ...     with stream.locked():
            ...         if stream.ready:
            ...             value = stream.newest
            ...             # Without the lock, the subscription handler
            ...             # might enqueue an item here, which would be
            ...             # lost forever.
            ...             stream.clear()
            ...             return value
            ...         # `ParamStream` uses a reentrant lock, so
            ...         # nothing bad happens if you call `wait_next()`
            ...         # while it is locked.
            ...         return stream.wait_next()
        """
        with self._condition:
            yield

    @property
    def ready(self) -> bool:
        """True if there is an event in the queue."""
        with self._condition:
            return bool(self._queue)

    @property
    @abc.abstractmethod
    def oldest(self) -> _Item:
        """The oldest item in the queue.

        Raises:
            IndexError: if the queue is empty.
            JavaException: if an exception occurred on the Java side
                while receiving this value.
        """
        with self._condition:
            event = self._queue[0]
        return _unwrap_event(event)

    @property
    @abc.abstractmethod
    def newest(self) -> _Item:
        """The most recent item in the queue.

        Raises:
            IndexError: if the queue is empty.
            JavaException: if an exception occurred on the Java side
                while receiving this value.
        """
        with self._condition:
            event = self._queue[-1]
        return _unwrap_event(event)

    # Tricky: We write the docstring on this internal method and
    # dynamically copy it onto the public method `wait_next()`
    # in the subclasses.
    def _wait_next(self, timeout: t.Optional[float]) -> t.Optional[_Item]:
        """Wait for the next value received by the stream.

        If there already is an item in the queue, it is removed and this
        function returns immediately. If there is none, this function
        blocks and waits for a new value to arrive.

        Args:
            timeout: If passed and not None, the amount of time (in
                seconds) for which to wait if there is no value in the
                queue.

        Returns:
            The oldest value in the queue or, if there is none, the next
            value received. None if the specified timeout elapses before
            a new value has arrived.

        Raises:
            CancelledError: if a :class:`cancellation.Token` has been
                passed to :func:`subscribe_stream()` and the token has
                been cancelled.
            JavaException: if an exception occurred on the Java side
                while receiving this value.
            StreamError: if the queue is empty, the subscription is not
                active and no timeout has been specified; this serves to
                prevent a deadlock in the application.
        """
        # Prevent deadlock.
        if not self.monitoring and timeout is None and not self._queue:
            raise StreamError("queue is empty, wait_next() would deadlock")
        with self._condition:
            if self._token:
                self._token.raise_if_cancellation_requested()
            while not self._queue:
                # Threading: This wait may return for three reasons: 1.
                # a new item has arrived, 2. our cancellation token has
                # been cancelled, 3. the timeout has expired. We must
                # check all three.
                success = self._condition.wait(timeout)
                if self._token:
                    self._token.raise_if_cancellation_requested()
                if not success:
                    return None
            event = self._queue.popleft()
        return _unwrap_event(event)

    # Tricky: We write the docstring on this internal method and
    # dynamically copy it onto the public method `next_if_ready()`
    # in the subclasses.
    def _next_if_ready(self) -> t.Optional[_Item]:
        """Return the next value or None if the queue is empty.

        This is similar to ``wait_next(timeout=0.0)``, but skips
        checking the token for a cancellation request. Most importantly,
        this function still acquires a lock on the queue to check its
        contents.

        Raises:
            JavaException: if an exception occurred on the Java side
                while receiving this value.
        """
        with self._condition:
            if self._queue:
                event = self._queue.popleft()
                return _unwrap_event(event)
        return None

    def _on_value(
        self,
        names: _OneOrList[str],
        values: _OneOrList[object],
        headers: _OneOrList[dict],
    ) -> None:
        with self._condition:
            event: _Event
            if isinstance(names, str):
                event = (t.cast(object, values), Header(t.cast(dict, headers)))
            else:
                event = [
                    (value, Header(header))
                    for value, header in zip(
                        t.cast(t.List[object], values), t.cast(t.List[dict], headers)
                    )
                ]
            self._queue.append(event)
            # Threading: Notify all will wake up all threads waiting for
            # new data. They will race for `self._condition` and only
            # one will acquire it and successfully pop off the queue.
            # The others fail and go back to sleep.
            # Threading: We cannot use `notify()` because we share our
            # condition variable with `self._token`. A thread that waits
            # only on the token might be woken up and none of the
            # threads waiting on the queue would be the wiser.
            self._condition.notify_all()

    def _on_exception(
        self, _names: _OneOrList[str], _desc: str, exc: Exception
    ) -> None:
        with self._condition:
            self._queue.append(JavaException(exc))
            # Threading: See comment in `_on_value()`.
            self._condition.notify_all()


class ParamStream(_BaseStream):
    """A synchronized handle to a one-parameter PyJapc subscription.

    Typically you use :func:`subscribe_stream` to instantiate this
    class.
    """

    def __init__(
        self,
        japc: "PyJapc",
        name: str,
        *,
        token: t.Optional["cancellation.Token"],
        maxlen: t.Optional[int],
        **kwargs: t.Any,
    ) -> None:
        super().__init__(japc, name, token=token, maxlen=maxlen, **kwargs)

    def __str__(self) -> str:
        return f"<{type(self).__name__}({self.parameter_name!r})>"

    def __repr__(self) -> str:
        return "<{typename}(<PyJapc>, {name!r}, {token!r}, {maxlen!r})>".format(
            typename=type(self).__name__,
            name=self.parameter_name,
            token=self.token,
            maxlen=self._queue.maxlen,
        )

    @property
    def parameter_name(self) -> str:
        """The name of the stream's underlying parameter."""
        return self._handle.getParameter().getName()

    @property
    def oldest(self) -> t.Tuple[object, Header]:
        return t.cast(t.Tuple[object, Header], super().oldest)

    @property
    def newest(self) -> t.Tuple[object, Header]:
        return t.cast(t.Tuple[object, Header], super().newest)

    @t.overload
    def wait_next(self) -> t.Tuple[object, Header]:
        ...

    @t.overload
    def wait_next(self, timeout: float) -> t.Optional[t.Tuple[object, Header]]:
        ...

    @functools.wraps(_BaseStream._wait_next, assigned=["__doc__"], updated=[])
    def wait_next(
        self, timeout: t.Optional[float] = None
    ) -> t.Optional[t.Tuple[object, Header]]:
        # pylint: disable = missing-function-docstring
        return t.cast(t.Tuple[object, Header], super()._wait_next(timeout))

    @functools.wraps(_BaseStream._next_if_ready, assigned=["__doc__"], updated=[])
    def next_if_ready(self) -> t.Optional[t.Tuple[object, Header]]:
        # pylint: disable = missing-function-docstring
        return t.cast(t.Tuple[object, Header], super()._next_if_ready())


class ParamGroupStream(_BaseStream):
    """A synchronized handle to a multi-parameter PyJapc subscription.

    Typically you use :func:`subscribe_stream` to instantiate this
    class.
    """

    def __init__(
        self,
        japc: "PyJapc",
        name: t.Iterable[str],
        *,
        token: t.Optional["cancellation.Token"],
        maxlen: t.Optional[int],
        **kwargs: t.Any,
    ) -> None:
        super().__init__(japc, name, token=token, maxlen=maxlen, **kwargs)

    def __str__(self) -> str:
        return f"<{type(self).__name__} of {len(self.parameter_names)} parameters>"

    def __repr__(self) -> str:
        return "<{typename}(<PyJapc>, {names!r}, {token!r}, {maxlen!r})>".format(
            typename=type(self).__name__,
            names=self.parameter_names,
            token=self.token,
            maxlen=self._queue.maxlen,
        )

    @property
    def parameter_names(self) -> t.List[str]:
        """A list with the names of all underlying parameters."""
        return list(self._handle.getParameterGroup().getNames())

    @property
    def oldest(self) -> t.List[t.Tuple[object, Header]]:
        return t.cast(t.List[t.Tuple[object, Header]], super().oldest)

    @property
    def newest(self) -> t.List[t.Tuple[object, Header]]:
        return t.cast(t.List[t.Tuple[object, Header]], super().newest)

    @t.overload
    def wait_next(self) -> t.List[t.Tuple[object, Header]]:
        ...

    @t.overload
    def wait_next(self, timeout: float) -> t.Optional[t.List[t.Tuple[object, Header]]]:
        ...

    @functools.wraps(_BaseStream._wait_next, assigned=["__doc__"], updated=[])
    def wait_next(
        self, timeout: t.Optional[float] = None
    ) -> t.Optional[t.List[t.Tuple[object, Header]]]:
        # pylint: disable = missing-function-docstring
        return t.cast(t.List[t.Tuple[object, Header]], super()._wait_next(timeout))

    @functools.wraps(_BaseStream._next_if_ready, assigned=["__doc__"], updated=[])
    def next_if_ready(self) -> t.Optional[t.List[t.Tuple[object, Header]]]:
        # pylint: disable = missing-function-docstring
        return t.cast(t.List[t.Tuple[object, Header]], super()._next_if_ready())


@t.overload
def subscribe_stream(
    japc: "PyJapc",
    name_or_names: str,
    *,
    token: t.Optional["cancellation.Token"] = ...,
    maxlen: t.Optional[int] = ...,
    convert_to_python: bool = ...,
    selector: t.Optional[str] = ...,
    data_filter: t.Optional[str] = ...,
) -> ParamStream:
    ...


# Note: `name_or_names` is annotated as a list on purpose. The reason is
# that Python's strings themselves are collections of strings:
# `list("foo") == ["f", "o", "o"]`. Hence, `t.Collection[str]` and
# `t.Iterable[str]` will conflict with plain `str`. This likely will
# never be fixable.
@t.overload
def subscribe_stream(
    japc: "PyJapc",
    name_or_names: t.List[str],
    *,
    token: t.Optional["cancellation.Token"] = ...,
    maxlen: t.Optional[int] = ...,
    convert_to_python: bool = ...,
    selector: t.Optional[str] = ...,
    data_filter: t.Optional[str] = ...,
) -> ParamGroupStream:
    ...


def subscribe_stream(
    japc: "PyJapc",
    name_or_names: t.Union[str, t.List[str]],
    *,
    token: t.Optional["cancellation.Token"] = None,
    maxlen: t.Optional[int] = 1,
    convert_to_python: bool = True,
    selector: t.Optional[str] = None,
    data_filter: t.Optional[str] = None,
) -> t.Union[ParamStream, ParamGroupStream]:
    """Subscribe to a parameter and create a stream of its values.

    The returned stream synchronizes with the subscription handler to
    ensure that no race conditions occur. It provides methods that allow
    the caller to wait for the next value to arrive. By default, the
    stream also maintains a queue to ensure that no values are lost.

    Args:
        japc: The :class:`PyJapc` object on which to subscribe.
        name_or_names: The parameter(s) to which to subscribe. Pass a
            single string to subscribe to a parameter, a list of strings
            to subscribe to a parameter group.

    Keyword args:
        token: If passed, the stream will hold onto this token and
            watch it. In this case, :meth:`wait_next()` can get
            cancelled through the token.
        maxlen: The maximum length of the stream's internal queue. The
            default is ``1``, i.e. only the most recent value is
            retained. If None, there is no limit and the queue might
            grow beyond all bounds if not emptied regularly.
        convert_to_python: If passed and False, return raw Java objects.
            By default, JAPC attempts to convert Java objects to Python
            objects.
        selector: If passed, use this instead of ``japc``'s default
            timing selector.
        data_filter: If passed, use this instead of ``japc``'s default
            data filter.

    Returns:
        A :class:`ParamStream` for a single parameter and a
        :class:`ParamGroupStream` for a parameter group.

    Note:
        The synchronization happens purely on a threading level. No
        timestamps are inspected or acted upon. If you need to ensure
        certain timing behavior, you must inspect the :class:`Header`
        returned by the stream.

    The returned parameter streams are context managers. Entering their
    context starts monitoring their handle, exiting stops it. They are
    reusable, but not re-entrant. This means the *same* stream may be
    used in subsequent ``with`` blocks, but not in nested ones.

        >>> def run_analysis(japc: "PyJapc"):
        ...     stream = subscribe_stream(japc, "device/property#field")
        ...     with stream:
        ...         values_and_headers = [
        ...             stream.wait_next() for _ in range(10)
        ...         ]
        ...     values, headers = zip(*values_and_headers)
        ...     ...
    """
    subscribe_kwargs: t.Dict[str, t.Any] = {"noPyConversion": not convert_to_python}
    if selector is not None:
        subscribe_kwargs["timingSelectorOverride"] = selector
    if data_filter is not None:
        subscribe_kwargs["dataFilterOverride"] = data_filter
    if isinstance(name_or_names, str):
        return ParamStream(
            japc, name_or_names, token=token, maxlen=maxlen, **subscribe_kwargs
        )
    return ParamGroupStream(
        japc, name_or_names, token=token, maxlen=maxlen, **subscribe_kwargs
    )
