Waiting for New Data Without Blocking the GUI
=============================================

A typical use case for COI problems is optimization of parameters of various
CERN accelerators. Doing so naturally requires communication with these
machines. This communication may take take a long time – especially when the
data we're interested in is *cycle-bound* (is published in regular intervals of
several seconds). Handling this in a clean fashion requires **synchronization**
between our optimization logic and the subscription handler that receives data
from the machine.

In addition, machines may exhibit sporadic transient failures. In this case, we
want to discard the defective data and wait for the next sample to arrive. At
the same time, if a failure turns out to be non-transient (it requires human
intervention), we don't want this logic to get stuck in an infinite loop. In
other words, users of our COI problems must be able to **cancel** them.

Tricky problems indeed! While this package cannot claim to solve them in all
possible cases, it provides a few tools to get reasonable behavior with few
lines of code in the most common cases.

Synchronization
---------------

To solve the problem of synchronization, the :doc:`utils:index` introduce the
concept of *parameter streams*. Below is a trivial example on how to use them:
Please see the dedicated :doc:`guide<utils:guide/japc_utils>` for more
information.

.. code-block:: python

    from pyjapc import PyJapc
    from cernml.japc_utils import subscribe_stream

    japc = PyJapc("LHC.USER.ALL", noSet=True)
    the_field = subscribe_stream(japc, "device/property#field")
    # Blocks execution until the next value is there.
    value, header = the_field.wait_for_next()

Cancellation
------------

In order to cancel long-running data acquisition tasks, the COI have adopted
the concept of `cancellation tokens from C#`_. A cancellation token is a small
object that is handed to your `~cernml.coi.Problem` subclass on which you may
check whether the user has requested a cancellation of your operation. If this
is the case, you have the ability to cleanly shut down operations – usually by
raising an exception.

.. _cancellation tokens from C#:
   https://docs.microsoft.com/en-us/dotnet/standard/threading/cancellation-in-managed-threads

To use this feature, your problem must first declare that its support it by
setting the ``"cern.cancellable"`` :ref:`metadata <Metadata>`. When it does so,
a host application will pass a `~cernml.coi.cancellation.Token` to the
constructor. On this token, the problem should check whether cancellation has
been requested whenever it enters a loop that may run for a long time.

This sounds complicated, but luckily, :ref:`parameter streams
<Synchronization>` already support cancellation tokens:

.. code-block:: python

    from cernml.coi
    # Requires `pip install cernml-coi-utils`.
    from cernml.japc_utils import subscribe_stream

    class MyProblem(coi.SingleOptimizable):
        metadata = {
            "cern.japc": True,
            "cern.cancellable": True,
            ...,
        }

        def __init__(self, japc, cancellation_token):
            self.japc = japc
            self.token = cancellation_token
            # Pass in the token. The stream will hold onto it and monitor it
            # whenever you you call `.wait_next()`.
            self.bpm_readings = subscribe_stream(
                japc, "...", token=cancellation_token
            )

        def get_initial_params(self):
            ...

        def compute_single_objective(self, params):
            self.japc.setParam("...", param)
            try:
                # This may block for a long time, depending on how fast the
                # data arrives and whether the data is valid. However, if
                # the user sends a cancellation request via the token,
                # `wait_next()` will unblock and raise an exception.
                while True:
                    value, header = self.bpm_readings.wait_next()
                    if self.is_data_good(value):
                        return self.compute_loss(value)
            except coi.cancellation.CancelledError:
                # Our environment has the nice property that even after a
                # cancellation, it will still work. Our caller could call
                # `compute_single_objective()` again and everything would
                # behave the same. We let the outside world know that this
                # is the case by marking the cancellation as "completed".
                self.token.complete_cancellation()
                raise
            return value

If you have your own data acquisition logic, you can use the token yourself by
regularly calling
`~cernml.coi.cancellation.Token.raise_if_cancellation_requested()` on it:

.. code-block:: python

    from time import sleep

    class MyProblem(coi.SingleOptimizable):

        def compute_single_objective(self, params):
            self.japc.setParam(...)
            value = None
            while True:
                self.token.raise_if_cancellation_requested()
                sleep(0.5)  # Or any operation that takes a long time …
                value = ...
                if is_value_good(value):
                    return value

        ...

If you write a host application yourself, you will usually want to create a
`~cernml.coi.cancellation.TokenSource` and pass its token to the optimization
problem if it is cancellable:

.. code-block:: python

    from threading import Thread
    from cernml import coi
    from cernml.coi import cancellation

    class MyApp:
        def __init__(self):
            self.source = cancellation.TokenSource()

        def on_start(self):
            env_name = self.env_name
            agent = self.agent
            token = self.source.token
            self.worker = Thread(target=run, args=(env_name, agent, token))
            self.worker.start()

        def on_stop(self):
            self.source.cancel()
            self.worker.join()
            assert self.source.can_reset_cancellation
            self.reset_cancellation()

        ...

    def run(env_name, agent, token):
        kwargs = {}
        metadata = coi.spec(env_name).metadata
        if metadata.get("cern.cancellable", False):
            kwargs["cancellation_token"] = token
        env = coi.make(env_name, **kwargs)
        try:
            while True:
                # Also check the token ourselves, so that the `Problem`
                # only has to check it when it enters a loop.
                token.raise_if_cancellation_requested()
                obs = env.reset()
                done = False
                state = None
                while not done:
                    # Ditto.
                    token.raise_if_cancellation_requested()
                    action, state = agent.predict(obs, state)
                    obs, _reward, done, _info = env.step(action)
        except cancellation.CancelledError:
            # Because the env gets closed at the end of this thread, we
            # can *definitely* reuse the cancellation token source.
            token.complete_cancellation()
        finally:
            env.close()  # Never forget this!
