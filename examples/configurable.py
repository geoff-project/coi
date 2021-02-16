#!/usr/bin/env python
"""An example implementation of the `OptEnv` interface."""

import sys
import typing as t
from types import SimpleNamespace

import gym
import numpy as np
import scipy.optimize
from matplotlib import pyplot
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cernml import coi


class ConfParabola(coi.OptEnv, coi.Configurable):
    """Example implementation of `OptEnv`.

    The goal of this environment is to find the center of a parabola.
    """

    # pylint: disable = too-many-instance-attributes

    # Domain declarations.
    metadata = {
        "render.modes": ["ansi", "human", "matplotlib_figures"],
        "cern.machine": coi.Machine.NoMachine,
    }

    # The radius at which an episode is ended. We employ "reward dangling",
    # i.e. we start with a very wide radius and restrict it with each
    # successful episode, up to a certain limit. This improves training speed,
    # as the agent gathers more positive feedback early in the training.
    objective = -0.05
    max_objective = -0.003

    def __init__(
        self,
        norm: int = 2,
        dangling: bool = True,
        box_width: float = 2.0,
        dim: int = 5,
    ):
        self.norm = norm
        self.dangling = dangling
        self.action_space = gym.spaces.Box(-1.0, 1.0, shape=(dim,))
        self.observation_space = gym.spaces.Box(-box_width, box_width, shape=(dim,))
        self.optimization_space = gym.spaces.Box(-box_width, box_width, shape=(dim,))
        self.pos = np.zeros((dim,))
        max_distance = self._distance(self.optimization_space.high)
        self.reward_range = (-max_distance, 0.0)
        self.objective_range = (0.0, max_distance)
        self.figure: t.Optional[Figure] = None

    def get_config(self) -> coi.Config:
        (dim,) = self.pos.shape
        box_width = self.optimization_space.high[0]
        config = coi.Config()
        config.add("norm", self.norm, type=int, choices=(1, 2))
        config.add("seed", 0, type=int)
        config.add("dimensions", dim, type=int, range=(1, 10))
        config.add("enable_dangling", self.dangling, type=bool)
        config.add("box_width", box_width, type=float, range=(0.0, float("inf")))
        return config

    def apply_config(self, values: SimpleNamespace) -> None:
        self.norm = values.norm
        self.seed(values.seed)
        self.dangling = values.enable_dangling
        box_width = values.box_width
        dim = values.dimensions
        self.observation_space = gym.spaces.Box(-box_width, box_width, shape=(dim,))
        self.action_space = gym.spaces.Box(-1.0, 1.0, shape=(dim,))
        self.optimization_space = gym.spaces.Box(-box_width, box_width, shape=(dim,))
        self.pos = np.zeros((dim,))
        max_distance = self._distance(self.optimization_space.high)
        self.reward_range = (-max_distance, 0.0)
        self.objective_range = (0.0, max_distance)

    def reset(self) -> np.ndarray:
        self.pos = self.optimization_space.sample()
        return self.pos.copy()

    def step(self, action: np.ndarray) -> t.Tuple[np.ndarray, float, bool, t.Dict]:
        next_pos = self.pos + action
        self.pos = np.clip(
            next_pos,
            self.observation_space.low,
            self.observation_space.high,
        )
        reward = -self._distance()
        success = reward > self.objective
        done = success or next_pos not in self.observation_space
        info = dict(success=success, objective=self.objective)
        if self.dangling and success and self.objective < self.max_objective:
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
        return self._distance()

    def render(self, mode: str = "human") -> t.Any:
        if mode == "human":
            _, axes = pyplot.subplots()
            self._update_axes(axes)
            pyplot.show()
            return None
        if mode == "matplotlib_figures":
            if self.figure is None:
                self.figure = Figure()
                axes = self.figure.subplots()
            else:
                [axes] = self.figure.axes
            self._update_axes(axes)
            return [self.figure]
        if mode == "ansi":
            return str(self.pos)
        return super().render(mode)

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

    def seed(self, seed: t.Optional[int] = None) -> t.List[int]:
        return [
            *self.observation_space.seed(seed),
            *self.action_space.seed(seed),
            *self.optimization_space.seed(seed),
        ]

    def _distance(self, pos: t.Optional[np.ndarray] = None) -> float:
        return np.linalg.norm(pos if pos is not None else self.pos, ord=self.norm)


coi.register("ConfParabola-v0", entry_point=ConfParabola, max_episode_steps=10)


class OptimizerThread(QThread):
    """Qt Thread that runs a COBYLA optimization.

    Args:
        env: An optimizable problem.
    """

    step = pyqtSignal()

    def __init__(self, env: coi.SingleOptimizable) -> None:
        super().__init__()
        self.env = env

    def run(self) -> None:
        """Thread main function."""

        def constraint(params: np.ndarray) -> float:
            space = self.env.optimization_space
            width = space.high - space.low
            return np.linalg.norm(2 * params / width, ord=np.inf)

        def func(params: np.ndarray) -> float:
            loss = self.env.compute_single_objective(params)
            QThread.msleep(100)  # Simulate machine latency.
            self.step.emit()
            return loss

        res: scipy.optimize.OptimizeResult = scipy.optimize.minimize(
            func,
            x0=self.env.get_initial_params(),
            method="COBYLA",
            constraints=[scipy.optimize.NonlinearConstraint(constraint, 0.0, 1.0)],
        )
        if res.success:
            func(res.x)


