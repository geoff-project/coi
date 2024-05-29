#!/usr/bin/env python

# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""An example of how to use the `Configurable` interface."""

from __future__ import annotations

import sys
import typing as t

import gymnasium as gym
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from numpy.typing import NDArray
from PyQt5 import QtCore, QtGui, QtWidgets
from typing_extensions import override

from cernml import coi
from cernml.coi import cancellation


class ConfParabola(
    coi.OptEnv[NDArray[np.double], NDArray[np.double], NDArray[np.double]],
    coi.Configurable,
):
    """Example implementation of `OptEnv`.

    The goal of this environment is to find the center of a parabola.
    """

    # pylint: disable = too-many-instance-attributes

    # Domain declarations.
    metadata = {
        # All `mode` arguments to `self.render()` that we support.
        "render_modes": ["ansi", "human", "matplotlib_figures"],
        # The example is independent of all CERN accelerators.
        "cern.machine": coi.Machine.NO_MACHINE,
        # No need for communication with CERN accelerators.
        "cern.japc": False,
        # We implement cancellation for demonstration purposes.
        "cern.cancellable": True,
    }

    # The radius at which an episode is ended. We employ "reward
    # dangling", i.e. we start with a very wide radius and restrict it
    # with each successful episode, up to a certain limit. This improves
    # training speed, as the agent gathers more positive feedback early
    # in the training.
    objective = -0.05
    max_objective = -0.003
    action_space: gym.spaces.Box
    observation_space: gym.spaces.Box
    optimization_space: gym.spaces.Box

    def __init__(
        self,
        cancellation_token: cancellation.Token,
        *,
        norm: int = 2,
        dangling: bool = True,
        box_width: float = 2.0,
        dim: int = 5,
        render_mode: str | None = None,
    ):
        self.render_mode = render_mode
        self.token = cancellation_token
        self.norm = norm
        self.dangling = dangling
        self.action_space = gym.spaces.Box(-1.0, 1.0, shape=(dim,))
        self.observation_space = gym.spaces.Box(-box_width, box_width, shape=(dim,))
        self.optimization_space = gym.spaces.Box(-box_width, box_width, shape=(dim,))
        self.pos = np.zeros((dim,))
        max_distance = float(
            np.linalg.norm(self.optimization_space.high, ord=self.norm)
        )
        self.reward_range = (-max_distance, 0.0)
        self.objective_range = (0.0, max_distance)
        self.figure: Figure | None = None

    @override
    def get_config(self) -> coi.Config:
        (dim,) = self.pos.shape
        box_width = self.optimization_space.high[0]
        config = coi.Config()
        config.add("norm", self.norm, type=int, choices=(1, 2))
        config.add("dimensions", dim, type=int, range=(1, 10))
        config.add("enable_dangling", self.dangling, type=bool)
        config.add("box_width", box_width, type=float, range=(0.0, float("inf")))
        return config

    @override
    def apply_config(self, values: coi.ConfigValues) -> None:
        self.norm = values.norm
        self.dangling = values.enable_dangling
        box_width = values.box_width
        dim = values.dimensions
        self.observation_space = gym.spaces.Box(-box_width, box_width, shape=(dim,))
        self.action_space = gym.spaces.Box(-1.0, 1.0, shape=(dim,))
        self.optimization_space = gym.spaces.Box(-box_width, box_width, shape=(dim,))
        self.pos = np.zeros((dim,))
        max_distance = float(
            np.linalg.norm(self.optimization_space.high, ord=self.norm)
        )
        self.reward_range = (-max_distance, 0.0)
        self.objective_range = (0.0, max_distance)

    @override
    def reset(
        self, *, seed: int | None = None, options: coi.InfoDict | None = None
    ) -> tuple[NDArray[np.double], coi.InfoDict]:
        super().reset(seed=seed)
        # This is not good usage. In practice, you should only accept
        # and use cancellation tokens if your environment contains a
        # loop that waits for data. This is only for demonstration
        # purposes.
        self.token.raise_if_cancellation_requested()
        self.pos = self.optimization_space.sample()
        return self.pos.copy(), {}

    @override
    def step(
        self, action: NDArray[np.double]
    ) -> tuple[NDArray[np.double], float, bool, bool, coi.InfoDict]:
        old_pos = self.pos
        next_pos = self.pos + action
        self.pos = np.clip(
            next_pos,
            self.observation_space.low,
            self.observation_space.high,
        )
        try:
            # Because cancellation is cooperative, we know this is the
            # only place where we can get cancelled.
            reward = -self._fetch_distance_slow()
        except cancellation.CancelledError:
            self.pos = old_pos
            self.token.complete_cancellation()
            raise
        terminated = reward > self.objective
        truncated = next_pos not in self.observation_space
        info = {"objective": self.objective}
        if self.dangling and terminated and self.objective < self.max_objective:
            self.objective *= 0.95
        if self.render_mode == "human":
            self.render()
        return self.pos.copy(), reward, terminated, truncated, info

    @override
    def get_initial_params(
        self, *, seed: int | None = None, options: coi.InfoDict | None = None
    ) -> NDArray[np.double]:
        pos, _ = self.reset(seed=seed, options=options)
        return pos

    @override
    def compute_single_objective(self, params: NDArray[np.double]) -> float:
        old_pos = self.pos
        self.pos = np.clip(
            params,
            self.observation_space.low,
            self.observation_space.high,
        )
        try:
            # Because cancellation is cooperative, we know this is the
            # only place where we can get cancelled.
            return self._fetch_distance_slow()
        except cancellation.CancelledError:
            self.pos = old_pos
            self.token.complete_cancellation()
            raise

    @override
    def render(self) -> t.Any:
        if self.render_mode == "human":
            _, axes = plt.subplots()
            self._update_axes(axes)
            plt.show()
            return None
        if self.render_mode == "matplotlib_figures":
            if self.figure is None:
                self.figure = Figure()
                axes = self.figure.subplots()
            else:
                [axes] = self.figure.axes
            self._update_axes(axes)
            return [self.figure]
        if self.render_mode == "ansi":
            return str(self.pos)
        return super().render()

    def _update_axes(self, axes: Axes) -> None:
        """Plot this environment onto the given axes.

        This method allows us to implement plotting once for both the
        "human" and the "matplotlib_figures" render mode.
        """
        axes.cla()
        axes.plot(self.pos, "o")
        axes.plot(self.observation_space.low, "k--")
        axes.plot(self.observation_space.high, "k--")
        axes.plot(0.0 * self.observation_space.high, "k--")
        axes.set_xlabel("Axes")
        axes.set_ylabel("Position")

    def _fetch_distance_slow(self, pos: np.ndarray | None = None) -> float:
        """Get distance from the goal in a slow manner.

        This simulates interaction with the machine. We sleep for a
        while, then return the distance between the current position and
        the coordinate-space origin.

        Raises:
            cernml.cancellation.CancelledError: if a cancellation
                arrives while this method sleeps.
        """
        handle = self.token.wait_handle
        with handle:
            if handle.wait_for(lambda: self.token.cancellation_requested, timeout=0.3):
                raise cancellation.CancelledError
        return float(
            np.linalg.norm(pos if pos is not None else self.pos, ord=self.norm)
        )


