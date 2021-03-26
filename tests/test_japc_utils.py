"""Test the JAPC utilities."""

# pylint: disable = missing-class-docstring
# pylint: disable = missing-function-docstring
# pylint: disable = redefined-outer-name

import logging
import threading
import time
import typing as t
from unittest.mock import Mock

import pytest

from cernml.coi.unstable import cancellation, japc_utils


def test_monitoring() -> None:
    with japc_utils.monitoring(Mock()) as handle:
        handle.startMonitoring.assert_called_once_with()
    handle.stopMonitoring.assert_called_once_with()


def test_subscriptions() -> None:
    with japc_utils.subscriptions(Mock()) as japc:
        japc.startSubscriptions.assert_called_once_with()
    japc.stopSubscriptions.assert_called_once_with()


def mock_header() -> japc_utils.Header:
    keys = [
        "acqStamp",
        "cycleStamp",
        "setStamp",
        "selector",
        "isFirstUpdate",
        "isImmediateUpdate",
    ]
    return japc_utils.Header({key: Mock() for key in keys})


class MockSubscription:
    TIME_STEP_SECONDS = 0.01

    # pylint: disable = invalid-name

    def __init__(self) -> None:
        self.mock_values: list = []
        self.name: t.Optional[str] = None
        self.on_value: t.Optional[t.Callable] = None
        self.on_exception: t.Optional[t.Callable] = None
        self.thread: t.Optional[threading.Thread] = None

    def __call__(
        self,
        name: str,
        onValueReceived: t.Callable,
        onException: t.Callable,
        **kwargs: t.Any,
    ) -> "MockSubscription":
        self.name = name
        self.on_value = onValueReceived
        self.on_exception = onException
        return self

    def isMonitoring(self) -> bool:
        return bool(self.thread)

    def startMonitoring(self) -> None:
        if self.thread:
            return
        assert self.name is not None, "monitoring started before subscription"
        self.thread = threading.Thread(target=self._thread_func)
        self.thread.start()

    def stopMonitoring(self) -> None:
        if not self.thread:
            return
        thread = self.thread
        self.thread = None
        thread.join()

    def _thread_func(self) -> None:
        logging.info("starting thread")
        assert self.on_value is not None
        assert self.on_exception is not None
        for value in list(self.mock_values):
            time.sleep(self.TIME_STEP_SECONDS)
            if not self.isMonitoring():
                break
            if isinstance(value, Exception):
                self.on_exception(self.name, str(value), value)
            else:
                logging.info("sending %s", value)
                self.on_value(self.name, value, mock_header())
                logging.info("sent %s", value)
        logging.info("terminating thread")


@pytest.fixture
def japc() -> Mock:
    return Mock(subscribeParam=MockSubscription())


def test_receive_values(japc: Mock) -> None:
    expected = [Mock(), Mock(), Mock()]
    japc.subscribeParam.mock_values = expected
    stream = japc_utils.subscribe_stream(japc, "")
    with stream:
        received = [stream.wait_next()[0] for _ in range(3)]
        assert stream.wait_next(2 * MockSubscription.TIME_STEP_SECONDS) is None
    assert received == expected


def test_block_without_values(japc: Mock) -> None:
    japc.subscribeParam.mock_values = []
    stream = japc_utils.subscribe_stream(japc, "")
    with stream:
        assert stream.wait_next(2 * MockSubscription.TIME_STEP_SECONDS) is None


def test_raise_if_not_monitoring(japc: Mock) -> None:
    japc.subscribeParam.mock_values = []
    stream = japc_utils.subscribe_stream(japc, "")
    with pytest.raises(japc_utils.StreamError):
        stream.wait_next()
        assert stream.wait_next(MockSubscription.TIME_STEP_SECONDS) is None


def test_queue_maxlen_is_one(japc: Mock) -> None:
    sent_values = [Mock() for _ in range(3)]
    japc.subscribeParam.mock_values = sent_values
    stream = japc_utils.subscribe_stream(japc, "")
    with stream:
        japc.subscribeParam.thread.join()
        all_available = [value for value, _header in iter(stream.next_if_ready, None)]
    assert all_available == sent_values[-1:]


