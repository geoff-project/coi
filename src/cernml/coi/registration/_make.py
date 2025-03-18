# SPDX-FileCopyrightText: 2016 OpenAI
# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2022 - 2025 Farama Foundation
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Dedicated module for `cernml.coi.make()` because it's honestly a lot of code."""

from __future__ import annotations

import typing as t
import warnings
from copy import deepcopy
from itertools import zip_longest

from gymnasium import Env, Wrapper, wrappers

from . import _base, errors
from ._spec import EnvSpec

if t.TYPE_CHECKING:
    from .. import protocols

__all__ = ("make",)


def make(
    env_spec: EnvSpec,
    /,
    *,
    max_episode_steps: int | None = None,
    autoreset: bool | None = None,
    apply_api_compatibility: bool | None = None,
    disable_env_checker: bool | None = None,
    order_enforce: bool | None = None,
    **kwargs: t.Any,
) -> protocols.Problem:
    """Reimplementation of `gymnasium.make`.

    This implementation differs from the canonical one in `gymnasium` in
    a few ways that are necessary for our goal of compatibility. Please
    see the package documentation at `cernml.coi.registration` for
    a comprehensive list of changes.
    """
    stacklevel = kwargs.pop("stacklevel", 2)
    apply_api_compatibility = (
        apply_api_compatibility
        if apply_api_compatibility is not None
        else env_spec.apply_api_compatibility
    )
    disable_env_checker = (
        disable_env_checker
        if disable_env_checker is not None
        else env_spec.disable_env_checker
    )
    order_enforce = (
        order_enforce if order_enforce is not None else env_spec.order_enforce
    )
    max_episode_steps = (
        max_episode_steps
        if max_episode_steps is not None
        else env_spec.max_episode_steps
    )
    autoreset = autoreset if autoreset is not None else env_spec.autoreset
    env_creator = _get_env_creator(env_spec)
    metadata = _get_env_creator_metadata(env_creator)
    kwargs = deepcopy(env_spec.kwargs) | kwargs
    if apply_api_compatibility:
        flags = _deduce_render_mode(
            kwargs.pop("render_mode", None),
            metadata=metadata,
            stacklevel=1 + stacklevel,
        )
    elif "render_mode" in kwargs:
        flags = _deduce_render_mode(
            kwargs["render_mode"], metadata=metadata, stacklevel=1 + stacklevel
        )
        kwargs["render_mode"] = flags.render_mode
    else:
        # Don"t set kwargs["render_mode'] if it didn't exist previously.
        flags = _deduce_render_mode(None, metadata=metadata, stacklevel=1 + stacklevel)
    env = _create_env(
        env_spec,
        env_creator,
        kwargs=kwargs,
        apply_human_rendering=flags.apply_human_rendering,
    )
    return _add_wrappers(
        env,
        disable_env_checker=disable_env_checker,
        order_enforce=order_enforce,
        autoreset=autoreset,
        apply_api_compatibility=apply_api_compatibility,
        compatibility_render_mode=flags.render_mode,
        apply_human_rendering=flags.apply_human_rendering,
        apply_render_collection=flags.apply_render_collection,
        max_episode_steps=max_episode_steps,
        additional_wrappers=env_spec.additional_wrappers,
        stacklevel=1 + stacklevel,
    )


def _get_env_creator(spec: EnvSpec) -> _base.EnvCreator:
    if spec.entry_point is None:
        raise errors.EntryPointError(
            f"{spec.id} registered but entry_point is not specified"
        )
    if callable(spec.entry_point):
        return spec.entry_point
    return t.cast(_base.EnvCreator, _base.load_env_creator(spec.entry_point))


def _get_env_creator_metadata(env_creator: _base.EnvCreator) -> t.Mapping[str, t.Any]:
    metadata = getattr(env_creator, "metadata", {})
    return metadata if isinstance(metadata, t.Mapping) else {}


class _WrapperFlags(t.NamedTuple):
    render_mode: str | None
    apply_human_rendering: bool = False
    apply_render_collection: bool = False


def _deduce_render_mode(
    requested_render_mode: str | None,
    *,
    metadata: t.Mapping[str, t.Any],
    stacklevel: int,
) -> _WrapperFlags:
    supported_render_modes = _get_render_modes(metadata, stacklevel=1 + stacklevel)
    if (
        requested_render_mode is None
        or supported_render_modes is None
        or requested_render_mode in supported_render_modes
    ):
        return _WrapperFlags(requested_render_mode)
    displayable_modes = {"rgb_array", "rgb_array_list"}.intersection(
        supported_render_modes
    )
    if requested_render_mode == "human" and displayable_modes:
        warnings.warn(
            errors.HumanRenderingWarning(
                supported_modes=frozenset(supported_render_modes)
            ),
            stacklevel=stacklevel,
        )
        return _WrapperFlags(displayable_modes.pop(), apply_human_rendering=True)
    no_list_mode = requested_render_mode.removesuffix("_list")
    if requested_render_mode != no_list_mode and no_list_mode in supported_render_modes:
        return _WrapperFlags(no_list_mode, apply_render_collection=True)
    warnings.warn(
        errors.RenderModeWarning(
            selected_mode=requested_render_mode,
            supported_modes=frozenset(supported_render_modes),
        ),
        stacklevel=stacklevel,
    )
    return _WrapperFlags(requested_render_mode)