coi.register("ConfParabola-v0", entry_point=ConfParabola, max_episode_steps=10)


class OptimizerThread(QtCore.QThread):
    """Qt Thread that runs a COBYLA optimization.

    Args:
        env: An optimizable problem.
    """

    step = QtCore.pyqtSignal()

    def __init__(self, env: coi.SingleOptimizable) -> None:
        super().__init__()
        self.env = env
        opt_space = env.optimization_space
        assert isinstance(opt_space, gym.spaces.Box), opt_space
        self.optimization_space = opt_space

    def run(self) -> None:
        """Thread main function."""

        def constraint(params: NDArray[np.double]) -> t.SupportsFloat:
            space = self.optimization_space
            width = space.high - space.low
            return np.linalg.norm(2 * params / width, ord=np.inf)

        def func(params: NDArray[np.double]) -> t.SupportsFloat:
            loss = self.env.compute_single_objective(params)
            self.step.emit()
            return loss

        try:
            res: scipy.optimize.OptimizeResult = scipy.optimize.minimize(
                func,
                x0=self.env.get_initial_params(),
                method="COBYLA",
                constraints=[scipy.optimize.NonlinearConstraint(constraint, 0.0, 1.0)],
                tol=0.01,
            )
            if res.success:
                func(res.x)
        except cancellation.CancelledError:
            print("Operation cancelled by user")