class ConfigureDialog(QDialog):
    """Qt dialog that allows configuring an environment.

    Args:
        target: The environment to be configured.
        parent: The parent widget to attach to.
    """

    def __init__(
        self, target: coi.Configurable, parent: t.Optional[QWidget] = None
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
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        params = QWidget()
        main_layout.addWidget(params)
        params_layout = QFormLayout()
        params.setLayout(params_layout)
        for field in self.config.fields():
            label = QLabel(field.label)
            widget = self._make_field_widget(field)
            params_layout.addRow(label, widget)
        controls = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Apply | QDialogButtonBox.Cancel
        )
        controls.button(QDialogButtonBox.Ok).clicked.connect(self.on_ok_clicked)
        controls.button(QDialogButtonBox.Apply).clicked.connect(self.on_apply_clicked)
        controls.button(QDialogButtonBox.Cancel).clicked.connect(self.on_cancel_clicked)
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

    def _make_field_widget(self, field: coi.Config.Field) -> QWidget:
        """Given a field, pick the best widget to configure it."""
        # pylint: disable = too-many-return-statements
        if field.choices is not None:
            widget = QComboBox()
            widget.addItems(str(choice) for choice in field.choices)
            widget.setCurrentText(str(field.value))
            widget.currentTextChanged.connect(self._make_setter(field))
            return widget
        if field.range is not None:
            low, high = field.range
            if isinstance(field.value, (int, np.integer)):
                widget = QSpinBox()
            elif isinstance(field.value, (float, np.floating)):
                widget = QDoubleSpinBox()
            else:
                raise KeyError(type(field.value))
            widget.setValue(field.value)
            widget.setRange(low, high)
            widget.valueChanged.connect(self._make_setter(field))
            return widget
        if isinstance(field.value, (bool, np.bool_)):
            widget = QCheckBox()
            widget.setChecked(field.value)
            widget.stateChanged.connect(self._make_setter(field))
            return widget
        if isinstance(field.value, (int, np.integer)):
            widget = QLineEdit(str(field.value))
            widget.setValidator(QIntValidator())
            widget.editingFinished.connect(self._make_setter(field, get=widget.text))
            return widget
        if isinstance(field.value, (float, np.floating)):
            widget = QLineEdit(str(field.value))
            widget.setValidator(QDoubleValidator())
            widget.editingFinished.connect(self._make_setter(field, get=widget.text))
            return widget
        if isinstance(field.value, str):
            widget = QLineEdit(str(field.value))
            widget.editingFinished.connect(self._make_setter(field, get=widget.text))
            return widget
        return QLabel(str(field.value))

    def _make_setter(
        self,
        field: coi.Config.Field,
        get: t.Optional[t.Callable[[], str]] = None,
    ) -> QWidget:
        """Return a callback that can be used to update a field's value."""

        def _setter(value: t.Any = None) -> None:
            if get is not None:
                value = get()
            if isinstance(field.value, (bool, np.bool_)):
                value = "checked" if value else ""
            else:
                value = str(value)
            self.current_values[field.dest] = value

        return _setter


class MainWindow(QMainWindow):
    """Main window of the Qt application."""

    def __init__(self) -> None:
        super().__init__()

        self.env = coi.make("ConfParabola-v0")
        self.worker = OptimizerThread(self.env)
        self.worker.step.connect(self.on_opt_step)
        self.worker.finished.connect(self.on_opt_finished)
        self.env.reset()

        [figure] = self.env.render(mode="matplotlib_figures")
        self.canvas = FigureCanvas(figure)
        self.launch = QPushButton("Launch")
        self.launch.clicked.connect(self.on_launch)
        self.configure_env = QPushButton("Configure…")
        self.configure_env.clicked.connect(self.on_configure)

        window = QWidget()
        self.setCentralWidget(window)
        main_layout = QVBoxLayout(window)
        buttons_layout = QHBoxLayout()
        main_layout.addWidget(self.canvas)
        main_layout.addLayout(buttons_layout)
        buttons_layout.addWidget(self.launch)
        buttons_layout.addWidget(self.configure_env)
        self.addToolBar(NavigationToolbar(self.canvas, parent=self))

    def on_configure(self) -> None:
        """Open the dialog to configure the environment."""
        dialog = ConfigureDialog(self.env, parent=self)
        dialog.open()

    def on_launch(self) -> None:
        """Disable the GUI and start optimization."""
        self.launch.setEnabled(False)
        self.configure_env.setEnabled(False)
        self.worker.start()

    def on_opt_step(self) -> None:
        """Update the plots."""
        self.env.render("matplotlib_figures")
        self.canvas.draw()

    def on_opt_finished(self) -> None:
        """Re-enable the GUI."""
        self.launch.setEnabled(True)
        self.configure_env.setEnabled(True)


def main(argv: t.List[str]) -> int:
    """Main function. You should pass in `sys.argv`."""
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    main(sys.argv)
