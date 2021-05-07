# Changelog

This package uses a variant of [Semantic Versioning](https://semver.org/) that
makes additional promises during the initial development (major version 0):
whenever breaking changes to the public API are published, the first non-zero
version number will increase. This means that code that uses COI version 0.6.0
will continue to work with version 0.6.1, but may break with version 0.7.0.

The exception to this are the contents of `cernml.coi.unstable`, which may
change in any given release.

## v0.7.3

- ADD: Split the COI tutorial into a [tutorial on packaging](tutorials/packaging.md) and a [tutorial on the COI proper](tutorials/implement-singleoptimizable.md).
- FIX: Improve the documentation of {class}`~gym.Env` and other Gym classes.
- OTHER: Upgraded docs. Switch markdown parser from Recommonmark to Myst. Change theme from *Read the Docs* to *Sphinxdoc*.
- OTHER: Changes to the CI pipeline. Version of code checkers are pinned now. Added Pycodestyle to the list of checkers to run.

## v0.7.2

- ADD: [`next_if_ready()`](api.html#cernml.coi.unstable.japc_utils.ParamStream.next_if_ready) no longer checks stream's the cancellation token.
- ADD: [`parameter_name`](api.html#cernml.coi.unstable.japc_utils.ParamStream.parameter_name) and [`parameter_names`](api.html#cernml.coi.unstable.japc_utils.ParamGroupStream.parameter_names).
- FIX: `repr()` of [`ParamGroupStream`](api.html#cernml.coi.unstable.japc_utils.ParamGroupStream) called wrong Java API.

## v0.7.1

- ADD: Enum member [`Machine.ISOLDE`](api.html#cernml.coi.Machine.ISOLDE).

## v0.7.0

- BREAKING: Remove [Cancellation tokens](guide.md#cancellation). The stable API did not accommodate all required use cases and could not be fixed in a backwards-compatible manner.
- ADD: Re-add [Cancellation tokens](guide.md#cancellation) as an unstable module. The new API supports cancellation completion and resets.

## v0.6.2

- ADD: Rename all variants of {class}`~cernml.coi.Machine` to `SCREAMING_SNAKE_CASE`. The `PascalCase` names remain available, but issue a deprecation warning.
- ADD: [Cancellation tokens](guide.md#cancellation).
- ADD: Cancellation support to {func}`parameter streams<cernml.coi.unstable.japc_utils.subscribe_stream>`.
- ADD: Property {attr}`~cernml.coi.unstable.japc_utils.ParamStream.locked` to parameter streams.
- ADD: Document [parameter streams](guide.md#synchronization).
- ADD: Document plugin support in {func}`~cernml.coi.check`.
- FIX: Add default values for all known {attr}`~cernml.coi.Problem.metadata` keys.
- FIX: Missing `figure.show()` when calling {meth}`SimpleRenderer.update("human")<cernml.coi.unstable.renderer.SimpleRenderer.update>`.

## v0.6.1

- ADD: `title` parameter to {meth}`SimpleRenderer.from_generator<cernml.coi.unstable.renderer.SimpleRenderer.from_generator>`.
- FIX: Missing `figure.draw()` when calling {meth}`SimpleRenderer.update("human")<cernml.coi.unstable.renderer.SimpleRenderer.update>`.

## v0.6.0

- BREAKING: Instate [a variant of semantic versioning](#changelog).
- BREAKING: Move the Matplotlib utilities into [`mpl_utils`](api.md#matplotlib-utilities).
- ADD: Unstable module {class}`renderer<cernml.coi.unstable.renderer.Renderer>`.
- ADD: Unstable module [`japc_utils`](api.md#pyjapc-utilities).
- ADD: Allow a single `Figure` as return value of {meth}`render("matplotlib_figure")<cernml.coi.Problem.render>`.

## v0.5.0

- BREAKING: Add {meth}`cernml.coi.Problem.close`.

## v0.4.7

- FIX: Typo in {attr}`~cernml.coi.Problem.metadata` key `"cern.machine"`.
- FIX: Mark {attr}`~cernml.coi.Problem.metadata` as a class variable.
- FIX: Make base {attr}`~cernml.coi.Problem.metadata` a `mappingproxy` to prevent accidental mutation.

## v0.4.6

- BREAKING: Remove keyword arguments from the signature of {meth}`~cernml.coi.Problem.render`.
- ADD: Start distributing wheels.

## v0.4.5

- ADD: Plugin entry point and logging to {func}`cernml.coi.check`.

## v0.4.4

- ADD: Export some (for now) undocumented helper functions from {func}`cernml.coi.checkers<cernml.coi.check>`.

## v0.4.3

- BREAKING: Switch to setuptools-scm for versioning.
- ADD: Unmark {meth}`~cernml.coi.Problem.render` as an abstract method.

## v0.4.2

- ADD: Make dependency on Matplotlib optional.
- FIX: Add missing check for defined render modes to {func}`cernml.coi.check`.

## v0.4.1

- FIX: Expose {func}`cernml.coi.check` argument `headless`.

## v0.4.0

- BREAKING: Mark the package as fully type-annotated.
- BREAKING: Switch to pyproject.toml and setup.cfg based building.
- BREAKING: Rewrite `check_env()` as {func}`cernml.coi.check`.
- ADD: {func}`~cernml.coi.mpl_utils.iter_matplotlib_figures`.

## v0.3.3

- FIX: Set window title in example `configurable.py`.

## v0.3.2

- ADD: `help` argument to {meth}`cernml.coi.Config.add`.

## v0.3.1

- BREAKING: Make all submodules private.
- ADD: {class}`~cernml.coi.Configurable` interface.

## v0.3.0

- BREAKING: Rename `Optimizable` to {class}`~cernml.coi.SingleOptimizable`.
- BREAKING: Add dependency on Numpy.
- ADD: {class}`~cernml.coi.Problem` interface.
- ADD: [Environment registry](api.md#problem-registry).
- FIX: Check inheritance of `env.unwrapped` in {func}`check_env()<cernml.coi.check>`.

## v0.2.1

- FIX: Fix broken CI tests.

## v0.2.0

- BREAKING: Rename package from `cernml.abc` to `cernml.coi` (And the distribution from `cernml-abc` to `cernml-coi`).
- BREAKING: Rename `OptimizeMixin` to {class}`Optimizable<cernml.coi.SingleOptimizable>`.
- BREAKING: Add {attr}`~cernml.coi.Problem.metadata` key `"cern.machine"`.
- BREAKING: Add more restrictions to {func}`env_checker()<cernml.coi.check>`.
- ADD: Virtual inheritance: Any class that implements the required methods of our interfaces automatically subclass them, even if they are not direct bases.
- FIX: Make {class}`~cernml.coi.SeparableOptEnv` subclass {class}`~cernml.coi.SeparableEnv`.

## v0.1.0

The dawn of time.
