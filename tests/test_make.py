# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test `cernml.coi.make()`."""

from __future__ import annotations

import typing as t
from unittest.mock import DEFAULT, Mock, call

import gymnasium as gym
import pytest

from cernml.coi.registration import EnvSpec, WrapperSpec, errors


@pytest.fixture
def entry_point(request: pytest.FixtureRequest) -> Mock:
    marker: pytest.Mark | None = request.node.get_closest_marker("render_modes")
    ep = Mock(name="entry_point")
    ep.metadata = {
        "render_modes": list(marker.args) if marker else [],
        "render_fps": 60,
    }
    ep.return_value.metadata = ep.metadata
    ep.return_value.unwrapped = ep.return_value

    def __init__(render_mode: str | None = None) -> object:
        ep.return_value.render_mode = render_mode
        return DEFAULT

    ep.side_effect = __init__
    return ep


def test_make(entry_point: Mock) -> None:
    # Given:
    spec = EnvSpec(
        "ns/name-v1",
        entry_point=entry_point,
        order_enforce=False,
        disable_env_checker=True,
    )
    # When:
    res = spec.make()
    # Then:
    assert res == entry_point.return_value
    entry_point.assert_called_once_with(render_mode=None)


def test_import(entry_point: Mock, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given:
    import_module = Mock(name="importlib.import_module")
    spec = EnvSpec(
        "ns/name-v1",
        entry_point="modname:entry_point",
        order_enforce=False,
        disable_env_checker=True,
    )
    import_module.return_value.entry_point = entry_point
    entry_point.metadata.clear()
    monkeypatch.setattr("importlib.import_module", import_module)
    # When:
    res = spec.make()
    # Then:
    assert res == entry_point.return_value
    import_module.assert_called_once_with("modname")
    entry_point.assert_called_once_with(render_mode=None)


def test_require_entry_point() -> None:
    with pytest.raises(errors.EntryPointError):
        EnvSpec("ns/name-v1").make()


def test_api_compat_requires_legacy_env(entry_point: Mock) -> None:
    # We _have_ to add a spec here! Protocol before Python 3.12 used
    # `getattr()` instead of `inspect.getattr_static()` and so `Mock`
    # objects would match any protocol.
    entry_point.return_value.mock_add_spec(object)
    spec = EnvSpec(
        "ns/name-v1",
        entry_point=entry_point,
        order_enforce=False,
        disable_env_checker=True,
        apply_api_compatibility=True,
    )
    with (
        pytest.raises(errors.ApiCompatError),
        pytest.warns(errors.GymDeprecationWarning),
    ):
        spec.make()


@pytest.mark.render_modes("rgb_array")
def test_ignore_non_env_wrappers(entry_point: Mock) -> None:
    # Given:
    spec = EnvSpec(
        "ns/name-v1",
        entry_point=entry_point,
        autoreset=True,
        max_episode_steps=10,
        order_enforce=True,
        disable_env_checker=False,
    )
    # When:
    with pytest.warns(errors.GymDeprecationWarning, match="autoreset"):
        env = spec.make(render_mode="rgb_array_list")
    # Then:
    assert env == entry_point.return_value


@pytest.mark.render_modes("rgb_array")
def test_all_wrappers(entry_point: Mock) -> None:
    # Given:
    spec = EnvSpec(
        "ns/name-v1",
        entry_point=entry_point,
        autoreset=True,
        max_episode_steps=10,
        order_enforce=True,
        disable_env_checker=False,
        apply_api_compatibility=True,
    )
    env = Mock(
        gym.wrappers.compatibility.LegacyEnv,
        name="Env",
        observation_space=Mock(gym.Space, name="observation_space"),
        action_space=Mock(gym.Space, name="action_space"),
    )
    env.spec = spec
    env.unwrapped = env
    entry_point.return_value = env
    # When:
    with pytest.warns(DeprecationWarning):
        wrapped = spec.make(render_mode="rgb_array_list")
    # Then:
    # Extra `.env` to unwrap the `EnvCompatibility`, which isn't really
    # a wrapper.
    assert wrapped.unwrapped.env == entry_point.return_value  # type: ignore[attr-defined]
    wrapper_types = []
    while inner := getattr(wrapped, "env", None):
        wrapper_types.append(type(wrapped))
        wrapped = inner
    assert wrapper_types == [
        gym.wrappers.RenderCollection,
        gym.wrappers.AutoResetWrapper,
        gym.wrappers.TimeLimit,
        gym.wrappers.OrderEnforcing,
        gym.wrappers.PassiveEnvChecker,
        gym.wrappers.EnvCompatibility,
    ]


@pytest.mark.parametrize("render_mode", ["unknown", "rgb_array"])
def test_no_render_compat(render_mode: str) -> None:
    ep = Mock(name="entry_point")
    ep.metadata = {"render_modes": [render_mode]}
    ep.side_effect = TypeError("got an unexpected keyword argument 'render_mode'")
    warning, error = (
        (errors.HumanRenderingWarning, errors.HumanRenderingError)
        if render_mode == "rgb_array"
        else (errors.RenderModeWarning, TypeError)
    )
    with pytest.warns(warning), pytest.raises(error):
        EnvSpec("ns/name-v1", entry_point=ep).make(render_mode="human")


@pytest.mark.render_modes("rgb_array")
def test_human_rendering(entry_point: Mock) -> None:
    # Given:
    spec = EnvSpec(
        "ns/name-v1",
        entry_point=entry_point,
        order_enforce=False,
        disable_env_checker=True,
    )
    # When:
    with pytest.warns(errors.HumanRenderingWarning):
        res = spec.make(render_mode="human")
    # Then:
    assert isinstance(res, gym.wrappers.HumanRendering)
    assert res.env == entry_point.return_value


@pytest.mark.render_modes("rgb_array")
def test_warn_old_render_modes_key(entry_point: Mock) -> None:
    entry_point.metadata["render.modes"] = entry_point.metadata.pop("render_modes")
    spec = EnvSpec(
        "ns/name-v1",
        entry_point=entry_point,
        order_enforce=False,
        disable_env_checker=True,
    )
    # When:
    with (
        pytest.warns(errors.GymDeprecationWarning, match="'render\\.modes'"),
        pytest.warns(errors.HumanRenderingWarning),
    ):
        res = spec.make(render_mode="human")
    # Then:
    assert isinstance(res, gym.wrappers.HumanRendering)
    assert res.env == entry_point.return_value


def test_extra_wrappers(entry_point: Mock, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given:
    wrap = Mock(name="wrap")
    wrap.return_values = []

    def __new__(env: Mock, **kwargs: object) -> object:
        res = Mock(name=f"wrap({wrap.call_count})", env=env, unwrapped=env.unwrapped)
        wrap.return_values.append(res)
        return res

    wrap.side_effect = __new__
    spec = EnvSpec(
        "ns/name-v1",
        entry_point=entry_point,
        order_enforce=False,
        disable_env_checker=True,
        additional_wrappers=(
            WrapperSpec("InnerWrapper", "innermod:wrapper_entry_point", {}),
            WrapperSpec("OuterWrapper", "outermod:wrapper_entry_point", {"kwarg": 1}),
        ),
    )
    import_module = Mock(name="importlib.import_module")
    import_module.return_value.wrapper_entry_point = wrap
    monkeypatch.setattr("importlib.import_module", import_module)
    # When:
    env = t.cast(Mock, spec.make())
    # Then:
    assert env == wrap.return_values[1]
    assert env.env == wrap.return_values[0]
    assert env.env.env == entry_point.return_value
    assert env.unwrapped == entry_point.return_value
    assert import_module.call_args_list == [call("innermod"), call("outermod")]
    assert wrap.call_args_list == [
        call(env=entry_point.return_value),
        call(env=wrap.return_values[0], kwarg=1),
    ]


def test_bad_extra_wrapper(entry_point: Mock, monkeypatch: pytest.MonkeyPatch) -> None:
    spec = EnvSpec(
        "ns/name-v1",
        entry_point=entry_point,
        order_enforce=False,
        disable_env_checker=True,
        additional_wrappers=(
            WrapperSpec("BadWrapper", "innermod:wrapper_entry_point", None),
        ),
    )
    # Patch `import_module()` for safety, we won't actually reach it.
    import_module = Mock(name="importlib.import_module", side_effect=RuntimeError)
    monkeypatch.setattr("importlib.import_module", import_module)
    # When:
    with pytest.raises(errors.WrapperClassError, match="BadWrapper"):
        spec.make()
    # Then:
    import_module.assert_not_called()


@pytest.mark.parametrize(
    ("additional_wrappers", "exc_type"),
    [
        ((WrapperSpec("Wrapper", "gymnasium.core:Wrapper", None),), None),
        ((WrapperSpec("BadWrapper", "", None),), errors.WrapperMismatchError),
        ((), errors.WrapperUnexpectedError),
    ],
)
def test_prior_wrappers(
    additional_wrappers: tuple[WrapperSpec, ...],
    exc_type: type[Exception] | None,
    entry_point: Mock,
) -> None:
    wrapped_entry_point = Mock(
        name="wrap",
        metadata=None,
        side_effect=lambda render_mode: gym.Wrapper(entry_point(render_mode)),
    )
    spec = EnvSpec(
        "ns/name-v1",
        entry_point=wrapped_entry_point,
        order_enforce=False,
        disable_env_checker=True,
        additional_wrappers=additional_wrappers,
    )
    if exc_type is None:
        env = spec.make()
        assert type(env) is gym.Wrapper
        assert env.env == entry_point.return_value
    else:
        with pytest.raises(exc_type):
            spec.make()
