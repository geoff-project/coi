# Changelog

## v0.7.2

- ADD: [`next_if_ready()`](api.html#cernml.coi.unstable.japc_utils.ParamStream.next_if_ready) no longer checks stream's the cancellation token.
- ADD: [`parameter_name`](api.html#cernml.coi.unstable.japc_utils.ParamStream.parameter_name) and [`parameter_names`](api.html#cernml.coi.unstable.japc_utils.ParamGroupStream.parameter_names).
- FIX: `repr()` of [`ParamGroupStream`](api.html#cernml.coi.unstable.japc_utils.ParamGroupStream) called wrong Java API.

## v0.7.1

- ADD: Enum member [`Machine.ISOLDE`](api.html#cernml.coi.Machine.ISOLDE).

## v0.7.0

- BREAKING: Remove [Cancellation tokens](guide.html#synchronization). The
  stable API did not accommodate all required use cases and could not be fixed
  in a backwards-compatible manner.
- ADD: Re-add [Cancellation tokens](guide.html#synchronization) as an unstable
  module. The new API supports cancellation completion and resets.

## v0.6.2

- ADD: Rename all variants of [`Machine`](api.html#cernml.coi.Machine) to `SCREAMING_SNAKE_CASE`. The `PascalCase` names remain available, but issue a deprecation warning.
- ADD: [Cancellation tokens](guide.html#cancellation).
- ADD: Cancellation support to [parameter streams](api.html#cernml.coi.unstable.japc_utils.subscribe_param).
- ADD: Property [`locked`](api.html#cernml.coi.unstable.japc_utils.ParamStream.locked) to parameter streams.
- ADD: Document [parameter streams](guide.html#synchronization).
- ADD: Document [checker plugins](api.html#cernml.coi.check).
- FIX: Add default values for all known [`metadata`](api.html#cernml.coi.Problem.metadata) keys.
- FIX: Missing `figure.show()` when calling [`SimpleRenderer.update("human")`](api.html#cernml.coi.unstable.renderer.SimpleRenderer.update).

## v0.6.1

- ADD: `title` parameter to [`SimpleRenderer.from_generator()`](api.html#cernml.coi.unstable.renderer.SimpleRenderer).
- FIX: Missing `figure.draw()` when calling [`SimpleRenderer.update("human")`](api.html#cernml.coi.unstable.renderer.SimpleRenderer.update).

## v0.6.0

- BREAKING: Instate [a variant of semantic versioning](https://gitlab.cern.ch/be-op-ml-optimization/cernml-coi#stability).
- BREAKING: Move the Matplotlib utilities into [`mpl_utils`](api.html#matplotlib-utilities).
- ADD: Unstable module [`renderer`](api.html#cernml.coi.unstable.renderer.Renderer).
- ADD: Unstable module [`japc_utils`](api.html#pyjapc-utilities).
- ADD: Allow a single `Figure` as return value of [`render("matplotlib_figure")`](api.html#cernml.coi.Problem.render).

## v0.5.0

- BREAKING: Add [`Problem.close()`](api.html#cernml.coi.Problem.close).

## v0.4.7

- FIX: Typo in [`metadata`](api.html#cernml.coi.Problem.metadata) key `"cern.machine"`.
- FIX: Mark [`metadata`](api.html#cernml.coi.Problem.metadata) as a class variable.
- FIX: Make base [`metadata`](api.html#cernml.coi.Problem.metadata) a mappingproxy to prevent accidental mutation.

## v0.4.6

- BREAKING: Remove keyword arguments from the signature of [`Problem.render()`](api.html#cernml.coi.Problem.render).
- ADD: Start distributing wheels.

## v0.4.5

- ADD: Plugin entry point and logging to [`check()`](api.html#cernml.coi.check).

## v0.4.4

- ADD: Export some (for now) undocumented helper functions from `cernml.coi.checkers`.

## v0.4.3

- BREAKING: Switch to setuptools-scm for versioning.
- ADD: Unmark [`Problem.render()`](api.html#cernml.coi.Problem.render) as an abstract method.

## v0.4.2

- ADD: Make dependency on Matplotlib optional.
- FIX: Add missing check for defined render modes to [`check()`](api.html#cernml.coi.check).

## v0.4.1

- FIX: Expose [`check()`](api.html#cernml.coi.check) argument `headless`.

## v0.4.0

- BREAKING: Mark the package as fully type-annotated.
- BREAKING: Switch to pyproject.toml and setup.cfg based building.
- BREAKING: Rewrite `check_env()` as [`check()`](api.html#cernml.coi.check).
- ADD: [`iter_matplotlib_figures`](api.html#cernml.coi.mpl_utils.iter_matplotlib_figures).

## v0.3.3

- FIX: Set window title in example `configurable.py`.

## v0.3.2

- ADD: `help` argument to [`Config.add()`](api.html#cernml.coi.Config.add).

## v0.3.1

- BREAKING: Make all submodules private.
- ADD: [`Configurable`](api.html#cernml.coi.Configurable) interface.

## v0.3.0

- BREAKING: Rename `Optimizable` to [`SingleOptimizable`](api.html#cernml.coi.SingleOptimizable).
- BREAKING: Add dependency on Numpy.
- ADD: [`Problem`](api.html#cernml.coi.Problem) interface.
- ADD: [Environment registry](api.html#problem-registry).
- FIX: Check inheritance of `env.unwrapped` in [`check_env()`](api.html#cernml.coi.check).

## v0.2.1

- FIX: Fix broken CI tests.

## v0.2.0

- BREAKING: Rename package from `cernml.abc` to `cernml.coi` (And the distribution from `cernml-abc` to `cernml-coi`).
- BREAKING: Rename `OptimizeMixin` to [`Optimizable`](api.html#cernml.coi.SingleOptimizable).
- BREAKING: Add [`metadata`](api.html#cernml.coi.Problem.metadata) key `"cern.machine"`.
- BREAKING: Add more restrictions to [`env_checker()`](api.html#cernml.coi.check).
- ADD: Virtual inheritance: Any class that implements the required methods of our interfaces automatically subclass them, even if they are not direct bases.
- FIX: Make [`SeparableOptEnv`](api.html#cernml.coi.SeparableOptEnv) subclass [`SeparableEnv`](api.html#cernml.coi.SeparableEnv).

## v0.1.0

The dawn of time.
