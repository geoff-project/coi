# User Guide

The Common Optimization Interfaces make it possible to define optimization
problems in a uniform fashion so that they can be used with as many
optimization algorithms as possible. The goal is to make it possible to write
generic programs that make use of optimization problems written by a third
party without knowing the specifics of the problem.

These interfaces assume a plugin architecture. They assume that an optimization
problem is embedded into some sort of *host* application. As such, the problem
must be able to advertise certain capabilities and properties and the
application must be able to query such properties.

## The Core API

```{digraph} inheritance_diagram
---
caption: "Fig. 1: Inheritance diagram of the core interfaces"
---
rankdir = "BT";
bgcolor = "#00000000";
node [shape=record, fontname="Latin Modern Sans", style=filled, fillcolor="white"];
edge [style=dashed];

problem[label=<{
    cernml.coi.<b>Problem</b>|
    render(<i>mode</i>: str) → Any<br/>close() → None|
    <i>metadata</i>: Dict[str, Any]<br/><i>unwrapped</i>: Problem}>,
];

sopt[label=<{
    cernml.coi.<b>SingleOptimizable</b>|
    get_initial_params() → Params<br/>compute_single_objective(<i>p</i>: Params) → float|
    <i>optimization_space</i><br/><i>objective_range</i><br/><i>constraints</i>}>,
];

env[label=<{
    gym.<b>Env</b>|
    reset() → Obs<br/>step(<i>a</i>: Action) → Obs, …<br/>seed(…) → …|
    <i>action_space</i><br/><i>observation_space</i><br/><i>reward_range</i>}>,
];

optenv[label=<cernml.coi.<b>OptEnv</b>>];

optenv -> sopt -> problem;
optenv -> env -> problem;
```

The interfaces are designed in a modular fashion: depending on the algorithms
that an optimization problem supports, it either implements
{class}`~cernml.coi.SingleOptimizable` (for classical single-objective
optimization), {class}`~gym.Env` (for reinforcement learning) or both. The
{class}`~cernml.coi.Problem` interface captures the greatest common
denominator – that, which all interfaces have in common.

As a convenience, this package also provides the {class}`~cernml.coi.OptEnv`
interface. It is simply an intersection of
{class}`~cernml.coi.SingleOptimizable` and {class}`~gym.Env`. This means that
implementing it is the same as implementing both of its bases. At the same
time, every class that implements both base interfaces also implements
{class}`~cernml.coi.OptEnv`. A demonstration:

```python
import gym
from cernml import coi

class Indirect(coi.SingleOptimizable, gym.Env):
    ...

assert issubclass(Indirect, coi.OptEnv)
```


### Metadata

Every optimization problem should have a class attribute called
{attr}`~cernml.coi.Problem.metadata`, which is a dict with string keys. The
dict must be defined at the class level and immutable. It communicates
fundamental properties of the class and how a host application can use it.

The following keys are defined and understood by this package:

