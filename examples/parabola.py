#!/usr/bin/env python
"""An example implementation of the `OptEnv` interface."""

import sys
import argparse
import warnings

import gym
import gym.wrappers
import numpy as np
import scipy.optimize
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import stable_baselines

from cdao_interfaces import OptEnv


class Parabola(OptEnv):
    """Example implementation of `OptEnv`.

    The goal of this environment is to find the center of a 2D parabola.
    """
    observation_space = gym.spaces.Box(-1.0, 1.0, shape=(2, ))
    action_space = gym.spaces.Box(-1.0, 1.0, shape=(2, ))
    opt_action_space = observation_space
    reward_range = (-np.inf, 0.0)

    def __init__(self):
        self.x = np.zeros(2)  # pylint: disable=invalid-name

    def reset(self):
        self.x = self.opt_action_space.sample()
        return self.x.copy()

    def step(self, action):
        new_x = self.x + action
        reward = -sum(new_x**2)
        if new_x in self.observation_space:
            self.x = new_x
        obs = self.x.copy()
        done = reward > -0.01
        return obs, reward, done, {}

    def step_opt(self, opt_action):
        if opt_action in self.opt_action_space:
            self.x = opt_action
        reward = -sum(opt_action**2)
        return reward

    def render(self, mode='human'):
        return str(self.x)

    def seed(self, seed=None):
        seeds = self.observation_space.seed(seed)
        seeds.extend(self.action_space.seed(seed))
        seeds.extend(self.opt_action_space.seed(seed))
        return seeds


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
    env = gym.wrappers.TimeLimit(env, max_episode_steps=10)
    agent = stable_baselines.TD3(
        'MlpPolicy',
        env,
        learning_rate=1e-2,
        learning_starts=50,
    )
    agent.learn(total_timesteps=300)
    obs = env.reset()
    done = False
    trajectory = [obs]
    while not done:
        action, _ = agent.predict(obs)
        obs, _, done, info = env.step(action)
        trajectory.append(obs)
    print('Success:', not info.get('TimeLimit.truncated', False))
    print('x:', env.unwrapped.x)


def main_opt(env: OptEnv):
    """Handler for `opt` mode."""
    res = scipy.optimize.minimize(
        fun=lambda x: -env.step_opt(x),
        x0=env.opt_action_space.sample(),
        bounds=scipy.optimize.Bounds(
            env.opt_action_space.low,
            env.opt_action_space.high,
        ),
    )
    print('Success:', res.success)
    print('x:', res.x)
    print(res.message)


def main(args):
    """Main function. Should be passed `sys.argv[1:]`."""
    args = get_parser().parse_args(args)
    env = Parabola()
    dict(rl=main_rl, opt=main_opt)[args.mode](env)


if __name__ == '__main__':
    main(sys.argv[1:])
