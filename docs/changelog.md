# Changelog

This package uses a variant of [Semantic Versioning](https://semver.org/) that
makes additional promises during the initial development (major version 0):
whenever breaking changes to the public API are published, the first non-zero
version number will increase. This means that code that uses COI version 0.6.0
will continue to work with version 0.6.1, but may break with version 0.7.0.

## Unreleased

- ADD: Add install extra `doc_only` to build docs in a non-CERN environment. (This skips the PyJapc dependency.)

## v0.8.2

- ADD: New optional attributes {attr}`~cernml.coi.SingleOptimizable.objective_name`, {attr}`~cernml.coi.SingleOptimizable.param_names` and {attr}`~cernml.coi.SingleOptimizable.constraint_names` to {class}`~cernml.coi.SingleOptimizable`.
- FIX: Adjust the documentation of {meth}`~cernml.coi.FunctionOptimizable.get_objective_function_name()` and {meth}`~cernml.coi.FunctionOptimizable.get_param_function_names()` to be in line with its {class}`~cernml.coi.SingleOptimizable` counter-parts.

## v0.8.1

- ADD: {meth}`cernml.coi.Config.extend()` to make configuration more composable.
- ADD: {class}`cernml.coi.ConfigValues` as a convenience alias for {class}`types.SimpleNamespace`.
- ADD: {func}`~cernml.coi.checkers.check_configurable()` for all implementors of the {class}`~cernml.coi.Configurable` interface.
- FIX: Broken links in the API docs of the {doc}`api/checkers`.

## v0.8.0

- BREAKING: Drop Python 3.6 support.
- BREAKING: Require {doc}`importlib-metadata<importlib_metadata:index>` 3.6 (was 3.4).
- BREAKING: Drop the `cernml.coi.__version__` attribute. To query the COI version, use instead {mod}`importlib_metadata`. (With Python 3.8+, this is in the standard library as {mod}`importlib.metadata`.)
- BREAKING: Remove `PascalPase`-style members of {class}`~cernml.coi.Machine`. Use the `SCREAMING_SNAKE_CASE`-style members intead.
- BREAKING: Remove `cernml.coi.unstable.japc_utils`. It is now provided by {doc}`cernml-coi-utils<utils:index>` as {mod}`cernml.japc_utils`.
- BREAKING: Remove `cernml.coi.unstable.renderer` and `cernml.coi.mpl_utils`. Both are now provided by {doc}`cernml-coi-utils<utils:index>`'s {mod}`cernml.mpl_utils`.
- BREAKING: Remove `cernml.coi.unstable.cancellation`. The module is now available as {mod}`cernml.coi.cancellation`.
- BREAKING: Remove `cernml.coi.unstable`. The module is now empty.
- BREAKING: Change {class}`~cernml.coi.Config.Field` from a {class}`~typing.NamedTuple` into a {func}`~dataclasses.dataclass`.
- ADD: Support for {doc}`importlib-metadata<importlib_metadata:index>` 4.

## v0.7.6

- FIX: Backport change from v0.8.x that removes {func}`~cernml.mpl_utils.iter_matplotlib_figures()` calls from {func}`cernml.coi.check()`. This avoids deprecation warnings introduced in the previous version.

## v0.7.5

- FIX: Increase the stacklevel of the [](#v074) deprecation warnings so that they appear more reliably.

## v0.7.4

- ADD: Merge {class}`~cernml.coi.FunctionOptimizable` and {func}`~cernml.coi.checkers.check_function_optimizable()` from cernml-coi-funcs v0.2.2.
- ADD: Deprecate `cernml.coi.unstable.japc_utils`, {doc}`renderer<utils:api/mpl_utils>` and {doc}`mpl_utils<utils:api/mpl_utils>`. The same features are provided by the {doc}`cernml-coi-utils<utils:index>` package.
- ADD: Stabilize the {mod}`~cernml.coi.cancellation` module. It is now available under `cernml.coi.cancellation`. The old location at `cernml.coi.unstable.cancellation` remains available but is deprecated.
- FIX: Correct the type annotation on {class}`~cernml.coi.SingleOptimizable.get_initial_params()` from {data}`~std:typing.Any` to {class}`~np:numpy.ndarray`.

## v0.7.3

- ADD: Split the COI tutorial into a {doc}`tutorial on packaging <tutorials/packaging>` and a {doc}`tutorial on the COI proper <tutorials/implement-singleoptimizable>`.
- FIX: Improve the documentation of {class}`~gym.Env` and other Gym classes.
- OTHER: Upgraded docs. Switch markdown parser from Recommonmark to Myst. Change theme from *Read the Docs* to *Sphinxdoc*.
- OTHER: Changes to the CI pipeline. Version of code checkers are pinned now. Added Pycodestyle to the list of checkers to run.

## v0.7.2

- ADD: {meth}`ParamStream.next_if_ready()<cernml.japc_utils.ParamStream.pop_if_ready()>` no longer checks stream's the cancellation token.
- ADD: {attr}`ParamStream.parameter_name <cernml.japc_utils.ParamStream.parameter_name>` and {attr}`ParamGroupStream.parameter_names <cernml.japc_utils.ParamGroupStream.parameter_names>`.
- FIX: {func}`repr()` of {class}`~cernml.japc_utils.ParamGroupStream` called wrong Java API.

## v0.7.1

- ADD: Enum member {attr}`Machine.ISOLDE <cernml.coi.Machine.ISOLDE>`.

## v0.7.0

- BREAKING: Remove [Cancellation tokens](guide/cancellation.md#cancellation). The stable API did not accommodate all required use cases and could not be fixed in a backwards-compatible manner.
- ADD: Re-add [Cancellation tokens](guide/cancellation.md#cancellation) as an unstable module. The new API supports cancellation completion and resets.

## v0.6.2

- ADD: Rename all variants of {class}`~cernml.coi.Machine` to `SCREAMING_SNAKE_CASE`. The `PascalCase` names remain available, but issue a deprecation warning.
- ADD: [Cancellation tokens](guide/cancellation.md#cancellation).
- ADD: Cancellation support to {func}`parameter streams<cernml.japc_utils.subscribe_stream>`.
- ADD: Property {attr}`~cernml.japc_utils.ParamStream.locked` to parameter streams.
- ADD: Document [parameter streams](guide/cancellation.md#synchronization).
- ADD: Document plugin support in {func}`~cernml.coi.check`.
- FIX: Add default values for all known {attr}`~cernml.coi.Problem.metadata` keys.
- FIX: Missing `figure.show()` when calling {meth}`SimpleRenderer.update("human")<cernml.mpl_utils.Renderer.update>`.

## v0.6.1

- ADD: *title* parameter to {meth}`SimpleRenderer.from_generator()<cernml.mpl_utils.FigureRenderer.from_callback>`.
- FIX: Missing `figure.draw()` when calling {meth}`SimpleRenderer.update("human")<cernml.mpl_utils.Renderer.update>`.

## v0.6.0

- BREAKING: Instate [a variant of semantic versioning](#changelog).
- BREAKING: Move the {doc}`Matplotlib utilities<utils:api/mpl_utils>` into `cernml.coi.mpl_utils`.
- ADD: {class}`cernml.coi.unstable.renderer<cernml.mpl_utils.Renderer>`.
- ADD: {mod}`cernml.coi.unstable.japc_utils<cernml.japc_utils>`.
- ADD: Allow a single {class}`~matplotlib.figure.Figure` as return value of {meth}`render("matplotlib_figure")<cernml.coi.Problem.render>`.

## v0.5.0

- BREAKING: Add {meth}`cernml.coi.Problem.close`.

## v0.4.7

- FIX: Typo in {attr}`~cernml.coi.Problem.metadata` key `"cern.machine"`.
- FIX: Mark {attr}`~cernml.coi.Problem.metadata` as a class variable.
- FIX: Make base {attr}`~cernml.coi.Problem.metadata` a {class}`~types.MappingProxyType` to prevent accidental mutation.

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

- FIX: Expose {func}`cernml.coi.check` argument *headless*.

## v0.4.0

- BREAKING: Mark the package as fully type-annotated.
- BREAKING: Switch to pyproject.toml and setup.cfg based building.
- BREAKING: Rewrite `check_env()` as {func}`cernml.coi.check`.
- ADD: {func}`cernml.coi.mpl_utils.iter_matplotlib_figures()<cernml.mpl_utils.iter_matplotlib_figures>`.

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
- ADD: {doc}`Environment registry<api/registry>`.
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