`"render.modes"`
: the render modes that the optimization problem understands (see
[](#rendering));

`"cern.machine"`
: the accelerator that an optimization problem is associated with;

`"cern.japc"`
: a boolean flag indicating whether the problem's constructor expects an
argument named `japc` of type `pyjapc.PyJapc`;

`"cern.cancellable"`
: A boolean flag indicating whether the problem's constructor expects an
argument named `cancellation_token` of type
{class}`cancellation.Token<cernml.coi.unstable.cancellation.Token>` (see
[](#cancellation)).

See the {attr}`API docs<cernml.coi.Problem.metadata>` for a full spec.

### Rendering

The metadata entry `"render.modes"` allows a problem to declare that its
internal state can be visualized. It should be a list of strings where each
string is a supported render mode. Host applications may pick one of these
strings and pass it to the problems {meth}`~cernml.coi.Problem.render` method.
For this to work, render modes need to have well-defined semantics.

The following render modes are standardized by either Gym or this package:

`"human"`
: The default mode, for interactive use. This should e.g. open a window and
display the problem's current state in it. Displaying the window should not
block control flow.

`"ansi"`
: Return a text-only representation of the problem. This may contain e.g.
terminal control codes for color effects.

`"rgb_array"`
: Return a Numpy array representing color image data.

`"matplotlib_figures"`
: Return a list of Matplotlib `Figure` objects, suitable for embedding into a
GUI application.

See the {meth}`~cernml.coi.Problem.render` docs for a full spec of each render
mode.

### Closing

Some optimization problems have to acquire certain resources in order to
perform their tasks. Examples include:

- spawning processes,
- starting threads,
- subscribing to JAPC parameters.

While Python garbage-collects objects which are no longer accessible (including
{class}`~cernml.coi.Problem` instances), some of these resources require manual
function calls in order to be properly cleaned up.

If such is the case for an optimization problem, it should override the
{meth}`~cernml.coi.Problem.close` method and define all such actions in it. A
host application is required to call {meth}`~cernml.coi.Problem.close` when it
has no more need for an optimization problem.

```{warning}
The {meth}`~cernml.coi.Problem.close` method is *not* called after an
optimization procedure is done. In particular, a host application may perform
several optimization runs on the same problem and call
{meth}`~cernml.coi.Problem.close` only at the very end. Furthermore, an
arbitrary amount of time may pass between the last call to
{meth}`~cernml.coi.SingleOptimizable.compute_single_objective` and the call to
{meth}`~cernml.coi.Problem.close`.
```

```{note}
**Note:** If you want to use an optimization problem in your own application or
script, consider using a [context
manager](https://docs.python.org/3/library/contextlib.html#contextlib.closing):

    from contextlib import closing

    with closing(MyProblem(...)) as problem:
    optimize(problem)

The context manager ensures that {meth}`~cernml.coi.Problem.close` is called
under all circumstances – even if an exception occurs.
```

### Spaces

Optimization is always executed over a certain numeric *domain*, i.e. a space
of allowed values. These domains are encapsulated by Gym's concept of a
{class}`~gym.spaces.Space`. While Gym provides many different kinds of spaces
(discrete, continuous, aggregate, …), this package for now only supports
{class}`~gym.spaces.Box` for maximum portability. This restriction may be
lifted in the future.

In addition, box spaces are for now restricted to the bounds \[−1; 1\]. This
restriction, too, may be lifted in the future.

The interfaces make use of spaces as follows:

{attr}`SingleOptimizable.optimization_space<cernml.coi.SingleOptimizable.optimization_space>`
: the domain of valid inputs to
{meth}`~cernml.coi.SingleOptimizable.compute_single_objective`;

{class}`Env.action_space<gym.Env>`
: the domain of valid inputs to {meth}`~gym.Env.step`;

{class}`Env.observation_space<gym.Env>`
: the domain of valid observations returned by {meth}`~gym.Env.reset` and
{meth}`~gym.Env.step`.

### Control Flow for `SingleOptimizable`

The {class}`~cernml.coi.SingleOptimizable` interface provides two methods that
a host application can interact with:
{meth}`~cernml.coi.SingleOptimizable.get_initial_params` and
{meth}`~cernml.coi.SingleOptimizable.compute_single_objective`.

The {meth}`~cernml.coi.SingleOptimizable.get_initial_params` method should
return a reasonable point in phase space from where to start optimization. E.g.
this may be the current state of the machine; a constant, known-good point; or
a randomly-chosen point in phase space.

It must always be safe to call
{meth}`~cernml.coi.SingleOptimizable.compute_single_objective` directly with
the result of {meth}`~cernml.coi.SingleOptimizable.get_initial_params`.
Afterwards, an optimizer may choose any point in the phase space defined by the
{attr}`~cernml.coi.SingleOptimizable.optimization_space` and pass it to
{meth}`~cernml.coi.SingleOptimizable.compute_single_objective`. This will
typically happen in a loop until the optimizer has found a minimum of the
objective function.

Even after optimization is completed, a host application may call
{meth}`~cernml.coi.SingleOptimizable.compute_single_objective` again with the
value returned by {meth}`~cernml.coi.SingleOptimizable.get_initial_params`
before optimization. A use case is that optimization has failed and the user
wishes to reset the machine to the state before optimization.

In addition, this basic control flow can be interleaved arbitrarily with calls
to {meth}`~cernml.coi.Problem.render` in order to visualize progress to the
user.

Thus, typical control flow looks as follows:

```python
from cernml import coi

show_progress: bool = ...
optimizer = ...
problem = coi.make("MySingleOptimizableProblem-v0")
initial = params = problem.get_initial_params()

while not optimizer.is_done():
    loss = problem.compute_single_objective(params)
    params = optimizer.step(loss)
    if show_progress:
        problem.render(...)

if optimizer.has_failed():
    problem.compute_single_objective(initial)
```


### Control Flow for `Env`

The {class}`~gym.Env` interface provides three methods that a host application
can interact with: {meth}`~gym.Env.reset`, {meth}`~gym.Env.step` and
{meth}`~cernml.coi.Problem.close`. In contrast to
{class}`~cernml.coi.SingleOptimizable`, the {class}`~gym.Env` interface is
typically called many times in *episodes*, especially during training. Each
episode follows the same protocol.

The {meth}`~gym.Env.reset` method is called at the start of an episode. It
typically picks a random, known-bad initial state and clears any state from the
previous episode. It eventually must return an initial observation to seed the
agent. Though an environment may pick a constant initial state or re-use the
current state, (see [the above section](#control-flow-for-singleoptimizable)),
this is often reduces the amount of experience a reinforcement learner can
gather.

Afterwards, the host application calls an agent to decide on an action given
the current observation. This action is then passed to {meth}`~gym.Env.step`,
which must return a 4-tuple of the following values:


`obs`
: the next observation after the action has been applied;

`reward`
: the reward for the given action (a reinforcement learner's goal is to
maximize the expected cumulative reward over an episode);

`done`
: a boolean flag indicating whether the episode has ended;

`info`
: a dict mapping from strings to arbitrary values.

This is done in a loop until the episode is ended by passing a True value as
`done`. Once the episode is over, the host application will make no further
call to {meth}`~gym.Env.step` until the next episode is started via
{meth}`~gym.Env.reset`. A host application is also free to end an episode
prematurely, e.g. to call {meth}`~gym.Env.reset` before an episode is over.
There is no guarantee that any episode is ever driven to completion.

The `info` dict is free to return any additional information. There is
currently only one standardized key:

`"success"`
: a bool indicating whether the episode has ended by reaching a "good" terminal
state. Absence of this key may either mean that the episode hasn't ended, that
a "bad" terminal state has been reached, or that there is not difference
between terminal states.

The {meth}`~cernml.coi.Problem.close` method is called at the end of the
lifetime of an environment. No further calls to the environment will be made
afterwards. It should use this method to release any resources it has acquired
in its constructor.

In addition, this basic control flow can be interleaved arbitrarily with calls
to {meth}`~cernml.coi.Problem.render` in order to visualize progress to the
user.

Thus, typical control flow looks as follows:

```python
from cernml import coi
from contextlib import closing
from gym.wrappers import TimeLimit

show_progress: bool = ...
num_episodes: int = ...
agent = ...

# Use TimeLimit to prevent infinite loops.
env = TimeLimit(coi.make("MyEnv-v0"), 10)

with closing(env):
    for _ in range(num_episodes):
        done = False
        obs = env.reset()
        while not done:
            action = agent.predict(obs)
            obs, reward, done, info = env.step(action)
            if show_progress:
                env.render(...)
                display(reward, info, ...)
```


### Additional Restrictions

For maximum compatibility, this API puts the following *additional*
restrictions on environments:

- The {class}`observation_space<gym.Env>`, {class}`action_space<gym.Env>` and
  {attr}`~cernml.coi.SingleOptimizable.optimization_space` must all be
  {class}`gym.spaces.Box`es. The only exception is if the environment is a
  {class}`~gym.GoalEnv`: in that case, {class}`observation_space<gym.Env>` must
  be {class}`gym.spaces.Dict` (with exactly the three expected keys) and the
  `"observation"` sub-space must be a {class}`gym.spaces.Box`.
- The {class}`action_space<gym.Env>` and the
  {attr}`~cernml.coi.SingleOptimizable.optimization_space`  must have the same
  shape; They must only differ in their bounds. The bounds of the action space
  must be symmetric around zero and normalized (equal to or less than one).
- If the environment supports any rendering at all, it should support at least
  the render modes `human`, `ansi` and `matplotlib_figures`. The former two
  facilitate debugging and stand-alone usage, the latter makes it possible to
  embed the environment into a GUI.
- The environment metadata must contain a key `cern.machine` with a value of
  type {class}`~cernml.coi.Machine`. It tells users which CERN accelerator the
  environment belongs to.
- Rewards must always lie within the defined reward range and objectives within
  the defined objective range. Both ranges are unbounded by default.
- The problems must never diverge to NaN or infinity.

For the convenience of problem authors, this package provides a function
{func}`~cernml.coi.check` that verifies these requirements on a best-effort
basis. If you package your problem, we recommend adding a unit test to your
package that calls this function and exercise it on every CI job. See [the
Acc-Py guidelines on testing][Acc-Py-Testing] for more information.

[Acc-Py-Testing]: https://wikis.cern.ch/display/ACCPY/Testing

## Problem Registry

This package provides an *registry* similar to the one provided by Gym itself.
Every optimization problem that wants to be usable in a generic context should
register itself to it. The usage is as follows:

```python
from cernml.coi import OptEnv, register

class MyEnv(OptEnv):
    ...

register('mypackage:MyEnv-v0', entry_point=MyEnv)
```

This makes your environment known to "the world" and an environment management
application that imports your package knows how to find and interact with your
environment.

## Synchronization and Cancellation

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

### Synchronization

To solve the problem of synchronization, the COI provide the concept of
*parameter streams*. A stream is a combination of a PyJapc subscription
handler, a data queue, and synchronization logic between the two. It allows you
to subscribe to a JAPC parameter and wait for the next value to arrive:

```python
from pyjapc import PyJapc
from cernml.coi.unstable.japc_utils import subscribe_stream

japc = PyJapc("LHC.USER.ALL", noSet=True)
the_field = subscribe_stream(japc, "device/property#field")
# Blocks execution until the next value is there.
value, header = the_field.wait_next()
```

They allow you to get the next value without manually maintaining a queue and
sleeping for what you think is a reasonable time between cycles. This example
sets a JAPC parameter and then waits until the next cycle after the operation:

```python
from datetime import datetime, timezone
japc.setParam(...)
now = datetime.now(timezone.utc)
for value, header in iter(the_field.wait_next, None):
    if header.cycle_stamp > now:
        break
make_use(value)
```

See the {func}`~cernml.coi.unstable.japc_utils.subscribe_stream` docs for all
details.

```{warning}
Parameter streams are considered *unstable* and may change arbitrarily between
minor releases. The more users experiment with them, and the more feedback we
gather, the more likely they are to get stabilized soon.
```

### Cancellation

In order to cancel long-running data acquisition tasks, the COI have adopted
the concept of [cancellation tokens][C-Sharp Cancellation Tokens] from C#. A
cancellation token is a small object that is handed to your
{class}`~cernml.coi.Problem` subclass on which you may check whether the user
has requested a cancellation of your operation. If this is the case, you have
the ability to cleanly shut down operations – usually by raising an exception.

[C-Sharp Cancellation Tokens]: https://docs.microsoft.com/en-us/dotnet/standard/threading/cancellation-in-managed-threads

To use this feature, your problem must first declare that its support it by
setting the `cern.cancellable` [metadata](#metadata). When it does so, a host
application will pass a {class}`~cernml.coi.unstable.cancellation.Token` to the
constructor. On this token, the problem should check whether cancellation has
been requested whenever it enters a loop that may run for a long time.

This sounds complicated, but luckily, [parameter streams](#synchronization)
already support cancellation tokens:

```python
from cernml.coi
from cernml.coi.unstable.japc_utils import subscribe_stream

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
```

If you have your own data acquisition logic, you can use the token yourself by
regularly calling
{meth}`~cernml.coi.unstable.cancellation.Token.raise_if_cancellation_requested`
on it:

```python
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
```

If you write a host application yourself, you will usually want to create a
{class}`~cernml.coi.unstable.cancellation.TokenSource` and pass its token to
the optimization problem if it is cancellable:

```python
from threading import Thread
from cernml import coi
from cernml.coi.unstable import cancellation

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
        # can _definitely_ reuse the cancellation token source.
        token.complete_cancellation()
    finally:
        env.close()  # Never forget this!
```

## GoalEnv

```{digraph} inheritance_diagram
---
caption: "Fig. 2: Inheritance diagram of multi-goal environments"
---

rankdir = "BT";
bgcolor = "#00000000";
node [shape=record, fontname="Latin Modern Sans", style=filled, fillcolor="white"];
edge [style=dashed];

node[color=gray, fontcolor=gray];

problem[shape=rectangle, label=<cernml.coi.<b>Problem</b>>];
sopt[shape=rectangle, label=<cernml.coi.<b>SingleOptimizable</b>>];
env[shape=rectangle, label=<gym.<b>Env</b>>];
optenv[label=<cernml.coi.<b>OptEnv</b>>];

node[color=black, fontcolor=black];
goalenv[label=<{
    gym.<b>GoalEnv</b>|
    compute_reward(<i>achieved</i>: Obs, <i>desired</i>: Obs, <i>info</i>: Dict) → float}>,
];

optgoalenv[label=<cernml.coi.<b>OptGoalEnv</b>>];

optenv -> sopt -> problem;
optenv -> env -> problem;
optgoalenv -> goalenv -> env;
optgoalenv -> sopt;
```

Gym provides {class}`~gym.GoalEnv` as a specialization of {class}`~gym.Env`. To
accommodate it, this package also provides {class}`~cernml.coi.OptGoalEnv` as a
similar abstract base class for everything that inherits both from
{class}`~cernml.coi.SingleOptimizable` and from {class}`~gym.GoalEnv`.

## SeparableEnv

```{digraph} inheritance_diagram
---
caption: "Fig. 3: Inheritance diagram of the separable-environment interfaces"
---

rankdir = "BT";
bgcolor = "#00000000";
node [shape=record, fontname="Latin Modern Sans", style=filled, fillcolor="white"];
edge [style=dashed];

node[color=gray, fontcolor=gray];
env[shape=rectangle, label=<gym.<b>Env</b>>];
goalenv[label=<{
    gym.<b>GoalEnv</b>|
    compute_reward(<i>achieved</i>: Obs, <i>desired</i>: Obs, <i>info</i>: Dict) → float}>,
];

node[color=black, fontcolor=black];
sepenv[label=<{
    gym.<b>SeparableEnv</b>|
    compute_observation(<i>action</i>: Action, <i>info</i>: Dict) →
    float<br/>compute_reward(<i>achieved</i>: Obs, <i>desired</i>: None, <i>info</i>: Dict) → float<br/>compute_done(<i>achieved</i>: Obs, <i>reward</i>: float, <i>info</i>: Dict) → float}>,
];
sepgoalenv[label=<{
    gym.<b>SeparableGoalEnv</b>|
    compute_observation(<i>action</i>: Action, <i>info</i>: Dict) →
    float<br/>compute_done(<i>achieved</i>: Obs, <i>reward</i>: float, <i>info</i>: Dict) → float}>,
];

sepenv -> env;
sepgoalenv -> goalenv -> env;
```

Many environments in a particle accelerator context are very simple: their
rewards do not depend explictly on time and the end of the episode can be
determined in a side-effect-free manner.

Such environments may expose this fact through the
{class}`~cernml.coi.SeparableEnv` interface. This is useful to e.g. calculate
the reward that would correspond to the initial observation. (if there *were* a
reward to associate with it.)

The {class}`~cernml.coi.SeparableEnv` interface implements
{meth}`Env.step<cernml.coi.SeparableEnv.step>` for you by means of three new
abstract methods: {meth}`~cernml.coi.SeparableEnv.compute_observation`,
{meth}`~cernml.coi.SeparableEnv.compute_reward` and
{meth}`~cernml.coi.SeparableEnv.compute_done`.

Similarly, {class}`~cernml.coi.SeparableGoalEnv` adds
{meth}`~cernml.coi.SeparableGoalEnv.compute_observation` and
{meth}`~cernml.coi.SeparableGoalEnv.compute_done` in addition to the already
existing {meth}`~gym.GoalEnv.compute_reward`.

One quirk of this interface is that
{meth}`~cernml.coi.SeparableEnv.compute_reward` takes a dummy parameter
`desired` that must always be None. This is for compatibility with
{class}`~gym.GoalEnv`, ensuring that both methods have the same signature. This
makes it easier to write generic code that can handle both interfaces equally
well.

In an analogous manner to {class}`~cernml.coi.OptEnv`, convenience base classes
exist that combine each of the separable interfaces with
{class}`~cernml.coi.SingleOptimizable`. They are
{class}`~cernml.coi.SeparableOptEnv`, and
{class}`~cernml.coi.SeparableOptGoalEnv`.











