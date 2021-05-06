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
$ alias setup-acc-py='source /acc/local/share/python/acc-py/base/pro/setup.sh'
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
Acc-Py does not create for us: .gitignore and pyproject.toml. We might as well
add them now.

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

## Adding pyproject.toml (Optional)

While [Setuptools](https://setuptools.readthedocs.io/) is the most common tool
to build Python packages, [it
is](https://python-poetry.org/docs/pyproject/#poetry-and-pep-517) [not
the](https://flit.readthedocs.io/en/latest/#usage) [only
one](https://thiblahute.gitlab.io/mesonpep517/pyproject.html). By
default, [Pip](https://pip.pypa.io/en/stable/) makes the reasonable assumption
that you do use Setuptools, but it's still good style to declare this fact.

The pyproject.toml file fulfills just this purpose: It allows declaring your
build-time dependencies. In addition, many Python tools (e.g.
[Black](https://github.com/psf/black#pyprojecttoml),
[Isort](https://pycqa.github.io/isort/docs/configuration/config_files/),
[Pylint](http://pylint.pycqa.org/en/latest/user_guide/run.html#command-line-options),
[Pytest](https://docs.pytest.org/en/latest/reference/customize.html#pyproject-toml),
[Setuptools-SCM](https://github.com/pypa/setuptools_scm#pyprojecttoml-usage))
can be configured in this file. This reduces clutter in your project directory
and makes it possible to do all configuration using a [single file
format](https://toml.io/en/).

This is what a minimal pyproject.toml file using Setuptools looks like:

```toml
# pyproject.toml
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
  pyproject.toml](https://www.python.org/dev/peps/pep-0518/)
- [Awesome Pyproject.toml](https://github.com/carlosperate/awesome-pyproject)

## Adding dependencies

Once this is done, we can edit the setup.py file created for us and fill in
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
- [Setuptools
  keywords](https://setuptools.readthedocs.io/en/latest/references/keywords.html)

## Version Requirements (Digression)

When specifying your requirements, you should make sure to put in a reasonable
version range.

* Being too lax with your requirements means that one of your dependencies
  might change and break your code without prior warning.
* Being too strict with your requirements means that other people will have a
  harder time making your package work in conjunction with theirs.

There are two common ways to specify version ranges:

- `~= 0.4.0` means: “I am compatible with all versions 0.4.X, but the last part
  must at least be 0”. This is a good choice if the target adheres to [Semantic
  Versioning](https://semver.org/). (Not all packages do!)
- `>=0.4, <0.5` means “I am compatible with all versions greater than (or equal
  to) 0.4.0 but lower than 0.5”. This is a reasonable choice if you know a
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

## SDists and Wheels (Digression)

Bringing a Python code base into a publishable format is a surprisingly
complicated topic with a lot of historical baggage. This section skips most of
the history and explains the terms that are most relevant today.

Python is an interpreted language. As such, one *could* think that it's enough
to have the source code of a program to run it. However, this assumption is
wrong for a number of reasons:

- some libraries contain [C extensions](https://github.com/numpy/numpy/);
- some libraries [generate their own code](https://launchpad.net/pytz) during
  installation;
- all libraries must provide [their
  metadata](https://www.python.org/dev/peps/pep-0345/) in a certain,
  standardized format.

As such, even Python packages must be built before publication.

The publishable result of the build process is called a [**distribution** or
**package**](https://packaging.python.org/glossary/#term-Distribution-Package).
Several historical kinds of distributions exist, but only two remain relevant
today: sdists and wheels.

[**Sdists**](https://packaging.python.org/glossary/#term-Source-Distribution-or-sdist)
(source distributions) contain only the above mentioned metadata and all
relevant source files. It does not contain files that are not packaged by the
author (e.g. `.gitignore`). Because it contains source code, it it must compile
its C extensions (if any). For this reason, installation is a bit slower and
may run arbitrary code. Sdists are created via `python setup.py sdist`.

[**Wheels**](https://packaging.python.org/glossary/?highlight=sdist#term-Wheel)
are a binary distribution format. Under the hood, they are zip files with a
standardized layout and file name. They are fully built and any C extensions
are already compiled. This makes them faster to install than sdists. The
disadvantage is that *if* your project contains C extensions, you have to
provide one wheel for each supported platform. Wheels are created via `python
setup.py bdist_wheel`.

Given that most projects will be written purely in Python, wheels are the
preferred distribution format. Depending on circumstances, it may make sense to
publish an sdist in addition. The way to manually create and upload a
distribution to the package repository is [described
elsewhere](https://wikis.cern.ch/display/ACCPY/Development+Guidelines#DevelopmentGuidelines-CreationandUploadofyourpackage).
See [](#releasing-a-package-via-ci) for the preferred and supported method at
CERN.

Further reading:
- [What are Python wheels and why should you
  care?](https://realpython.com/python-wheels/)
- [Building wheels for Python
  packages](https://wikis.cern.ch/display/ACCPY/Building+wheels+for+Python+packages)
- [Python packaging user guide](https://packaging.python.org/)
- [Twisted history of Python
  packaging](https://www.youtube.com/watch?v=lpBaZKSODFA) (2012)

## Continuous Integration

[Continuous integration](https://en.wikipedia.org/wiki/Continuous_integration)
is a software development strategy that favors frequent merging of features
into the main branch of a project to prevent code divergence. To facilitate
this, websites like Gitlab offer
[pipelines](https://gitlab.cern.ch/help/ci/quick_start/index.md) that
automatically build and test code on each commit.

[Continuous delivery](https://en.wikipedia.org/wiki/Continuous_delivery) takes
the practice a step further and also automates the publication of software
using the same pipeline. Nowadays, when people talk about “CI/CD”, they usually
refer to having an automated pipeline of tests and publication.

All of this is important to us because Gitlab's CI/CD pipeline is the only
supported way to publish Python packages on the [Acc-Py package
index](https://wikis.cern.ch/pages/viewpage.action?pageId=145493385).

The Gitlab CI/CD pipeline is configured through a file called `.gitlab-ci.yml`
at the root of your project. Run the command `acc-py init-ci` to have an
automatically generated version of this file added to your project. It should
look somewhat like this:

```yaml
include:
  - project: acc-co/devops/python/acc-py-devtools
    file: acc_py_devtools/templates/gitlab-ci/python.yml

variables:
  project_name: coi_example
  PY_VERSION: '3.7'

build_wheel:
  extends: .acc_py_build_wheel

test_install:
  extends: .acc_py_full_test

release_wheel:
  extends: .acc_py_release_wheel

# More jobs …
```

The first block (`include`) textually includes a lot of [pre-defined job
templates from
Acc-Py](https://gitlab.cern.ch/acc-co/devops/python/acc-py-devtools/tree/master/acc_py_devtools/templates/gitlab-ci).
These templates tell Gitlab how to test or publish a Python package, so you
don't have to. You can recognize these templates by [having a period `.` in
front of their name](https://gitlab.cern.ch/help/ci/yaml/README.md#hide-jobs).

The next block (`variables`) defines Acc-Py-specific variables that configure
the job templates we just included. They tell Acc-Py which directory contains
your Python code and which Python version should be used for testing.

Each subsequent block defines a **job** that is run on the Gitlab servers. Each
job has a trigger (on each commit, on each Git tag, manually, etc.) and a stage
(build → test → deploy). Whenever a trigger fires, all relevant jobs are
collected into a pipeline and run, one stage after the other.

The jobs in our file all don't actually define of this – they simply reuse the
values already set in their respective job template via the `extends` keyword.
[See here for an
example](https://gitlab.cern.ch/acc-co/devops/python/acc-py-devtools/-/blob/master/acc_py_devtools/templates/gitlab-ci/dev_testing.yml).

Further reading:
- [Get started with GitLab
  CI/CD](https://gitlab.cern.ch/help/ci/quick_start/index.md)
- [Keyword reference for the .gitlab-ci.yml
  file](https://gitlab.cern.ch/help/ci/yaml/README.md)

## Testing Your Package

As you might have noticed, the `acc-py init` call created a subpackage of your
package called “tests”. As a dynamically typed language, Python cannot rely on
compiler type safety to ensure the correctness of your code; unit tests will
have to carry this weight.

Acc-Py initializes your `.gitlab-ci.yml` file with two jobs for testing:
- a [*dev
  test*](https://gitlab.cern.ch/acc-co/devops/python/acc-py-devtools/-/blob/master/acc_py_devtools/templates/gitlab-ci/dev_testing.yml)
  that runs the tests directly in your source directory,
- an [*install
  test*](https://gitlab.cern.ch/acc-co/devops/python/acc-py-devtools/-/blob/master/acc_py_devtools/templates/gitlab-ci/install_test.yml)
  that installs your package and runs the tests in the installed copy. This is
  particularly important, as it ensures that your package will work not just
  for you, but also for your users.

Both you the same program, [Pytest](https://pytest.org/), to discover and run
your unit tests. Click their respective links to find the exact invocations.

The way that Pytest finds your unit tests is simple: It searches for files that
match the pattern `test_*.py` and, inside, searches for functions that match
`test_*` and classes that match `Test*`. All found methods and functions are
run. If they finish without raising an exception, they are assumed successful,
otherwise they have failed.

If you have any non-trivial logic in your code – anything that goes beyond
reading, and setting parameters – it is highly recommended to put them into
separate functions. These functions should only depend on their parameters (and
no global state). This makes it much easier to write tests for them to ensure
that they work as expected – and most importantly, that future changes won't
silently break them!

If you're writing a COI optimization problem that does not depend on JAPC or
LSA, there is one easy test case you can always add: run the COI checker with
your class to catch some common pitfalls:

```python
# coi_example/tests/test_coi_example.py
from cernml import coi

def test_checker():
    env = coi.make("YourEnv-v0")
    coi.check(env, warn=True, headless=True)
```

If your program is in a very strange niche where it is impossible to test it
reliably, you can also remove the testing code: remove the “tests” package, and
delete the two test jobs from your `.gitlab-ci.yml` file.

Further reading:
- [Tests as part of application code](https://docs.pytest.org/en/latest/explanation/goodpractices.html#tests-as-part-of-application-code)
- [GUI testing](https://wikis.cern.ch/display/ACCPY/GUI+Testing)
- [PAPC – a pure Python PyJapc offline
  simulator](https://wikis.cern.ch/display/ACCPY/papc+-+a+pure+Python+PyJapc+offline+simulator)
- [`unittest.mock` standard library
  module](https://docs.python.org/3/library/unittest.mock.html)
- [`doctest` standard library
  module](https://docs.python.org/3/library/doctest.html)
- [Example CI setup to test projects that rely on
  Java](https://gitlab.cern.ch/scripting-tools/pyjapc/-/blob/master/.gitlab-ci.yml)

## Releasing a Package via CI

Once CI has been set up and tests have been written (or disabled), your package
is ready for publication! Normally,
[twine](https://twine.readthedocs.io/en/latest/) is the command of choice to
upload a package to the package index, but Acc-Py is already taking over this
job for us.

```{warning}
Publishing a package is permanent! Once your code has been uploaded to the
index, it is almost impossible to remove it again. And once a project name has
been claimed on the package index, it usually cannot be transferred to another
project. Make double- and triple-sure that everything is correct before
following the next steps.
```

If your project is not in a Git repository yet, this is the time to check it
in:

```bash
$ git init
$ git add --all
$ git commit --message="Initial commit."
$ git remote add origin ...  # Clone URL of your repo on Gitlab
$ git push --set-upstream origin master
```

Then, all that is necessary to publish the next (or first) version of your
package is to create a Git tag and upload it to Gitlab.

```bash
$ # The tag name doesn't actually matter, but let's stay consistent.
$ git tag v0.0.1.dev0
$ git push --tags
```

This will trigger a CI pipeline that builds, tests and eventually
[releases](https://gitlab.cern.ch/acc-co/devops/python/acc-py-devtools/-/blob/master/acc_py_devtools/templates/gitlab-ci/upload_on_tag.yml)
your code. Once this pipeline has finished successfully (which includes running
your tests), your package is published and immediately available anywhere
inside CERN:

```bash
$ cd ~
$ pip install coi-example
```

```{note}
The version of your package is determined by setup.py, not by the tag name you
choose. If you tag another commit that declares the same version number, and
you push this tag, your pipeline will run and the deploy stage will fail due to
the version conflict.
```

Further reading:
- [Python package
  index/repository](https://wikis.cern.ch/pages/viewpage.action?pageId=145493385)
- [Acc-Py repository](https://acc-py-repo.cern.ch/)

## Extra Credit: setup.cfg

This section, like the subsequent ones, gives a little bit more background
information on Python packaging, but is not necessary to get off the ground.
Especially if you're a beginner, feel free to stop here.

While the setup.py is nice and generally gets the work done, there are
several problems with it:

- The logic on top the bare `setup()` quickly becomes hard to read.
- It is impossible to extract project metadata without executing arbitrary
  Python code. Security-minded people generally don't like that.
- Most projects don't *need* to execute arbitrary Python code to declare their
  package metadata.

For this reason, setuptools recommends to configure your project using a new
file called setup.cfg. It fulfills the same role as setup.py, but as a
configuration file, it can be read without executing Python code. Certain
patterns that require Python login in setup.py can be handled via special value
types.

For example, this setup script:

```python
# setup.py
from pathlib import Path
from setuptools import setup, find_packages

PROJECT_ROOT = Path(__file__).parent.absolute()
PKG_DIR = PROJECT_ROOT / "my_package"

with open(PKG_DIR / "__init__.py", encoding="utf-8") as infile:
    for line in infile:
        name, equals, version = line.partition("=")
        name = name.strip()
        version = version.strip()
        if name == "VERSION" and version[0] == version[-1] == '"':
            version = version[1:-1]
            break
    else:
        raise ValueError("no version number found")

with open(PROJECT_ROOT / "README.rst", encoding="utf-8") as infile:
    readme = infile.read()

setup(
    name="py_package",
    version=version,
    long_description=readme,
    packages=find_packages(),
    install_requires=[
        "requests",
        "importlib; python_version == 2.6",
    ]
    extras_require={
        "pdf": ["ReportLab>=1.2; RXP"],
        "rest": ["docutils>=0.3; pack == 1.1, == 1.3"],
    },
)
```

does the same as this configuration file:

```cfg
# setup.cfg
[metadata]
name = my_package
version = attr: src.VERSION  # Does not import your package in most cases.
long_description = file: README.rst  # Reads the entire file as a string.

[options]
packages = find:  # Same as the `find_packages()` function.
install_requires =  # Lists of strings use hanging indent.
    requests
    importlib; python_version == "2.6"

# Complex options are put into separate sections.
[options.extras_require]
pdf = ReportLab>=1.2; RXP
rest = docutils>=0.3; pack ==1.1, ==1.3
```

If you manage to put all your data into setup.cfg, your setup.py file can
become as simple as:

```python
# setup.py
from setuptools import setup
setup()
```

If you use setuptools version 40.9 or later (which should be specified [in your
pyproject.toml file](#adding-pyprojecttoml-optional)), you can completely
remove the setup.py file in this case.

Further reading:
- [What's the difference between setup.py and setup.cfg in python
  projects](https://stackoverflow.com/questions/39484863/)
- [Setuptools
  quickstart](https://setuptools.readthedocs.io/en/latest/userguide/quickstart.html)
- [Configuring `setup()` using setup.cfg
  files](https://setuptools.readthedocs.io/en/latest/userguide/declarative_config.html)
- [Setuptools
  keywords](https://setuptools.readthedocs.io/en/latest/references/keywords.html)

## Extra Credit: Single-Sourcing Your Version Number

Over time, it may become annoying to manually bump your version number every
time you release a new version of your package. Since Acc-Py already [requires
us to use Git tags to publish our package](#releasing-a-package-via-ci) (but
doesn't actually read the tag name), it would be nice if we could co-opt the
tag name for this purpose.

[Setuptools-SCM](https://pypi.org/project/setuptools-scm/) is a plugin for
setuptools that takes care of this task. It generates your package's version
number automatically based on your Git tags and feeds it directly into
setuptools. The minimal setup looks as follows:

```toml
# pyproject.toml
[build-system]
requires = ['setuptools>=42', 'wheel', 'setuptools_scm[toml]>=3.4']

# Add an empty tool section to enable version inference.
[tool.setuptools_scm]
```

```cfg
# setup.cfg
[metadata]
name = my_package
# No version declaration at all!
# version = automatically generated
...
```

You can also add a `write_to` line to your configuration to automatically
generate *during installation* a source file in your package that contains the
version number. This way, your package can expose its version in a
`__version__` variable:

```toml
# pyproject.toml
[tool.setuptools_scm]
write_to = 'my_package/version.py'
```

```python
# my_package/__init__.py
from .version import version as __version__
...
```

```{warning}
The practice of adding a `__version__` variable to your package is
[deprecated](https://www.python.org/dev/peps/pep-0396/#pep-rejection). In new
code, you should fetch other packages' version through the
[`importlib.metadata`](https://docs.python.org/3/library/importlib.metadata.html)
standard library package (Python 3.8+) or its
[backport](https://importlib_metadata.readthedocs.io/) (Python 3.6+).
```

Some solutions that are not recommended:
1. Importing your own package in setup.py and passing `my_package.__version__`
   to the `setup()` call. This breaks as soon as your package imports any of
   its dependencies (e.g. Numpy) because Pip hasn't had a chance to install
   your dependencies yet.
2. Specify `version = attr: my_package.__version__` in setup.cfg: On setuptools
   before version 46.4, this does the same as the first option – and so has the
   same problems.
3. Specify `version = attr: my_package.__version__` in setup.cfg *and* require
   `setuptools>=46.4` in pyproject.toml: New versions of setuptools textually
   analyze your package to find `__version__` without running your code. If
   this fails, however, setuptools will fall back to importing your package and
   break again.

Further reading:
- [Single-sourcing the package
  version](https://packaging.python.org/guides/single-sourcing-package-version/)
- [Zest.releaser](https://zestreleaser.readthedocs.io/en/latest/)

## Extra Credit: Automatic Code Formatting

Although a lot of programmers have needlessly strong opinions on it, good code
formatting has two undeniable advantages:
- it makes it easier to spot typos and related bugs;
- it makes it easier for other people to read your code – if they're familiar
  with the formatting style.

At the same time, it requires effort to pick, follow and enforce a particular
style guide. Ideally, code formatting would be consistent, automatic and
require as little human input as possible.

[Black](https://github.com/psf/black) qualifies for all of these:
- It is an automatic formatter. That means you don't have to follow its style
  yourself. You run it over your code base and it edits your files in place to
  be uniformly formatted.
- [Most IDEs support
  it](https://black.readthedocs.io/en/stable/editor_integration.html). This
  means you can run it automatically on every file save or Git commit. With
  this, you can stop thinking about formatting (almost) entirely.
- It is almost unconfigurable This obviates pointless style discussions, as
  they are known in the C++ world.

On top of it, you may also want to run [ISort](https://pycqa.github.io/isort/)
to sort your import statements for you. To make ISort compatible with Black,
add these lines to your configuration:

```python
# pyproject.toml
[tool.isort]
profile = "black"
```

Further reading:
- [The *Black* code
  style](https://github.com/psf/black/blob/master/docs/the_black_code_style.md)

## Extra Credit: Linting

As an interpreted and dynamically typed language, Python cannot rely on a
type-checking compiler to verify that your code does what you expect it to do.
Instead, Python developers must rely on *linters*, i.e. static-analysis tools,
to find bugs and anti-patterns.

The simplest choice for beginners [Pylint](https://pylint.readthedocs.io/). It
is a general-purpose linter that catches style and complexity issues as well as
outright bugs. In contrast to Black, Pylint is extremely configurable and
encourages users to enable or disable lints as necessary. Here is an example
configuration:

```python
# pyproject.toml
[tool.pylint.FORMAT]
max-line-length=88  # Compatibility with Black.
ignore-long-lines = '<?https?://\S+>?$'  # Ignore long URLs.

[tool.pylint.REPORTS]
# Don't show a summary, just print the errors, one per line.
reports = false
score = false

[tool.pylint.'MESSAGES CONTROL']
disable = [
    'bad-continuation',
]
```

Sometimes, Pylint gives you a warning that you find generally useful, but
shouldn't apply to an individual piece of code. In this case you can add a
comment like this to suppress the warning:

```python
# pylint: disable = unused-import
```

These comments respect scoping. If you put them within a function, they apply
to only that function. If you put them at the end of a line, they only apply to
that line.

You can prevent bugs from silently sneaking into your code by running Pylint in
your [CI/CD pipeline](#continuous-integration) every time you push code to
Gitlab:

```yaml
# .gitlab-ci.yml
test_lint:
  extends: .acc_py_base
  stage: test
  before_script:
    # Pin the version number and only update it manually. This avoids
    # spontaneous failure.
    - python -m pip install pylint==2.8.2 black==21.5b0 isort==5.8.0
    - python -m pip install -e .
  script:
    # Run each linter, but don't abort on error. Only abort at the end
    # if any linter failed. This way, you get all warnings at once.
    - pylint ${project_name} || pylint_exit=$?
    - black --check . || black_exit=$?
    - isort --check . || isort_exit=$?
    - if [[ pylint_exit+black_exit+isort_exit -gt 0 ]]; then false; fi
```

If you write Python code that is used by other people, you might also want to
add [type annotations](https://www.python.org/dev/peps/pep-0483/) and use a
type checker like
[Mypy](https://mypy.readthedocs.io/en/latest/getting_started.html) or
[Pyright](https://github.com/microsoft/pyright/blob/master/docs/getting-started.md).

Further reading:
- [Python static code analysis
  tools](https://pawamoy.github.io/posts/python-static-code-analysis-tools/)
