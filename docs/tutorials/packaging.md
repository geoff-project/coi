# Packaging Crash Course

This tutorial teaches you briefly how to create a Python package, set up a CI
pipeline and publish it to the [Acc-Py
Artifactory](https://artifactory.cern.ch/). It uses
[Acc-Py](https://wikis.cern.ch/display/ACCPY/) to simplify the process, but
also explains what happens under the hood. For each topic, hyperlinks to
further information are provided.

Each section should be reasonably self-contained. Feel free to skip boring
sections or go directly to the one that answers your question. See also [this
walkthrough](https://wikis.cern.ch/display/ACCPY/Deployment+walk-through) on
converting an unstructured repository of Python code into a app-py-deployable
Python package.

## Loading Acc-Py

If you're confident in your Python environment, feel free to skip this section.
This serves as a baseline from which beginners can start and be confident that
none of the experiments here will impact their other projects.

Start out by loading Acc-Py. We recommend using the latest Acc-Py Base
distribution (2020.11 at the time of this writing):

```bash
$ source /acc/local/share/python/acc-py/base/pro/setup.sh
```

If you put this line into your `~/.bash_profile` script, it will be executed
every time you log into your machine. If you don't want this, but you also
don't want to have to remember this long path, consider putting an alias into
your `~/.bash_profile` instead:

```bash
alias setup-acc-py='source /acc/local/share/python/acc-py/base/pro/setup.sh'
```

This way, you can load Acc-Py by invoking `setup-acc-py` on your command line.

```{note}
Acc-Py is only available within the CERN network. Outside, you can either use
your pre-installed Python distribution or use a distribution manager like
[Pyflow](https://github.com/David-OConnor/pyflow),
[Pyenv](https://github.com/pyenv/pyenv) or
[Miniconda](https://docs.conda.io/en/latest/miniconda.html).
```

Further reading:
- [Acc-Py Base](https://wikis.cern.ch/display/ACCPY/Acc-Py+base)
- [difference between the *Base* and the *Interactive*
  distributions](https://wikis.cern.ch/display/ACCPY/Python+distribution)

## Creating a virtual environment

Virtual environments separate dependencies of one project from another. This
way, you can work on one project that uses Tensorflow 1.x, switch your venv,
then work on another project that uses Tensorflow 2.x.

Venvs also allow you to install dependencies that are not available in the
Acc-Py distribution. This approach is much more robust than installing them
into your home directory via `pip install --user`. The latter is discouraged,
as it quickly leads to incomprehensible import errors.

If you're working on your VM, we recommend creating your venv in the `/opt`
directory, since space in your home directory is limited. Obviously, this does
not work on [LXPLUS](https://lxplusdoc.web.cern.ch/), where your home directory
is the only choice.

```bash
$ sudo mkdir -p /opt/venvs        # Create a directory for all your venvs.
$ sudo chown "$USER:" /opt/venvs  # Make it your own (instead of root's).
$ acc-py venv /opt/venvs/coi-example
```

The `acc-py venv` command is a convenience wrapper around the [`venv` standard
library module](https://docs.python.org/3/library/venv.html). In particular, it
passes the `--system-site-packages` flag. This flag ensures that everything
that is preinstalled in the Acc-Py distribution also is available in your new
environment. Without it, you would have to install common dependencies such as
[Numpy](https://numpy.org/).

Once the virtual environment is created, you can activate it like this:

```bash
$ source /opt/venvs/coi-example/bin/activate
$ which python  # Where does our Python interpreter come from?
/opt/venvs/coi-example/bin/python
$ # deactivate  # Leave the venv again.
```

After activating the environment, you can give it a test run by upgrading the
Pip package manager. This should be visible only within your virtual
environment:

```bash
$ pip install --upgrade pip
```

Further reading:
- [Getting started with
  Acc-Py](https://wikis.cern.ch/display/ACCPY/Getting+started+with+Acc-Py)
- [Acc-Py Development
  advice](https://wikis.cern.ch/display/ACCPY/Development+advice)

## Setting up the Project

Time to get started! Go into your projects folder and initialize a project
using Acc-Py:

```bash
$ cd ~/Projects
$ acc-py init coi-example
$ cd ./coi-example
```

```{note}
Don't forget to hit the tab key while typing the above lines, so that your
shell will auto-complete the words for you!
```

The `acc-py init` command creates a basic project structure for you. You can
inspect the results via the [`tree`](http://mama.indstate.edu/users/ice/tree/)
command:

```bash
$ tree
.
├── coi_example
│   ├── __init__.py
│   └── tests
│       ├── __init__.py
│       └── test_coi_example.py
├── README.md
└── setup.py
```

This is usually enough to get started. However, there are two useful files that
Acc-Py does not create for us: `.gitignore` and `pyproject.toml`. We might as
well add them now.

Further reading:
- [Starting a new Python
  project](https://wikis.cern.ch/display/ACCPY/Getting+started+with+Acc-Py#GettingstartedwithAcc-Py-StartinganewPythonproject)
- [Project Layout](https://wikis.cern.ch/display/ACCPY/Project+layout)
- [Creating a Python package from a directory of
  scripts](https://wikis.cern.ch/display/ACCPY/Creating+a+Python+package+from+a+directory+of+scripts)

## Adding `.gitignore` (Optional)

The `.gitignore` file tells Git which files to ignore. It should contain all
sorts of temporary files that are created by our tools and by Python itself
(e.g. `__pycache__/`). You can download a very comprehensive and universally
agreed-on file [from
Github](https://github.com/github/gitignore/blob/master/Python.gitignore).

Note that it is very common to later add project-specific file names and
patterns to this list. Do not hesitate to edit it!

```{note}
If you use an IDE like [PyCharm](https://www.jetbrains.com/pycharm/), it is
very common that IDE-specific config and manifest files will end up in your
project directory. You *could* manually add these files to the `.gitignore`
file of every single project. However, it is simpler to keep these files in a
[global
gitignore](http://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration#_core_excludesfile)
file that is specific to your machine (and not your project) instead.
```


Further reading:
- [Common gitignore files](https://github.com/github/gitignore/)
- [*Ignoring files* in the Git
  book](http://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository#_ignoring)
- [Gitignore reference](http://git-scm.com/docs/git-check-ignore)

## Adding `pyproject.toml` (Optional)

While [Setuptools](https://setuptools.readthedocs.io/) is the most common tool
to build Python packages, [it
is](https://python-poetry.org/docs/pyproject/#poetry-and-pep-517) [not
the](https://flit.readthedocs.io/en/latest/#usage) [only
one](https://thiblahute.gitlab.io/mesonpep517/pyproject.html). By
default, [Pip](https://pip.pypa.io/en/stable/) makes the reasonable assumption
that you do use Setuptools, but it's still good style to declare this fact.

The `pyproject.toml` file fulfills just this purpose: It allows declaring your
build-time dependencies. In addition, many Python tools (e.g.
[Black](https://github.com/psf/black#pyprojecttoml),
[Isort](https://pycqa.github.io/isort/docs/configuration/config_files/),
[Pylint](http://pylint.pycqa.org/en/latest/user_guide/run.html#command-line-options),
[Pytest](https://docs.pytest.org/en/latest/reference/customize.html#pyproject-toml),
[Setuptools-SCM](https://github.com/pypa/setuptools_scm#pyprojecttoml-usage))
can be configured in this file. This reduces clutter in your project directory
and makes it possible to do all configuration using a [single file
format](https://toml.io/en/).

This is what a minimal `pyproject.toml` file using Setuptools looks like:

```toml
[build-system]
requires = ['setuptools', 'wheel']
build-backend = 'setuptools.build_meta'
```

And this is a slightly more complex file that also configures a few tools:

```toml
# Build-time dependencies can have minimum versions and [extras]!
[build-system]
requires = [
    'setuptools >= 42',
    'setuptools-scm[toml] ~= 5.0',
    'wheel',
]
build-backend = 'setuptools.build_meta'

# Setuptools-SCM is a bit quirky in that the *presence* of its config
# block is enough to activate it.
[tool.setuptools_scm]

# Tell isort to be compatible with the Black formatting style. This is
# necessary if you use both tools.
[tool.isort]
profile = 'black'

# As of now, PyTest takes its options in a nested .ini_options table.
# Here, we tell it to also run doctests, not just unit tests.
[tool.pytest.ini_options]
addopts = '--doctest-modules'

# Pylint splits its configuration across multiple tables. Here, we
# disable one warning and minimize their report size.
[tool.pylint.REPORTS]
reports = false
score = false

[tool.pylint.'MESSAGES CONTROL']
disable = ['similarities']
```

Further reading:
- [What the heck is
  pyproject.toml?](https://snarky.ca/what-the-heck-is-pyproject-toml/)
- [PEP 518 introducting
  `pyproject.toml`](https://www.python.org/dev/peps/pep-0518/)
- [Awesome Pyproject.toml](https://github.com/carlosperate/awesome-pyproject)

## Adding dependencies

Once this is done, we can edit the `setup.py` file created for us and fill in
the blanks. This is what the new requirements look like:

```python
# setup.py
REQUIREMENTS: dict = {
    "core": [
        "cernml.coi ~= 0.4.0",
        "gym >= 0.11",
        "matplotlib ~= 3.0",
        "numpy ~= 1.0",
        "pyjapc ~= 2.0",
    ],
    "test": [
        "pytest",
    ],
}
```

And this is the new `setup()` call:

```python
# setup.py (cont.)
setup(
    name="coi-example",
    version="0.0.1.dev0",
    author="Your Name",
    author_email="your.name@cern.ch",
    description="An example for how to use the cernml-coi package",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.6, <4",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    # Rest as before …
)
```

Of all these changes, only the *description* and the *requirements* were really
necessary. Things like classifiers are nice-to-have metadata that we could
technically also live without.

Further reading:
- [Packaging of your
  module](https://wikis.cern.ch/display/ACCPY/Development+Guidelines#DevelopmentGuidelines-Packagingofyourmodule)
- [Setuptools
  Quickstart](https://setuptools.readthedocs.io/en/latest/userguide/quickstart.html)
- [Dependency management in
  Setuptools](https://setuptools.readthedocs.io/en/latest/userguide/dependency_management.html)

## Version Requirements (Digression)

When specifying your requirements, you should make sure to put in a reasonable
version range.

* Being too lax with your requirements means that one of your dependencies
  might change and break your code without prior warning.
* Being too strict with your requirements means that other people will have a
  harder time making your package work in conjunction with theirs.

There are two common ways to specify version ranges:

- `~= 0.4.0` means: "I am compatible with all versions 0.4.X, but the last part
  must at least be 0". This is a good choice if the target adheres to [Semantic
  Versioning](https://semver.org/). (Not all packages do!)
- `>=0.4, <0.5` means "I am compatible with all versions greater than (or equal
  to) 0.4.0 but lower than 0.5". This is a reasonable choice if you know a
  version of the target that works for you and a version that doesn't.

[Other
specifiers](https://www.python.org/dev/peps/pep-0440/#version-specifiers) may
also make sense if you know that the target makes very strong backwards
compatibility guarantees (e.g. NumPy or Setuptools).

Further reading:
- [Dependency and release
  management](https://wikis.cern.ch/display/ACCPY/Dependency+and+release+management)

## Interlude: Test Run

With this minimum in place, your package already can be installed via Pip! Give
it a try:

```bash
$ pip install .  # "." means "the current directory".
```

Once this is done, your package is installed in your environment and can be
imported by other packages without any path hackery:

```python
>>> import coi_example
>>> coi_example.__version__
'0.0.1'
>>> import pkg_resources
>>> pkg_resources.get_distribution('coi-example')
coi-example 0.0.1.dev0 (/opt/venvs/coi-example/lib/python3.7/site-packages)
```

Of course, you can always remove your package again:

```bash
$ pip uninstall coi-example
```

Note that installation puts a _copy_ of your package into your venv. This means
that every time you change the code, you have to reinstall it for the changes
to become visible.

There is also the option to link from your venv to your source directory. In
this case, all changes to the source code become visible immediately. This is
bad for a production release, but extremely useful during development. This
feature is called an *editable install*:

```bash
$ pip install --editable .
```

Further reading:
- [When would the -e, --editable option be useful with pip
  install?](https://stackoverflow.com/questions/35064426)