def _get_render_modes(
    metadata: t.Mapping[str, t.Any], stacklevel: int
) -> tuple[str, ...]:
    modes = metadata.get("render.modes", None)
    if modes is not None:
        warnings.warn(
            errors.GymDeprecationWarning(
                "metadata key 'render.modes'", "'render_modes'"
            ),
            stacklevel=stacklevel,
        )
        # Try to fix the mistake, but continue as usual if that's not
        # possible.
        try:
            return tuple(t.cast(dict, metadata).setdefault("render_modes", modes))
        except AttributeError:  # pragma: no cover
            return tuple(modes)
    return tuple(metadata.get("render_modes", ()))


def _create_env(
    spec: EnvSpec,
    creator: _base.EnvCreator,
    *,
    kwargs: dict[str, t.Any],
    apply_human_rendering: bool,
) -> protocols.Problem:
    try:
        env = t.cast("protocols.Problem", creator(**kwargs))
    except TypeError as exc:
        if (
            apply_human_rendering
            and str(exc).find("got an unexpected keyword argument 'render_mode'") >= 0
        ):
            raise errors.HumanRenderingError(spec.id) from exc
        raise
    # Inner-most spec is minimal: since we're going to handle flags like
    # `max_episode_steps` or `apply_api_compatibility`, they can be set
    # to their default values inside the env.
    vars(env.unwrapped)["spec"] = EnvSpec(
        id=spec.id,
        entry_point=spec.entry_point,
        reward_threshold=spec.reward_threshold,
        nondeterministic=spec.nondeterministic,
        max_episode_steps=None,
        order_enforce=False,
        autoreset=False,
        disable_env_checker=True,
        apply_api_compatibility=False,
        kwargs=kwargs,
        additional_wrappers=(),
        vector_entry_point=spec.vector_entry_point,
    )
    return env


def _add_wrappers(
    env: protocols.Problem,
    *,
    disable_env_checker: bool,
    autoreset: bool,
    order_enforce: bool,
    apply_api_compatibility: bool,
    compatibility_render_mode: str | None = None,
    apply_human_rendering: bool,
    apply_render_collection: bool,
    max_episode_steps: int | None,
    additional_wrappers: tuple[_base.WrapperSpec, ...],
    stacklevel: int,
) -> protocols.Problem:
    assert env.spec is not None
    num_prior_wrappers = len(env.spec.additional_wrappers)
    prior_wrappers = additional_wrappers[:num_prior_wrappers]
    extra_wrappers = additional_wrappers[num_prior_wrappers:]
    _verify_prior_wrappers(expected=prior_wrappers, actual=env.spec.additional_wrappers)
    if apply_api_compatibility:
        warnings.warn(
            errors.GymDeprecationWarning("apply_api_compatibility"),
            stacklevel=stacklevel,
        )
        env = _wrap_compatibility(env, compatibility_render_mode)
    if not disable_env_checker:
        env = _wrap_if_env(env, wrappers.PassiveEnvChecker)
    if order_enforce:
        env = _wrap_if_env(env, wrappers.OrderEnforcing)
    if max_episode_steps is not None:
        env = _wrap_if_env(env, wrappers.TimeLimit, max_episode_steps)
    if autoreset:
        warnings.warn(errors.GymDeprecationWarning("autoreset"), stacklevel=stacklevel)
        env = _wrap_if_env(env, wrappers.AutoResetWrapper)
    for wrapper_spec in extra_wrappers:
        if wrapper_spec.kwargs is None:
            raise errors.WrapperClassError(wrapper_spec.name)
        wrapper = t.cast(
            _base.EnvCreator, _base.load_env_creator(wrapper_spec.entry_point)
        )
        env = wrapper(env=env, **wrapper_spec.kwargs)
    if apply_human_rendering:
        env = wrappers.HumanRendering(t.cast(Env, env))
    if apply_render_collection:
        env = _wrap_if_env(env, wrappers.RenderCollection)
    # TODO: Wrappers for SingleOptimizable and FunctionOptimizable.
    # https://gitlab.cern.ch/geoff/cernml-coi/-/issues/13
    return env


def _verify_prior_wrappers(
    *,
    expected: tuple[_base.WrapperSpec, ...],
    actual: tuple[_base.WrapperSpec, ...],
) -> None:
    for exp_spec, act_spec in zip_longest(expected, actual, fillvalue=None):
        if act_spec is None:  # pragma: no cover
            raise RuntimeError(
                "unreachable: `expected[:len(actual)]` cannot be longer than `actual`"
            )
        if exp_spec is None:
            assert act_spec is not None
            raise errors.WrapperUnexpectedError(act_spec)
        if exp_spec != act_spec:
            raise errors.WrapperMismatchError(expected=exp_spec, actual=act_spec)


def _wrap_compatibility(env: protocols.Problem, render_mode: str | None) -> Env:
    if not isinstance(env, wrappers.compatibility.LegacyEnv):
        raise errors.ApiCompatError(problem=env)
    return wrappers.EnvCompatibility(env, render_mode)


P = t.TypeVar("P", bound="protocols.Problem")


def _wrap_if_env(env: P, wrap_class: type[Wrapper], *args: t.Any) -> P | Env:
    if isinstance(env, Env):
        return wrap_class(env, *args)
    return env
