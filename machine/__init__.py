#!/usr/bin/env python
"""An extension of Gym environments for DESY and CERN.

This package contains, first and foremost, the `MachineEnv` Gym environment.
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

import gym
from .machine import Machine
from .goalspec import GoalSpec
from .codecs import MeasurementEncoder, ActionDecoder


class MachineEnv(gym.Env):
    """An interface between accelerator machines and RL agents.

    This class wraps up the various interfaces defined in this package and
    implements a Gym environment that uses them. This environment can be used
    as any other to train reinforcement learning agents.

    Args:
        machine: An interface to the concrete machine.
        goal: The optimization goal.
        obscode: A translator between machine measurements and RL observations.
        actcode: A translator between RL actions and machine settings.
    """
    def __init__(self, machine: Machine, goal: GoalSpec,
                 obscode: MeasurementEncoder, actcode: ActionDecoder):
        super().__init__()
        self._machine = machine
        self._goal = goal
        self._obscode = obscode
        self._actcode = actcode
        self.metadata = machine.metadata

    @property
    def observation_space(self) -> gym.Space:
        """The observation space as defined by the `MeasurementEncoder`."""
        return self._obscode.observation_space

    @property
    def action_space(self) -> gym.Space:
        """The action space as defined by the `ActionDecoder`."""
        return self._actcode.action_space

    @property
    def reward_range(self) -> (float, float):
        """The reward range as defined by the `GoalSpec`."""
        return self._goal.reward_range

    def reset(self):
        settings = self._machine.generate_new_settings()
        self._machine.apply_settings(settings)
        measurement = self._machine.take_measurement()
        self._actcode.reset_with_settings(settings)
        obs = self._obscode.encode_measurement(measurement, True)
        return obs

    def step(self, action):
        settings = self._actcode.decode_action(action)
        self._machine.apply_settings(settings)
        measurement = self._machine.take_measurement()
        info = dict(settings=settings, measurement=measurement)
        obs = self._obscode.encode_measurement(measurement, False)
        reward, done = self._goal.evaluate(measurement, info)
        return obs, reward, done, info

    def render(self, mode: str = 'human'):
        return self._machine.render(mode)

    def seed(self, seed=None):
        seeds = self._machine.seed(seed)
        seeds.extend(self._obscode.seed(seed))
        seeds.extend(self._actcode.seed(seed))
        return seeds

    def close(self):
        return self._machine.close()
