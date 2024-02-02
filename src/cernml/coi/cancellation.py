# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provide cooperative task cancellation.

Cancellation is implemented as two classes with two-way communication
between them: `TokenSource` and `Token`:

    >>> import threading, time
    >>> def loop(token: Token) -> None:
    ...     while not token.cancellation_requested:
    ...         # Something that takes a long time:
    ...         time.sleep(0.01)
    >>> source = TokenSource()
    >>> thread = threading.Thread(target=loop, args=(source.token,))
    >>> thread.start()
    >>> source.cancel()
    >>> # This line would deadlock if we had
    >>> # not sent a cancellation request.
    >>> thread.join()

Usually, it is more convenient to check the token's state with
`Token.raise_if_cancellation_requested()`:

    >>> def loop(token: Token) -> None:
    ...     while True:
    ...         token.raise_if_cancellation_requested()
    ...         # Something that takes a long time:
    ...         time.sleep(0.01)

Note that :func:`cernml.japc_utils.subscribe_stream()` supports
cancellation tokens. This makes it easy to interrupt a thread that is
waiting a long time for accelerator data.

Normally, a cancellation request cannot be undone. This is on purpose,
as cancellation might have left the task object in an unclean state.
However, the task may explicitly declare that it has cleaned itself up
after a cancellation by *completing* it. Completing a cancellation
allows the source to reset and reuse it for another cancellation.

Take this class. It reads values from some machine, but occasionally
gets stuck in an infinite loop:

    >>> class SporadicFailure:
    ...     def __init__(self, token):
    ...         self.token = token
    ...         self.next_value = 0
    ...
    ...     def get_next(self):
    ...         # We know that our class won't break if it gets
    ...         # interrupted. Hence, once we have handled a
    ...         # cancellation, we can mark it as completed.
    ...         try:
    ...             value = self.read_from_machine()
    ...             return value
    ...         except CancelledError:
    ...             self.token.complete_cancellation()
    ...             raise
    ...
    ...     def read_from_machine(self):
    ...         self.next_value += 1
    ...         # Deadlock sometimes:
    ...         if self.next_value == 2:
    ...             self.deadlock()
    ...         self.token.raise_if_cancellation_requested()
    ...         return self.next_value
    ...
    ...     def deadlock(self):
    ...         # This waits indefinitely. However, because we use a
    ...         # cancellation token, it can be interrupted.
    ...         with self.token.wait_handle:
    ...             while not self.token.cancellation_requested:
    ...                 self.token.wait_handle.wait()

We want to fetch a value from it and add it to a list. With a real
machine, this could take a while:

    >>> source = TokenSource()
    >>> receiver = SporadicFailure(source.token)
    >>> collected_data = []
    >>> collected_data.append(receiver.get_next())
    >>> collected_data
    [1]

Fetching the next value will deadlock for some reason, so we will have
to cancel it. In a real application, we would put fetching into a
background thread and cancel when the user clicks a button:

    >>> timer = threading.Timer(0.1, source.cancel)
    >>> timer.start()
    >>> collected_data.append(receiver.get_next())
    Traceback (most recent call last):
    ...
    coi.cancellation.CancelledError

However, we have a problem: If we now tried to fetch the next value, the
token would still be cancelled, so we would get another exception:

    >>> collected_data.append(receiver.get_next())
    Traceback (most recent call last):
    ...
    coi.cancellation.CancelledError

However, we are lucky, because the receiver still is in a usable state
(and is telling us as much):

    >>> source.can_reset_cancellation
    True
    >>> source.reset_cancellation()

And now we can collect data again:

    >>> collected_data.append(receiver.get_next())
    >>> collected_data
    [1, 4]
