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

```{toctree}
---
maxdepth: 2
---

core
registry
cancellation
otherenvs
funcopt
```
