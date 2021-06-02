# Separable and Goal-Based Interfaces

```{eval-rst}
.. class:: gym.GoalEnv

    Bases: :class:`gym.Env`

    A goal-based environment. It functions just as any regular OpenAI Gym
    environment but it imposes a required structure on the
    :attr:`~gym.Env.observation_space`. More concretely, the observation space
    is required to contain at least three elements, namely *observation*,
    *desired_goal*, and *achieved_goal*. Here, *desired_goal* specifies the
    goal that the agent should attempt to achieve. *achieved_goal* is the goal
    that it currently achieved instead. The *observation* contains the actual
    observations of the environment as per usual.

    .. method:: compute_reward(achieved_goal: numpy.ndarray, desired_goal: numpy.ndarray, info: dict) -> float

        Compute the step reward. This externalizes the reward function and
        makes it dependent on a desired goal and the one that was achieved. If
        you wish to include additional rewards that are independent of the
        goal, you can include the necessary values to derive it in *info* and
        compute it accordingly.

        :param achieved_goal: The goal that was achieved during execution.
        :param desired_goal: The desired goal that we asked the agent to
            attempt to achieve.
        :param info: An info dictionary with additional information.

        :return: The reward that corresponds to the provided achieved goal
            w.r.t. to the desired goal.

        .. note::

            The following should always hold true::

                ob, reward, done, info = env.step()
                assert reward == env.compute_reward(ob['achieved_goal'], ob['goal'], info)

.. autoclass:: cernml.coi.SeparableEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SeparableGoalEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.OptEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.OptGoalEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SeparableOptEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SeparableOptGoalEnv
    :members:
    :show-inheritance:
```