class ConfigureDialog(QtWidgets.QDialog):
    """Qt dialog that allows configuring an environment.

    Args:
        target: The environment to be configured.
        parent: The parent widget to attach to.
    """

    def __init__(
        self, target: coi.Configurable, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)
        spec = getattr(target, "spec", None)
        name = getattr(spec, "id", type(target).__name__)
        self.setWindowTitle(f"Configure {name} ...")
        self.target = target
        self.config = self.target.get_config()
        self.current_values = {
            field.dest: field.value for field in self.config.fields()
        }
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        params = QtWidgets.QWidget()
        main_layout.addWidget(params)
        params_layout = QtWidgets.QFormLayout()
        params.setLayout(params_layout)
        for field in self.config.fields():
            label = QtWidgets.QLabel(field.label)
            widget = self._make_field_widget(field)
            params_layout.addRow(label, widget)
        controls = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok
            | QtWidgets.QDialogButtonBox.Apply
            | QtWidgets.QDialogButtonBox.Cancel
        )
        controls.button(controls.Ok).clicked.connect(self.on_ok_clicked)
        controls.button(controls.Apply).clicked.connect(self.on_apply_clicked)
        controls.button(controls.Cancel).clicked.connect(self.on_cancel_clicked)
        main_layout.addWidget(controls)

    def on_ok_clicked(self) -> None:
        """Apply the configs and close the window."""
        values = self.config.validate_all(self.current_values)
        print(values)
        self.target.apply_config(values)
        self.accept()

    def on_apply_clicked(self) -> None:
        """Apply the configs."""
        values = self.config.validate_all(self.current_values)
        print(values)
        self.target.apply_config(values)

    def on_cancel_clicked(self) -> None:
        """Discard any changes and close the window."""
        self.reject()

    def _make_field_widget(self, field: coi.Config.Field) -> QtWidgets.QWidget:
        """Given a field, pick the best widget to configure it."""
        # pylint: disable = too-many-return-statements
        if field.choices is not None:
            combo_box = QtWidgets.QComboBox()
            combo_box.addItems(str(choice) for choice in field.choices)
            combo_box.setCurrentText(str(field.value))
            combo_box.currentTextChanged.connect(
                lambda val: self.set_current_value(field.dest, val)
            )
            return combo_box
        if field.range is not None:
            low, high = field.range
            spin_box: QtWidgets.QSpinBox | QtWidgets.QDoubleSpinBox
            if isinstance(field.value, (int, np.integer)):
                spin_box = QtWidgets.QSpinBox()
                spin_box.setValue(int(field.value))
            elif isinstance(field.value, (float, np.floating)):
                spin_box = QtWidgets.QDoubleSpinBox()
                spin_box.setValue(float(field.value))
            else:
                raise KeyError(type(field.value))
            spin_box.setRange(low, high)
            spin_box.valueChanged.connect(
                lambda val: self.set_current_value(field.dest, str(val))
            )
            return spin_box
        if isinstance(field.value, (bool, np.bool_)):
            check_box = QtWidgets.QCheckBox()
            check_box.setChecked(bool(field.value))
            # Do not use `str(checked)`! `False` converts to `"False"`,
            # which would convert back to `True` via `bool(string)`.
            check_box.stateChanged.connect(
                lambda checked: self.set_current_value(
                    field.dest, "checked" if checked else ""
                )
            )
            return check_box
        if isinstance(field.value, (int, np.integer)):
            line_edit = QtWidgets.QLineEdit(str(field.value))
            line_edit.setValidator(QtGui.QIntValidator())
            line_edit.editingFinished.connect(
                lambda: self.set_current_value(field.dest, line_edit.text())
            )
            return line_edit
        if isinstance(field.value, (float, np.floating)):
            line_edit = QtWidgets.QLineEdit(str(field.value))
            line_edit.setValidator(QtGui.QDoubleValidator())
            line_edit.editingFinished.connect(
                lambda: self.set_current_value(field.dest, line_edit.text())
            )
            return line_edit
        if isinstance(field.value, str):
            line_edit = QtWidgets.QLineEdit(str(field.value))
            line_edit.editingFinished.connect(
                lambda: self.set_current_value(field.dest, line_edit.text())
            )
            return line_edit
        return QtWidgets.QLabel(str(field.value))

    def set_current_value(self, name: str, value: str) -> None:
        """Update the saved values.

        This is called by each config widget when it changes its value.
        """
        self.current_values[name] = value


