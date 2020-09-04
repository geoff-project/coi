#!/usr/bin/env python
"""An extension of Gym environments for DESY and CERN.

This module contains, first and foremost, the `MachineEnv` Gym environment.
This environment is not meant to be inherited from – instead, it uses several
abstract interfaces that the user should implement. These interfaces are geared
towards using reinforcement learning in particle accelerators and similar
machines. They make more assumptions that general Gym environments and thus
allow us to implement more common tasks on the user's behalf.

`MachineEnv` makes use of the following interfaces:

- `Machine`: An abstract interface between the RL problem and the machine to be
  controlled. (or a simulation of the machine) At its most fundamental, a
  machine has *settings* and each time these settings are changed, a new
  *measurement* is made.

- `GoalSpec`: A description of the optimization problem the RL agent shall
  solve. The point of this abstraction is that one might want to solve more
  than one optimization problem on a machine.

- `MeasurementEncoder`: A translator from machine-level *measurements* to RL
  agent-level *observations*. This may e.g. scale measurements into ranges that
  are suitable for machine learning. The translation may even be stateful.

- `ActionDecoder`: A translator from RL agent-level *actions* to machine-level
  *settings*. As for `MeasurementEncoder`, the translation may be stateful.

For more information about each interface, see their respective docstrings.
"""

from typing import List

import gym


class Machine:
    """An abstract description of the machine to interact with.

    This class serves two purposes: On the one hand, it communicates with the
    machine and provides a uniform interface to the RL agents; on the other
    hand, it implements those features of `gym.Env` that `MachineEnv` cannot
    reasonably implement itself.

    The attributes and methods that are taken over directly from `gym.Env` are:
    `metadata`, `render()`, `close()` and `seed()`. A default implementation of
    `seed()` is provided, so you should only override it if you use an RNG of
    your own.

    Communication with the machine is done through two methods:
    `apply_settings()` and `take_measurement()`. They separate the logic of
    `Env.step()` in a way that makes sense for particle accelerators.

    Settings and measurements should be as close to the raw values as
    reasonably possible, without accommodating machine learning. The
    translation between the physics domain and the ML domain is done through
    dedicated translators.

    Like `gym.Env`, this interface makes use of Gym spaces to declare the
    domains of measurements and settings. Translators may make use of this
    information, so ensure to be as accurate as possible when defining them.

    Note that *unlike* `gym.Env`, `Machine` has no notion of rewards. This is
    because in different scenarios, the optimization goal might differ as well.
    The concept of rewards is encapsulated in `GoalSpec`.
    """
    metadata = {'render.modes': []}
    settings_space: gym.Space = None
    measurements_space: gym.Space = None

    def apply_settings(self, settings):
        """Transmit the given settings to the machine.

        If the settings are invalid, e.g. out of range, the machine should
        reject them. A common implementation is to simply ignore invalid
        settings. Many RL agents handle this behavior without modifications.
        """
        raise NotImplementedError()

    def take_measurement(self):
        """Receive a measurement from the machine.

        Ideally, this is a stateless operation, i.e. taking two measurements
        without changing the settings should give approximately the same
        results.
        """
        raise NotImplementedError()

    def render(self, mode: str = 'human'):
        """Render the current state of the machine.

        This method is directly equivalent to `gym.Env.render()`. See there for
        details on the implementation.
        """
        # TODO: Should we define and/or require any specific render modes?
        raise NotImplementedError()

    def generate_new_settings(self):
        """Generate a new, possibly random set of settings.

        This function is used by `env.reset()`. By default, it simply
        samples the settings space. Another valid implementation would be to
        just return whatever the current settings of the machine are.

        Override this method only if you need a non-default distribution or if
        you need to communicate with the machine for this operation. If you
        override this method, consider using a non-global RNG that gets seeded
        in `self.seed()` to ensure reproducibility.
        """
        return self.settings_space.sample()

    def seed(self, seed: int = None) -> List[int]:
        """Set the seed for the machine's random number generators.

        This function is directly equivalent to `gym.Env.seed()`, except it
        provides a non-trivial implementation. By default, it forwards the call
        to `self.settings_space.seed()` and `self.measurements_space.seed()`.

        Only override this method if your implementation uses RNGs of its own.
        Consider calling the overridden method inside your own:

            >>> class MyMachine(Machine):
            ...     ...
            ...     def seed(self, seed=None):
            ...         seeds = super().seed(seed)
            ...         seeds.append(self.rng.seed(seed))
            ...         return seeds
        """
        seeds = self.settings_space.seed(seed)
        seeds.extend(self.measurements_space.seed(seed))
        return seeds

    def close(self):
        """Close the connection to the machine.

        If you have any cleanup to do, override this method. By default, it
        does nothing.
        """
