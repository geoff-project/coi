"""Provide cooperative task cancellation."""

import enum
import threading
import typing as t
import weakref


class CancelledError(Exception):
    """The current task has been requested to be cancelled.

    Note that it inherits from :class:`Exception`, so it can be caught
    by an overly broad ``except`` clause.
    """


class TokenSource:
    """Owner of a single :class:`Token`.

    Cancellation tokens provide a means to interrupt a problem that is
    calculating the next value of the loss function or reward. This is
    important in contexts where this calculation may take an arbitrarily
    long time, e.g. because it requires communication with an external
    machine.

    The usual way to use them is that whenever a :class:`Problem` enters
    a long-running calculation, it should periodically check the token
    for a cancellation request. If such a request has arrived, the
    problem has a chance to gracefully abort its calculation.

    Calling :meth:`~Token.raise_if_cancellation_requested()` is the most
    convenient way to handle cancellation in a long-running loop::

        >>> import time
        >>> def loop(token: Token) -> None:
        ...     while True:
        ...         token.raise_if_cancellation_requested()
        ...         time.sleep(1)  # Long-running operation.

    For more fine-grained control, you may also check
    :attr:`~Token.cancellation_requested` regularly::

        >>> def loop(token: Token) -> None:
        ...     while not token.cancellation_requested:
        ...         time.sleep(1)  # Long-running operation.

    From outside, the usual pattern is to create a source, pass its
    token to a *receiver*, and call :meth:`cancel()` (or not)::

        >>> import threading
        >>> source = TokenSource()
        >>> t = threading.Thread(target=loop, args=(source.token,))
        >>> t.start()
        >>> # Do something complex or just wait ...
        >>> source.cancel()
        >>> t.join()  # Deadlock if we hadn't cancelled.

    As a convenience feature, cancellation token sources are also
    context managers. They offer their token when entering a context and
    automatically cancel it when leaving the context::

        >>> with TokenSource() as token:
        ...     t = threading.Thread(target=loop, args=(source.token,))
        ...     t.start()
        ...     # Do something complex or just wait ...
        >>> # Leaving the `with` block cancels the token.
        >>> t.join()  # No deadlock!

    For debugging purposes, you can also create cancellation tokens that
    are always cancelled or can never be cancelled. See :class:`Token`
    for more information.
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

        Pass this token to a :class:`Problem` to be able to communicate
        a cancellation to it.
        """
        return self._token

    @property
    def cancellation_requested(self) -> bool:
        """True if :meth:`cancel()` has been called."""
        return self._token._cancellation_requested

    def cancel(self) -> None:
        """Send a cancellation request through the token.

        If there are any threads waiting for a cancellation request,
        they all get notified. Note that it is up the receiver of the
        token to honor the request.
        """
        self._token._cancellation_requested = True
        # Avoid creating the condition variable if there is none.
        wait_handle = self._token._wait_handle
        if wait_handle:
            with wait_handle:
                wait_handle.notify_all()

    def __enter__(self) -> "Token":
        return self.token

    def __exit__(self, *args: t.Any) -> None:
        self.cancel()


class Token:
    """Channel to cooperatively cancel a problem's calculation.

    Args:
        cancelled: If False (the default), create a token that cannot be
            cancelled. If True, create a token that is already
            cancelled.

    Use :class:`TokenSource` to create a normal, cancellable token::

        >>> source = TokenSource()
        >>> c = source.token
        >>> c.can_be_cancelled
        True
        >>> c.cancellation_requested
        False
        >>> source.cancel()
        >>> c.can_be_cancelled
        True
        >>> c.cancellation_requested
        True
        >>> c.raise_if_cancellation_requested()
        Traceback (most recent call last):
        ...
        coi._cancellation.CancelledError

    Manually created tokens can never change their state::

        >>> c = Token()
        >>> c.can_be_cancelled, c.cancellation_requested
        (False, False)
        >>> c = Token(True)
        >>> c.can_be_cancelled, c.cancellation_requested
        (True, True)

    Note:
        Once cancelled, a token can never become "uncancelled" again.
        This prevents `ABA problems`_. If you want to restart a
        cancelled optimization, the most portable solution is to create
        a new :class:`Problem` instance with a fresh token.

        If you only deal with a concrete :class:`Problem` subclass, it
        may also be feasible to pass a new token to it after
        instantiation.

        .. _ABA problems: https://en.wikipedia.org/wiki/ABA_problem
    """

    __slots__ = ("_cancellation_requested", "_wait_handle", "_source")

    def __init__(self, cancelled: bool = False) -> None:
        self._wait_handle: t.Optional[threading.Condition] = None
        self._cancellation_requested = cancelled
        # Trick: Use a weak reference to the source to avoid keeping it
        # alive. If the weak reference expires and we are still not
        # cancelled, we know we will never be cancelled. We never set
        # this reference, the TokenSource does in its
        # constructor.
        self._source: t.Optional[weakref.ReferenceType] = None

    @property
    def wait_handle(self) -> threading.Condition:
        """A condition variable on which to wait for cancellation.

        If you do not use condition variables to synchronize multiple
        threads, you may safely ignore this attribute.

        This lazily creates the condition variable. You may use it to
        wait for cancellation. To avoid deadlocks, you should check
        :attr:`cancellation_requested` while the condition variable
        is locked:

            >>> import threading
            >>> def loop(token: Token) -> None:
            ...     with token.wait_handle as h:
            ...         while not token.cancellation_requested:
            ...             h.wait()
            ...         # You might as well write:
            ...         # h.wait_for(lambda: token.cancellation_requested)
            >>> source = TokenSource()
            >>> t = threading.Thread(target=loop, args=(source.token,))
            >>> t.start()
            >>> source.cancel()
            >>> t.join()  # Doesn't deadlock, t got notified by `cancel()`.
        """
        if not self._wait_handle:
            self._wait_handle = threading.Condition()
        return self._wait_handle

    @property
    def can_be_cancelled(self) -> bool:
        """True if a cancellation request can arrive or has arrived."""
        return self._cancellation_requested or (
            self._source is not None and self._source() is not None
        )

    @property
    def cancellation_requested(self) -> bool:
        """True if a cancellation request has arrived."""
        return self._cancellation_requested

    def raise_if_cancellation_requested(self) -> None:
        """Raise an exception if a cancellation request has arrived.

        Raises:
            CancelledError: If :attr:`cancellation_requested` is
                True. Note that it inherits from :class:`Exception`,
                so it can be caught by an overly broad ``except``
                clause.
        """
        if self._cancellation_requested:
            raise CancelledError()
