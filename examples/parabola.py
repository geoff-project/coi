#!/usr/bin/env python

# SPDX-FileCopyrightText: 2020-2023 CERN
# SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""An example implementation of the `OptEnv` interface."""

import argparse
import sys
import typing as t

import gym
import numpy as np
import scipy.optimize
from matplotlib import pyplot
from matplotlib.figure import Figure
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.td3 import TD3

from cernml import coi


class Parabola(coi.OptEnv):
    """Example implementation of `OptEnv`.

    The goal of this environment is to find the center of a 2D parabola.
    """

    # Domain declarations.
    observation_space = gym.spaces.Box(-2.0, 2.0, shape=(2,))
    action_space = gym.spaces.Box(-1.0, 1.0, shape=(2,))
    optimization_space = gym.spaces.Box(-2.0, 2.0, shape=(2,))
    reward_range = (-8.0, 0.0)
    objective_range = (0.0, 8.0)
    metadata = {
        # All `mode` arguments to `self.render()` that we support.
        "render.modes": ["ansi", "human", "matplotlib_figures"],
        # The example is independent of all CERN accelerators.
        "cern.machine": coi.Machine.NO_MACHINE,
        # No need for communication with CERN accelerators.
        "cern.japc": False,
        # Cancellation is important if you communicate with an
        # accelerator. There might be a bug in the machine and your
        # environment is waiting for data that will never arrive. In
        # such situations, it is good when the user gets a chance to
        # cleanly shut down your environment. Cancellation tokens solve
        # this problem.
        # That being said, we don't communicate with an accelerator, so
        # we don't need this feature here.
        "cern.cancellable": False,
    }

    # The radius at which an episode is ended. We employ "reward
    # dangling", i.e. we start with a very wide radius and restrict it
    # with each successful episode, up to a certain limit. This improves
    # training speed, as the agent gathers more positive feedback early
    # in the training.
    objective = -0.05
    max_objective = -0.003

    def __init__(self) -> None:
        self.pos = np.zeros(2)
        self._train = True
        self.figure: t.Optional[Figure] = None

    def train(self, train: bool = True) -> None:
        """Turn the environment's training mode on or off.

        If the training mode is on, reward dangling is active and each
        successful end of episode makes the objective stricter. If
        training mode is off, the objective remains constant.
        """
        self._train = train

    def reset(self) -> np.ndarray:
        # Don't use the full observation space for initial states.
        self.pos = self.action_space.sample()
        return self.pos.copy()

    def step(self, action: np.ndarray) -> t.Tuple[np.ndarray, float, bool, t.Dict]:
        next_pos = self.pos + action
        self.pos = np.clip(
            next_pos,
            self.observation_space.low,
            self.observation_space.high,
        )
        reward = -sum(self.pos**2)
        success = reward > self.objective
        done = success or next_pos not in self.observation_space
        info = {"success": success, "objective": self.objective}
        if self._train and success and self.objective < self.max_objective:
            self.objective *= 0.95
        return self.pos.copy(), reward, done, info

    def get_initial_params(self) -> np.ndarray:
        return self.reset()

    def compute_single_objective(self, params: np.ndarray) -> float:
        self.pos = np.clip(
            params,
            self.observation_space.low,
            self.observation_space.high,
        )
        loss = sum(self.pos**2)
        return loss

    def render(self, mode: str = "human") -> t.Any:
        if mode == "human":
            pyplot.figure()
            pyplot.scatter(*self.pos)
            pyplot.show()
            return None
        if mode == "matplotlib_figures":
            if self.figure is None:
                self.figure = Figure()
                axes = self.figure.subplots()
            else:
                [axes] = self.figure.axes
            axes.scatter(*self.pos)
            return [self.figure]
        if mode == "ansi":
            return str(self.pos)
        return super().render(mode)

    def seed(self, seed: t.Optional[int] = None) -> t.List[int]:
        return [
            *self.observation_space.seed(seed),
            *self.action_space.seed(seed),
            *self.optimization_space.seed(seed),
        ]


coi.register("Parabola-v0", entry_point=Parabola, max_episode_steps=10)


def run_episode(agent: BaseAlgorithm, env: coi.OptEnv) -> bool:
    """Run one episode of ``env`` and return the success flag."""
    obs = env.reset()
    done = False
    while not done:
        action, _ = agent.predict(obs)
        obs, _, done, info = env.step(action)
    return info.get("success", False)


def get_parser() -> argparse.ArgumentParser:
    """Return an `ArgumentParser` instance."""
    description, _, epilog = __doc__.partition("\n\n")
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
    )
    parser.add_argument(
        "mode",
        choices=("rl", "opt"),
        help="whether to run numerical optimization or reinforcement learning",
    )
    return parser


def main_rl(env: coi.OptEnv, num_runs: int) -> t.List[bool]:
    """Handler for `rl` mode."""
    agent = TD3("MlpPolicy", env, learning_rate=2e-3)
    agent.learn(total_timesteps=300)
    env.train(False)
    return [run_episode(agent, env) for _ in range(num_runs)]


def main_opt(env: coi.OptEnv, num_runs: int) -> t.List[bool]:
    """Handler for `opt` mode."""
    bounds = bounds = scipy.optimize.Bounds(
        env.optimization_space.low,
        env.optimization_space.high,
    )
    return [
        scipy.optimize.minimize(
            fun=env.compute_single_objective,
            x0=env.get_initial_params(),
            bounds=bounds,
        ).success
        for _ in range(num_runs)
    ]


def main(argv: t.List[str]) -> None:
    """Main function. Should be passed `sys.argv[1:]`."""
    args = get_parser().parse_args(argv)
    env = coi.make("Parabola-v0")
    coi.check(env)
    successes = {"rl": main_rl, "opt": main_opt}[args.mode](env, 100)
    print(f"Success rate: {np.mean(successes):.1%}")


if __name__ == "__main__":
    main(sys.argv[1:])