class MainWindow(QtWidgets.QMainWindow):
    """Main window of the Qt application."""

    def __init__(self) -> None:
        super().__init__()

        self.cancellation_token_source = cancellation.TokenSource()
        env = coi.make(
            "ConfParabola-v0",
            cancellation_token=self.cancellation_token_source.token,
            render_mode="matplotlib_figures",
        )
        self.env = t.cast(ConfParabola, env)
        self.worker = OptimizerThread(self.env)
        self.worker.step.connect(self.on_opt_step)
        self.worker.finished.connect(self.on_opt_finished)
        self.env.reset()

        [figure] = self.env.render()
        self.canvas = FigureCanvas(figure)
        self.launch = QtWidgets.QPushButton("Launch")
        self.launch.clicked.connect(self.on_launch)
        self.cancel = QtWidgets.QPushButton("Cancel")
        self.cancel.clicked.connect(self.on_cancel)
        self.cancel.setEnabled(False)
        self.configure_env = QtWidgets.QPushButton("Configure…")
        self.configure_env.clicked.connect(self.on_configure)

        window = QtWidgets.QWidget()
        self.setCentralWidget(window)
        main_layout = QtWidgets.QVBoxLayout(window)
        buttons_layout = QtWidgets.QHBoxLayout()
        main_layout.addWidget(self.canvas)
        main_layout.addLayout(buttons_layout)
        buttons_layout.addWidget(self.launch)
        buttons_layout.addWidget(self.cancel)
        buttons_layout.addWidget(self.configure_env)
        self.addToolBar(NavigationToolbar(self.canvas, parent=self))

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        # pylint: disable = invalid-name, missing-function-docstring
        self.launch.setEnabled(False)
        self.cancel.setEnabled(False)
        self.configure_env.setEnabled(False)
        self.cancellation_token_source.cancel()
        self.worker.wait()
        event.accept()

    def on_configure(self) -> None:
        """Open the dialog to configure the environment."""
        assert coi.is_configurable(self.env)
        dialog = ConfigureDialog(self.env, parent=self)
        dialog.open()

    def on_launch(self) -> None:
        """Disable the GUI and start optimization."""
        self.launch.setEnabled(False)
        self.cancel.setEnabled(True)
        self.configure_env.setEnabled(False)
        self.worker.start()

    def on_cancel(self) -> None:
        """Send a cancellation request."""
        self.cancellation_token_source.cancel()
        # Disable the button. `on_opt_finished()` will eventually
        # re-enable the other buttons.
        self.cancel.setEnabled(False)

    def on_opt_step(self) -> None:
        """Update the plots."""
        self.env.render()
        self.canvas.draw()

    def on_opt_finished(self) -> None:
        """Re-enable the GUI."""
        # Reset the cancellation, if it is possible. Only re-enable the
        # launch button if we could reset the cancellation (or no
        # cancellation ever occurred.)
        if self.cancellation_token_source.can_reset_cancellation:
            self.cancellation_token_source.reset_cancellation()
        if not self.cancellation_token_source.cancellation_requested:
            self.launch.setEnabled(True)
        self.cancel.setEnabled(False)
        self.configure_env.setEnabled(True)


def main(argv: list[str]) -> int:
    """Main function. You should pass in `sys.argv`."""
    app = QtWidgets.QApplication(argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