def test_queue_without_maxlen(japc: Mock) -> None:
    sent_values = [Mock() for _ in range(5)]
    japc.subscribeParam.mock_values = sent_values
    stream = japc_utils.subscribe_stream(japc, "", maxlen=None)
    with stream:
        japc.subscribeParam.thread.join()
        all_available = [value for value, _header in iter(stream.next_if_ready, None)]
    assert all_available == sent_values


def test_next_if_ready_doesnt_block(japc: Mock) -> None:
    sent_values = [Mock() for _ in range(2)]
    japc.subscribeParam.mock_values = sent_values
    stream = japc_utils.subscribe_stream(japc, "", maxlen=None)
    with stream:
        first, _ = stream.wait_next()
        assert stream.next_if_ready() is None
        second, _ = stream.wait_next()
    assert [first, second] == sent_values


def test_locked_prevents_updates(japc: Mock) -> None:
    sent_values = [Mock()]
    japc.subscribeParam.mock_values = sent_values
    stream = japc_utils.subscribe_stream(japc, "")
    with stream:
        assert not stream.ready
        with stream.locked():
            # Wait long enough that the thread calls the subscription
            # handler. This blocks because we're holding the lock.
            time.sleep(2 * MockSubscription.TIME_STEP_SECONDS)
            assert not stream.ready
        # Threading: Ensure that the thread has time to acquire the lock
        # and send its data.
        time.sleep(MockSubscription.TIME_STEP_SECONDS)
    assert stream.ready


def test_clear(japc: Mock) -> None:
    sent_values = [Mock()]
    japc.subscribeParam.mock_values = sent_values
    stream = japc_utils.subscribe_stream(japc, "")
    with stream:
        assert not stream.ready
        # Wait until the thread has sent its data.
        japc.subscribeParam.thread.join()
    assert stream.ready
    assert [stream.oldest[0]] == [stream.newest[0]] == sent_values
    stream.clear()
    assert not stream.ready


def test_oldest_newest(japc: Mock) -> None:
    sent_values = [Mock(), Mock()]
    japc.subscribeParam.mock_values = sent_values
    stream = japc_utils.subscribe_stream(japc, "", maxlen=2)
    with stream:
        # Wait until the thread has sent its data.
        japc.subscribeParam.thread.join()
    first = stream.oldest
    second = stream.newest
    assert [first[0], second[0]] == sent_values
    assert stream.ready
    assert stream.next_if_ready() == first
    assert stream.next_if_ready() == second
    assert stream.next_if_ready() is None
    assert not stream.ready


def test_exception(japc: Mock) -> None:
    sent_values = [Mock(), Mock(), ValueError()]
    japc.subscribeParam.mock_values = sent_values
    stream = japc_utils.subscribe_stream(japc, "")
    with stream:
        received = []
        with pytest.raises(japc_utils.JavaException):
            while True:
                value, _ = stream.wait_next()
                received.append(value)
    assert received == sent_values[:-1]


def test_cancel(japc: Mock) -> None:
    token = cancellation.Token(cancelled=True)
    japc.subscribeParam.mock_values = [Mock()]
    stream = japc_utils.subscribe_stream(japc, "", token=token)
    with pytest.raises(cancellation.CancelledError):
        with stream:
            stream.wait_next()
    assert not stream.ready


def test_cancel_preempts_ready(japc: Mock) -> None:
    token = cancellation.Token(cancelled=True)
    japc.subscribeParam.mock_values = [Mock()]
    stream = japc_utils.subscribe_stream(japc, "", token=token)
    with pytest.raises(cancellation.CancelledError):
        with stream:
            japc.subscribeParam.thread.join()
            stream.wait_next()
    assert stream.ready


def test_cancel_breaks_deadlock(japc: Mock) -> None:
    sent_values = [Mock() for _ in range(3)]
    japc.subscribeParam.mock_values = sent_values
    source = cancellation.TokenSource()

    def cancel_delayed() -> None:
        japc.subscribeParam.thread.join()
        # Add some time to handle the last sent value.
        time.sleep(MockSubscription.TIME_STEP_SECONDS)
        source.cancel()

    stream = japc_utils.subscribe_stream(japc, "", token=source.token)
    canceller = threading.Thread(target=cancel_delayed)
    with pytest.raises(cancellation.CancelledError):
        received_values = []
        with stream:
            canceller.start()
            # Would eventually deadlock if not cancelled.
            for value, _ in iter(stream.wait_next, None):
                received_values.append(value)
    canceller.join()
    assert not stream.ready
    assert received_values == sent_values
