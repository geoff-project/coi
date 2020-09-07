#!/usr/bin/env python
"""An example implementation of the `OptEnv` interface."""

import sys
import argparse

import gym
import gym.wrappers
import numpy as np
import scipy.optimize
from stable_baselines3 import TD3

from cern.env_interfaces import OptEnv


class Parabola(OptEnv):
    """Example implementation of `OptEnv`.

    The goal of this environment is to find the center of a 2D parabola.
    """
    # Domain declarations.
    observation_space = gym.spaces.Box(-2.0, 2.0, shape=(2, ))
    action_space = gym.spaces.Box(-1.0, 1.0, shape=(2, ))
    optimization_space = gym.spaces.Box(-2.0, 2.0, shape=(2, ))
    reward_range = (-np.sqrt(8.0), 0.0)

    # The radius at which an episode is ended. We employ "reward dangling",
    # i.e. we start with a very wide radius and restrict it with each
    # successful episode, up to a certain limit. This improves training speed,
    # as the agent gathers more positive feedback early in the training.
    objective = -0.05
    max_objective = -0.003

    def __init__(self):
        self.pos = np.zeros(2)
        self._train = True

    def train(self, train=True):
        """Turn the environment's training mode on or off.

        If the training mode is on, reward dangling is active and each
        successful end of episode makes the objective stricter. If training
        mode is off, the objective remains constant.
        """
        self._train = train

    def reset(self):
        # Don't use the full observation space for initial states.
        self.pos = self.action_space.sample()
        return self.pos.copy()

    def step(self, action):
        self.pos += action
        reward = -sum(self.pos**2)
        success = reward > self.objective
        done = success or self.pos not in self.observation_space
        info = dict(success=success, objective=self.objective)
        if self._train and success and self.objective < self.max_objective:
            self.objective *= 0.95
        return self.pos.copy(), reward, done, info

    def compute_loss(self, parameters):
        self.pos = parameters
        loss = sum(self.pos**2)
        return loss

    def render(self, mode='human'):
        return str(self.pos)

    def seed(self, seed=None):
        return [
            *self.observation_space.seed(seed),
            *self.action_space.seed(seed),
            *self.optimization_space.seed(seed),
        ]


def run_episode(agent, env):
    """Run one episode of the given environment and return the success flag."""
    obs = env.reset()
    done = False
    while not done:
        action, _ = agent.predict(obs)
        obs, _, done, info = env.step(action)
    return info.get('success', False)


def get_parser():
    """Return an `ArgumentParser` instance."""
    description, _, epilog = __doc__.partition('\n\n')
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
    )
    parser.add_argument(
        'mode',
        choices=('rl', 'opt'),
        help='whether to run numerical optimization or reinforcement learning',
    )
    return parser


def main_rl(env: OptEnv):
    """Handler for `rl` mode."""
    num_runs = 100
    env = gym.wrappers.TimeLimit(env, max_episode_steps=10)
    agent = TD3('MlpPolicy', env, learning_rate=2e-3)
    agent.learn(total_timesteps=300)
    env.train(False)
    successes = [run_episode(agent, env) for _ in range(num_runs)]
    print(f'Number of runs: {num_runs}')
    print(f'Success rate: {np.mean(successes):.1%}')


def main_opt(env: OptEnv):
    """Handler for `opt` mode."""
    num_runs = 100
    bounds = bounds = scipy.optimize.Bounds(
        env.optimization_space.low,
        env.optimization_space.high,
    )
    successes = [
        scipy.optimize.minimize(
            fun=env.compute_loss,
            x0=env.optimization_space.sample(),
            bounds=bounds,
        ).success for _ in range(num_runs)
    ]
    print(f'Number of runs: {num_runs}')
    print(f'Success rate: {np.mean(successes):.1%}')


def main(args):
    """Main function. Should be passed `sys.argv[1:]`."""
    args = get_parser().parse_args(args)
    env = Parabola()
    dict(rl=main_rl, opt=main_opt)[args.mode](env)


if __name__ == '__main__':
    main(sys.argv[1:])