"""

import enum
import threading
import typing as t
import weakref

__all__ = [
    "CancelledError",
    "CannotReset",
    "Token",
    "TokenSource",
]


class CancelledError(Exception):
    """The current task has been requested to be cancelled.

    Note that it inherits from `Exception`, so it can be caught by an
    overly broad :keyword:`except` clause.
    """


class CannotReset(Exception):
    """Cancellation cannot be reset as the task did not complete it.

    There are two possible reasons for this:

    1. The task might have simply forgotten to call
       `Token.complete_cancellation()`.
    2. The task has ended up in a *poisoned* state because of the
       cancellation. For example, two variables meant to be consistent
       with each other no longer are.

    Because of #2, it is not safe to reset a cancellation that has not
    been completed.
    """


class _State(enum.Enum):
    """Internal state of the `Token`.

    Regular tokens start out in the `READY` state. Once the
    `TokenSource` requests cancellation, the token transitions into the
    `CANCELLING` state. If the token's holder has handled the
    cancellation, it may call `~Token.complete_cancellation()` to
    transition it into the `CANCELLED` state.

    This signals to the token source that cancellation is complete and
    it may call `~TokenSource.reset_cancellation()`. This transitions
    the token back into the `READY` state. From this, a new cancellation
    can be requested.

    For convenience, the state is ordered by the above state machine::

        >>> _State.READY < _State.CANCELLING
        True
        >>> _State.READY < _State.CANCELLED
        True
        >>> _State.CANCELLING < _State.CANCELLED
        True
        >>> _State.READY > _State.CANCELLING
        False
        >>> _State.READY <= _State.READY
        True
    """

    READY = 0
    CANCELLING = 1
    CANCELLED = 2

    def __lt__(self, other: "_State") -> bool:
        return int(self.value) < other.value

    def __gt__(self, other: "_State") -> bool:
        return int(self.value) > other.value

    def __le__(self, other: "_State") -> bool:
        return int(self.value) <= other.value

    def __ge__(self, other: "_State") -> bool:
        return int(self.value) >= other.value


class TokenSource:
    """Sending half of a cancellation channel.

    This half is usually created by a host application. It then sends
    the token to a `~cernml.coi.Problem` upon instantiation.

    Whenever a `~cernml.coi.Problem` enters a long-running calculation,
    it should periodically check the token for a cancellation request.
    If such a request has arrived, the problem has a chance to
    gracefully abort its calculation.

    As a convenience feature, token sources are also context managers.
    They yield their token when entering a context and automatically
    cancel it when leaving the context:

        >>> import threading, time
        >>> # An infinite loop that can be cancelled:
        >>> def loop(token: Token) -> None:
        ...     while not token.cancellation_requested:
        ...         time.sleep(0.01)
        >>> # Create source + token and start the thread.
        >>> with TokenSource() as token:
        ...     thread = threading.Thread(target=loop, args=(token,))
        ...     thread.start()
        ...     # Do something complex or just wait ...
        ...     time.sleep(0.01)
        >>> # Leaving the `with` block cancels the token.
        >>> thread.join()  # No deadlock!
    """

    # Developer note: In C#, which directly inspires this class, the
    # cancellation state is on the source and the token maintains a
    # strong reference to it. Uncancellable and always-cancelled tokens
    # are implemented by referencing static global immutable token
    # sources in the respective states.
    #
    # We don't do this for ease of implementation. In C#, all logic is
    # within the token source because of the additional complexity of
    # timers ("create a source that cancels automatically after X
    # seconds), registered actions ("call this function as soon as the
    # token is cancelled") and joined cancellation ("create a source
    # that cancels automatically as soon as these other sources are all
    # cancelled"). We support none of these, so the current architecture
    # is good enough.

    __slots__ = ("_token", "__weakref__")

    # pylint: disable = protected-access

    def __init__(self) -> None:
        self._token = Token(False)
        self._token._source = weakref.ref(self)

    @property
    def token(self) -> "Token":
        """The token associated with source.

        Pass this token to a `~cernml.coi.Problem` to be able to
        communicate a cancellation to it.
        """
        return self._token

    @property
    def cancellation_requested(self) -> bool:
        """True if `cancel()` has been called."""
        return self._token.cancellation_requested

    def cancel(self) -> None:
        """Send a cancellation request through the token.

        If there are any threads waiting for a cancellation request,
        they all get notified. Note that it is up the receiver of the
        token to honor the request.


        Example:

            >>> source = TokenSource()
            >>> source.token.cancellation_requested
            False
            >>> source.cancel()
            >>> source.token.cancellation_requested
            True

        Cancelling the same token twice is a no-op::

            >>> source.cancel()
            >>> source.token.cancellation_requested
            True
        """
        if self._token._state >= _State.CANCELLING:
            return
        self._token._state = _State.CANCELLING
        # Avoid creating the condition variable if there is none.
        wait_handle = self._token._wait_handle
        if wait_handle:
            with wait_handle:
                wait_handle.notify_all()

    @property
    def can_reset_cancellation(self) -> bool:
        """True if a previous cancellation can be reset.

        Example:

            >>> source = TokenSource()
            >>> source.can_reset_cancellation
            True
            >>> source.cancel()
            >>> source.can_reset_cancellation
            False
            >>> source.token.complete_cancellation()
            >>> source.can_reset_cancellation
            True
        """
        return self._token._state != _State.CANCELLING

    def reset_cancellation(self) -> None:
        """Reset a cancellation request.

        This can only be done if a previous cancellation request has
        been completed by the holder of the token. It resets the state
        back to as if there never was a cancellation.

        If not cancellation has been requested, this does nothing.

        Raises:
            CannotReset: if a cancellation has been requested but not
                completed.

        Example:

            >>> source = TokenSource()
            >>> source.cancellation_requested
            False
            >>> source.cancel()
            >>> source.cancellation_requested
            True
            >>> source.reset_cancellation()
            Traceback (most recent call last):
            ...
            coi.cancellation.CannotReset
            >>> source.token.complete_cancellation()
            >>> source.cancellation_requested
            True
            >>> source.reset_cancellation()
            >>> source.cancellation_requested
            False

        Resetting twice is a no-op::

            >>> source.reset_cancellation()
            >>> source.cancellation_requested
            False
        """
        if self._token._state == _State.CANCELLING:
            raise CannotReset()
        self._token._state = _State.READY

    def __enter__(self) -> "Token":
        return self.token

    def __exit__(self, *args: t.Any) -> None:
        self.cancel()


class Token:
    """Receiving half of a cancellation channel.

    Usually, you create this object via a `TokenSource`. It creates a
    token that can receive cancellation requests and mark them as
    completed. Marking a request as completed allows the token source to
    send further cancellation requests.

    Args:
        cancelled: If False (the default), create a token that cannot be
            cancelled. If True, create a token that is already
            cancelled.

    Manually created tokens can never change their state::

        >>> c = Token()
        >>> c.can_be_cancelled, c.cancellation_requested
        (False, False)
        >>> c = Token(True)
        >>> c.can_be_cancelled, c.cancellation_requested
        (True, True)
    """

    __slots__ = ("_state", "_wait_handle", "_source")

    def __init__(self, cancelled: bool = False) -> None:
        self._wait_handle: t.Optional[threading.Condition] = None
        self._state = _State.CANCELLED if cancelled else _State.READY
        # Trick: Use a weak reference to the source to avoid keeping it
        # alive. If the weak reference expires and we are still not
        # cancelled, we know we will never be cancelled. We never set
        # this reference, the TokenSource does in its
        # constructor.
        self._source: t.Optional[weakref.ReferenceType] = None

    @property
    def wait_handle(self) -> threading.Condition:
        """A condition variable on which to wait for cancellation.

        If you do not use `~threading.Condition` variables to
        synchronize multiple threads, you may safely ignore this
        attribute.

        This lazily creates the condition variable. You may use it to
        wait for cancellation. To avoid deadlocks, you should check
        `cancellation_requested` while the condition variable
        is locked:

            >>> import threading
            >>> def loop(token: Token) -> None:
            ...     with token.wait_handle:
            ...         while not token.cancellation_requested:
            ...             token.wait_handle.wait()
            >>> source = TokenSource()
            >>> thread = threading.Thread(
            ...     target=loop,
            ...     args=(source.token,),
            ... )
            >>> thread.start()
            >>> source.cancel()
            >>> # Doesn't deadlock, thread got notified by `cancel()`.
            >>> thread.join()
        """
        if not self._wait_handle:
            self._wait_handle = threading.Condition()
        return self._wait_handle

    @property
    def can_be_cancelled(self) -> bool:
        """True if a cancellation request can arrive or has arrived."""
        # Check that we have a weakref and it's still alive.
        source_is_alive = bool(self._source and self._source())
        return self.cancellation_requested or source_is_alive

    @property
    def cancellation_requested(self) -> bool:
        """True if a cancellation request has arrived."""
        return self._state >= _State.CANCELLING

    def raise_if_cancellation_requested(self) -> None:
        """Raise an exception if a cancellation request has arrived.

        Raises:
            CancelledError: If `cancellation_requested` is True. Note
                that it inherits from `Exception`, so it can be caught
                by an overly broad :keyword:`except` clause.
        """
        if self.cancellation_requested:
            raise CancelledError()

    def complete_cancellation(self) -> None:
        """Mark an ongoing cancellation as completed.

        Once a cancellation has been completed, the token source is free
        to reset it and later send another one. Hence, you should only
        call this function at the very end. Otherwise, the source may
        send a second request while you're still handling the first one.

        Calling this method more than once does nothing.

        Raises:
            RuntimeError: if no cancellation has been requested.

        Examples:

            >>> # Does nothing: cancellation already completed.
            >>> Token(True).complete_cancellation()
            >>> # Raises an exception: no cancellation ongoing.
            >>> Token(False).complete_cancellation()
            Traceback (most recent call last):
            ...
            RuntimeError: no cancellation request to be completed
        """
        if self._state < _State.CANCELLING:
            raise RuntimeError("no cancellation request to be completed")
        self._state = _State.CANCELLED
