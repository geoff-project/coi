#!/usr/bin/env python
"""Provides the `MeasurementEncoder` and `ActionDecoder` interfaces."""

import gym
from .machine import Machine

# TODO: Can or should be merge Encoder and Decoder into a single Codec class?
# On the one hand, merging would make these classes less pointlessly small; on
# the other hand, the user can always just inherit from both, as `Identity`
# shows.


class MeasurementEncoder:
    """A translator from `Machine` measurements to `gym` observations.

    Attributes:
        observation_space: A `gym.Space` that defines the structure and bounds
            of the observed variables. Environment wrappers frequently make use
            of this e.g. to normalize observations, so this definition should
            be accurate.
    """

    # pylint: disable=too-few-public-methods

    observation_space: gym.Space = None

    def encode_measurement(self, measurement, reset: bool = False):
        """Translate a measurement to an observation.

        Args:
            measurement: Return value of `Machine.take_measurement()`.
            reset: True if this is called from `Env.reset()`, False otherwise.

        Returns:
            observation: A value from inside `self.observation_space`.
        """
        raise NotImplementedError()


class ActionDecoder:
    """A translator from `gym` actions to `Machine` settings.

    Attributes:
        action_space: A `gym.Space` that defines the structure and bounds of
            the action variables. Environment wrappers frequently make use of
            this e.g. to normalize actions, so this definition should be
            accurate.
    """

    # pylint: disable=too-few-public-methods

    action_space: gym.Space = None

    def reset_with_settings(self, settings):
        """Reset any state this decoder might have. Called by `env.reset()`.

        The default implementation does nothing.

        Args:
            settings: The new settings that the machine has taken on.
        """

    def decode_action(self, action):
        """Translate an action to a set of settings.

        Args:
            action: Action taken by the RL agent.

        Returns:
            settings: Argument to `Machine.apply_settings()`.
        """
        raise NotImplementedError()


class StatelessMeasurementEncoder(MeasurementEncoder):
    """Wrapper to turn stateless functions into `MeasurementEncoder`s.

    Usage:
        >>> from gym.spaces import Box
        >>> def scale(measurement):
        ...     return numpy.asarray(measurement) / 1e2
        >>> scale = StatelessMeasurementEncoder(scale, Box(-1, 1, (5,)))

    Args:
        func: A callable with signature `func(measurement) -> observation`.
        observation_space: The observation space of the encoder.
    """

    # TODO: Find a shorter name.

    def __init__(self, func, observation_space):
        super().__init__()
        self.func = func
        self.observation_space = observation_space

    def encode_measurement(self, measurement, reset=False):
        return self.func(measurement)

    __call__ = encode_measurement

    @classmethod
    def with_space(cls, observation_space):
        """Decorator that allows specifying the observation space.

        Usage:
            >>> from gym.spaces import Box
            >>> @StatelessMeasurementEncoder.with_space(Box(-1, 1, (5,)))
            ... def scale(measurement):
            ...     return numpy.asarray(measurement) / 1e2
        """
        return lambda func: cls(func, observation_space)


class StatelessActionDecoder(ActionDecoder):
    """Wrapper to turn stateless functions into `ActionDecoder`s.

    Usage:
        >>> def scale(action):
        ...     return numpy.asarray(action) * 1e2
        >>> scale = StatelessActionDecoder(scale, gym.spaces.Box(-1, 1, (5,)))

    Args:
        func: A callable with signature `func(action) -> settings`.
        action_space: The action space of the decoder.
    """

    # TODO: Find a shorter name.
    def __init__(self, func, action_space):
        super().__init__()
        self.func = func
        self.action_space = action_space

    def decode_action(self, action):
        return self.func(action)

    __call__ = decode_action

    @classmethod
    def with_space(cls, action_space):
        """Decorator that allows specifying the action space.

        Usage:
            >>> @StatelessActionDecoder.with_space(gym.spaces.Box(-1, 1, (5,)))
            ... def scale(measurement):
            ...     return numpy.asarray(measurement) * 1e2
        """
        return lambda func: cls(func, action_space)


class IncrementalActionDecoder(ActionDecoder):
    """A wrapper that makes an action decoder incremental.

    "Incremental" means that this decoder keeps track of the current settings.
    The result of `decoder.decode(action)` is _not_ understood as a setting,
    but rather as an _increment_ to the current settings.

    Every time `decode_action()` is called, the inner decoder is called to
    translate the action to an increment, which is added to the current
    settings. The current settings are then returned. This makes this decoder
    inherently stateful.
    """

    # TODO: Should we keep track of settings or of actions? In other words,
    # should we do `decode(action) + current_settings` or `decode(action +
    # current_action)`?
    def __init__(self, decoder):
        self._decoder = decoder
        self.action_space = decoder.action_space
        self.settings = None

    @property
    def unwrapped(self):
        """The wrapped decoder."""
        return self._decoder

    def reset_with_settings(self, settings):
        self._decoder.reset_with_settings(settings)
        self.settings = settings.copy()

    def decode_action(self, action):
        settings_increment = self._decoder.decode_action(action)
        self.settings += settings_increment
        return self.settings.copy()


class Identity(MeasurementEncoder, ActionDecoder):
    """An encoder and decoder that does nothing.

    Args:
        machine: The `Machine` that this identity is applied to. This is used
            to determine observation space and action space.
    """
    def __init__(self, machine: Machine):
        super().__init__()
        self.observation_space = machine.measurements_space
        self.action_space = machine.action_space

    def encode_measurement(self, measurement, reset=False):
        return measurement

    def decode_action(self, action):
        return action
