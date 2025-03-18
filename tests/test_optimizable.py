# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test SingleOptimizable, FunctionOptimizable and their ABCs."""

import typing as t

import numpy as np
import pytest
from gymnasium.spaces import Box

from cernml import coi


class TestSingleOptProtocol:
    def test_protocol_attrs(self) -> None:
        assert getattr(coi.protocols.SingleOptimizable, "__protocol_attrs__", None) == {
            "close",
            "compute_single_objective",
            "constraint_names",
            "constraints",
            "get_initial_params",
            "get_wrapper_attr",
            "metadata",
            "objective_name",
            "optimization_space",
            "param_names",
            "render",
            "render_mode",
            "spec",
            "unwrapped",
        }

    def test_non_callable_proto_members(self) -> None:
        assert getattr(
            coi.protocols.SingleOptimizable, "__non_callable_proto_members__", None
        ) == {
            "constraint_names",
            "constraints",
            "metadata",
            "objective_name",
            "optimization_space",
            "param_names",
            "render_mode",
            "spec",
            "unwrapped",
        }

    def test_proto_classmethods__(self) -> None:
        assert (
            getattr(coi.protocols.SingleOptimizable, "__proto_classmethods__", None)
            == set()
        )


class TestFunctionOptProtocol:
    def test_protocol_attrs(self) -> None:
        assert getattr(
            coi.protocols.FunctionOptimizable, "__protocol_attrs__", None
        ) == {
            "close",
            "compute_function_objective",
            "constraints",
            "get_initial_params",
            "get_objective_function_name",
            "get_optimization_space",
            "get_param_function_names",
            "get_wrapper_attr",
            "metadata",
            "override_skeleton_points",
            "render",
            "render_mode",
            "spec",
            "unwrapped",
        }

    def test_non_callable_proto_members(self) -> None:
        assert getattr(
            coi.protocols.FunctionOptimizable, "__non_callable_proto_members__", None
        ) == {
            "constraints",
            "metadata",
            "render_mode",
            "spec",
            "unwrapped",
        }

    def test_proto_classmethods__(self) -> None:
        assert (
            getattr(coi.protocols.FunctionOptimizable, "__proto_classmethods__", None)
            == set()
        )


@pytest.mark.parametrize(
    "cls", [coi.protocols.SingleOptimizable, coi.SingleOptimizable]
)
def test_single_optimizable_defaults(
    cls: type[coi.protocols.SingleOptimizable],
) -> None:
    assert cls.metadata["render_modes"] == []
    assert cls.render_mode is None
    assert getattr(cls, "optimization_space", None) is None
    assert len(cls.constraints) == 0
    assert cls.objective_name == ""
    assert len(cls.param_names) == 0
    assert len(cls.constraint_names) == 0


@pytest.mark.parametrize(
    "cls", [coi.protocols.FunctionOptimizable, coi.FunctionOptimizable]
)
def test_function_optimizable_defaults(
    cls: type[coi.protocols.FunctionOptimizable],
) -> None:
    class Subclass(cls):  # type: ignore[misc,valid-type]
        def get_optimization_space(self, cycle_time: float) -> Box:
            return Box(-1, 1, ())

        def get_initial_params(self, cycle_time: float) -> np.ndarray:
            return cycle_time + np.zeros(())

        def compute_function_objective(
            self, cycle_time: float, params: np.ndarray
        ) -> float:
            return np.sum(params) + cycle_time

    problem = Subclass()
    assert problem.metadata["render_modes"] == []
    assert len(problem.constraints) == 0
    assert problem.get_objective_function_name() == ""
    assert problem.get_param_function_names() == ()
    assert problem.override_skeleton_points() is None


@pytest.mark.parametrize("cls", [coi.SingleOptimizable, coi.FunctionOptimizable])
def test_optimizable_sets_render_mode(cls: type[coi.AnyOptimizable]) -> None:
    class Subclass(cls):  # type: ignore[misc,valid-type]
        metadata = {"render_modes": ["rgb_array"]}

        def get_initial_params(
            self, cycle_time: t.Union[float, None] = None
        ) -> np.ndarray:
            return np.zeros(2)

        def get_optimization_space(self, cycle_time: float) -> Box:
            return Box(-2, 2, shape=(2,))

        def compute_single_objective(self, params: np.ndarray) -> float:
            return 0.0

        def compute_function_objective(
            self, params: np.ndarray, cycle_time: float
        ) -> float:
            return 0.0

    assert Subclass(render_mode="rgb_array").render_mode == "rgb_array"
