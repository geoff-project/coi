# SPDX-FileCopyrightText: 2016 OpenAI
# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2022 - 2025 Farama Foundation
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Definition of the `EnvSpec` class."""

from __future__ import annotations

import dataclasses as dc
import json
import sys
import typing as t
from abc import ABCMeta

from . import _base

if t.TYPE_CHECKING:
    from typing_extensions import Self

    from .. import protocols

__all__ = (
    "EnvSpec",
    "MinimalEnvSpec",
    "bump_stacklevel",
    "downcast_spec",
)


def bump_stacklevel(kwargs: dict[str, t.Any]) -> int:
    """Bump a dynamic argument *stacklevel* and ensure it's 2 or higher.

    This also returns the *stacklevel*. The purpose of this function is
    to ensure that all warnings point at code outside of the COI, no
    matter which function was called by the user.

    .. note::
        The stacklevel stored in *kwargs* is one higher than the one
        returned. The idea is that the return value is used within the
        caller of `bump_stacklevel()`, whereas the kwargs are passed on
        to nested functions.
    """
    level = kwargs.get("stacklevel", 2)
    kwargs["stacklevel"] = level + 1
    return level


if sys.version_info < (3, 10):
    decorator = dc.dataclass(frozen=True)
else:  # pragma: no cover
    decorator = dc.dataclass(frozen=True, match_args=False)


@decorator
class MinimalEnvSpec(t.Protocol):
    """Protocol that `EnvSpec` objects have to follow."""

    id: str
    entry_point: _base.EnvCreator | str | None
    vector_entry_point: _base.VectorEnvCreator | str | None
    additional_wrappers: tuple[_base.WrapperSpec, ...]
    kwargs: dict[str, t.Any]
    namespace: str | None
    name: str
    version: int | None

    def to_json(self) -> str:
        """Converts the environment spec into a json compatible string."""

    def pprint(
        self,
        disable_print: bool = False,
        include_entry_points: bool = False,
        print_all: bool = False,
    ) -> str | None:
        """Pretty prints the environment spec."""


@dc.dataclass
class EnvSpec(metaclass=ABCMeta):
    """Reimplementation of `gymnasium.envs.registration.EnvSpec`.

    This dataclass is largely identical to Gymnasium's version with
    exception of the following differences:

    - its `make()` implementation uses `.coi.make()` rather than
      :func:`gym:gymnasium.make()`;
    - it is an :term:`abstract base class` and has registered
      `gymnasium.envs.registration.EnvSpec` as a subclass.

    If you need a Gymnasium EnvSpec for typing purposes, you can convert
    this class via `downcast_spec()`.
    """

    id: str
    entry_point: _base.EnvCreator | str | None = None

    # Environment attributes
    reward_threshold: float | None = None
    nondeterministic: bool = False

    # Wrappers
    max_episode_steps: int | None = None
    order_enforce: bool = True
    autoreset: bool = False
    disable_env_checker: bool = False
    apply_api_compatibility: bool = False

    # Environment arguments
    kwargs: dict[str, t.Any] = dc.field(default_factory=dict)

    # post-init attributes
    namespace: str | None = dc.field(init=False)
    name: str = dc.field(init=False)
    version: int | None = dc.field(init=False)

    # applied wrappers
    additional_wrappers: tuple[_base.WrapperSpec, ...] = dc.field(default_factory=tuple)

    # Vectorized environment entry point
    vector_entry_point: _base.VectorEnvCreator | str | None = None

    def __post_init__(self) -> None:
        self.namespace, self.name, self.version = _base.parse_env_id(self.id)

    def make(self, **kwargs: t.Any) -> protocols.Problem:
        """Call `.coi.make()` using this spec."""
        # Delayed import to avoid a cyclic dependency between modules.
        from ._make import make

        bump_stacklevel(kwargs)
        return make(self, **kwargs)

    def to_json(self) -> str:
        """Convert this spec into a JSON-compatible string."""
        env_spec_dict = dc.asdict(self)
        # Remove post-init attributes.
        env_spec_dict.pop("namespace")
        env_spec_dict.pop("name")
        env_spec_dict.pop("version")
        self._check_can_jsonify(env_spec_dict)
        return json.dumps(env_spec_dict)

    @staticmethod
    def _check_can_jsonify(env_spec: dict[str, t.Any]) -> None:
        """Raise an exception if the spec contains a callable."""
        for key, value in env_spec.items():
            if callable(value):
                spec_name = env_spec.get("name") or env_spec["id"]
                raise ValueError(  # noqa: TRY004
                    f"Gymnasium does not support serialization of "
                    f"callables: {spec_name} attribute {key!r}"
                )

    @classmethod
    def from_json(cls, json_env_spec: str) -> Self:
        """Convert a JSON string back into a specification stack."""
        env_spec_dict = json.loads(json_env_spec)

        applied_wrapper_specs: list[_base.WrapperSpec] = []
        additional_wrappers = env_spec_dict.pop("additional_wrappers", [])
        try:
            for wrapper_spec_dict in additional_wrappers:
                wrapper_spec = _base.WrapperSpec(**wrapper_spec_dict)
                applied_wrapper_specs.append(wrapper_spec)
        except Exception as exc:
            raise ValueError(
                f"could not create WrapperSpec from JSON: {wrapper_spec_dict}"
            ) from exc

        try:
            env_spec = cls(**env_spec_dict)
            env_spec.additional_wrappers = tuple(applied_wrapper_specs)
        except Exception as exc:
            raise ValueError(
                f"could not create EnvSpec from JSON: {env_spec_dict}"
            ) from exc

        return env_spec

    pprint = _base.EnvSpec.pprint


EnvSpec.register(_base.EnvSpec)
del decorator


def downcast_spec(spec: EnvSpec) -> _base.EnvSpec:
    """Turn a COI EnvSpec into a Gym EnvSpec."""
    if isinstance(spec, _base.EnvSpec):
        return spec
    env_spec_dict = dc.asdict(spec)
    # Remove post-init attributes, copied from `to_json()`.
    env_spec_dict.pop("namespace")
    env_spec_dict.pop("name")
    env_spec_dict.pop("version")
    return _base.EnvSpec(**env_spec_dict)
