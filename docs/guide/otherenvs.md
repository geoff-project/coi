# Other Interfaces

This section introduces a few useful, but less common interfaces defined by Gym
and the COI.

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
*desired* that must always be None. This is for compatibility with
{class}`~gym.GoalEnv`, ensuring that both methods have the same signature. This
makes it easier to write generic code that can handle both interfaces equally
well.

In an analogous manner to {class}`~cernml.coi.OptEnv`, convenience base classes
exist that combine each of the separable interfaces with
{class}`~cernml.coi.SingleOptimizable`. They are
{class}`~cernml.coi.SeparableOptEnv`, and
{class}`~cernml.coi.SeparableOptGoalEnv`.
