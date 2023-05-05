Packaging Crash Course
======================

This tutorial teaches you briefly how to create a Python package, set up a CI
pipeline and publish it to the `Acc-Py Package Index`_. It uses Acc-Py_ to
simplify the process, but also explains what happens under the hood. For each
topic, hyperlinks to further information are provided.

Each section should be reasonably self-contained. Feel free to skip boring
sections or go directly to the one that answers your question. See also the
`Acc-Py deployment walkthrough`_ for an alternative approach that converts an
unstructured repository of Python code into a deployable Python package.

.. _Acc-Py Package Index:
   https://wikis.cern.ch/display/ACCPY/Python+package+index
.. _Acc-Py: https://wikis.cern.ch/display/ACCPY/
.. _Acc-Py deployment walkthrough:
   https://wikis.cern.ch/display/ACCPY/Deployment+walk-through

Loading Acc-Py
--------------

If you trust your Python environment, feel free to skip this section. This
serves as a baseline from which beginners can start and be confident that none
of the experimentation here will impact their other projects.

Start out by loading Acc-Py. We recommend using the latest Acc-Py Base
distribution (2021.12 at the time of this writing):

.. code-block:: shell-session

    $ source /acc/local/share/python/acc-py/base/pro/setup.sh

If you put this line into your :file:`~/.bash_profile` script [#profile]_, it
will be executed every time you log into your machine. If you don't want this,
but you also don't want to have to remember this long path, consider putting an
alias into your :file:`~/.bash_profile` instead:

.. code-block:: shell-session

    $ alias setup-acc-py='source /acc/local/share/python/acc-py/base/pro/setup.sh'

This way, you can load Acc-Py by invoking :command:`setup-acc-py` on your
command line.

.. note::
   If you want to use Acc-Py outside of the CERN network, the `Acc-Py Package
   Index`_ wiki page has instructions on how to access it from outside. If you
   want to use multiple Python versions on the same machine, you may use a tool
   like Pyenv_, Pyflow_ or Miniconda_.

.. _Pyflow: https://github.com/David-OConnor/pyflow,
.. _Pyenv: https://github.com/pyenv/pyenv or
.. _Miniconda: https://docs.conda.io/en/latest/miniconda.html.

Further reading in the Acc-Py Wiki:

- `Acc-Py Base`__
- `Acc-Py Interactive Eenvironment`__

__ https://wikis.cern.ch/display/ACCPY/Acc-Py+base+distribution
__ https://wikis.cern.ch/display/ACCPY/Interactive+environment

.. [#profile] See `here <https://unix.stackexchange.com/questions/45684/>`_ for
   the difference between :file:`.bash_profile` and :file:`.profile`.

Creating a virtual environment
------------------------------

Virtual environments (or :doc:`venvs <std:library/venv>` for short) separate
dependencies of one project from another. This way, you can work on one project
that uses PyTorch 1.x, switch your venv, then work on another project that
uses PyTorch 2.x.

Venvs also allow you to install dependencies that are not available in the
Acc-Py distribution. This approach is much more robust than installing them
into your home directory via :command:`pip install --user`. The latter often
leads to hard-to-understand import errors, so it is discouraged.

If you're working on your `BE-CSS VPC`_, we recommend creating your venv in the
:file:`/opt` directory, since space in your home directory is limited.
Obviously, this does not work on LXPLUS_, where your home directory is the only
choice.

.. _BE-CSS VPC:
   https://wikis.cern.ch/display/ACCADM/VPC+Virtual+Machines+BE-CSS
.. _LXPLUS: https://lxplusdoc.web.cern.ch/

.. code-block:: shell-session

    $ # Create a directory for all your venvs.
    $ sudo mkdir -p /opt/home/$USER/venvs
    $ # Make it your own (instead of root's).
    $ sudo chown "$USER:" /opt/home/$USER/venvs
    $ acc-py venv /opt/home/$USER/venvs/coi-example

.. note::
   The :command:`acc-py venv` command is a convenience wrapper around the
   :mod:`std:venv` standard library module. In particular, it passes the
   ``--system-site-packages`` flag. This flag ensures that everything that is
   preinstalled in the Acc-Py distribution also is available in your new
   environment. Without it, you would have to install common dependencies such
   as :doc:`NumPy <np:index>`.

Once the virtual environment is created, you can activate it like this:

.. code-block:: shell-session

    $ source /opt/home/$USER/venvs/coi-example/bin/activate
    $ which python  # Where does our Python interpreter come from?
    /opt/home/.../venvs/coi-example/bin/python
    $ # deactivate  # Leave the venv again.

After activating the environment, you can give it a test run by upgrading the
Pip package manager. This change should be visible only within your virtual
environment:

.. code-block:: shell-session

    $ pip install --upgrade pip

Further reading in the Acc-Py Wiki:

- `Getting started with Acc-Py`__
- `Acc-Py Development advice`__

__ https://wikis.cern.ch/display/ACCPY/Getting+started+with+Acc-Py
__ https://wikis.cern.ch/display/ACCPY/Development+advice

Setting up the Project
----------------------

Time to get started! Go into your projects folder and initialize a project
using Acc-Py:

.. code-block:: shell-session

    $ cd ~/Projects
    $ acc-py init coi-example
    $ cd ./coi-example

.. note::
   Don't forget to hit the tab key while typing the above lines, so that your
   shell will auto-complete the words for you!

The :command:`acc-py init` command creates a basic project structure for you.
You can inspect the results via the :command:`tree` `command <tree_>`_:

.. _tree: http://mama.indstate.edu/users/ice/tree/

.. code-block:: shell-session

    $ tree
    .
    ├── coi_example
    │   ├── __init__.py
    │   └── tests
    │       ├── __init__.py
    │       └── test_coi_example.py
    ├── README.md
    └── setup.py

This is usually enough to get started. However, there are two useful files that
Acc-Py does not create for us: :file:`.gitignore` and :file:`pyproject.toml`.
If you're not in a hurry, we suggest you create them now. Otherwise, continue
with :ref:`Adding Dependencies`.

Further reading in the Acc-Py wiki:

- `Starting a new Python project`__
- `Project Layout`__
- `Creating a Python package from a directory of scripts`__

__ https://wikis.cern.ch/display/ACCPY/Getting+started+with+Acc-Py#GettingstartedwithAcc-Py-StartinganewPythonproject
__ https://wikis.cern.ch/display/ACCPY/Project+layout
__ https://wikis.cern.ch/display/ACCPY/Creating+a+Python+package+from+a+directory+of+scripts

Adding :file:`.gitignore` (Optional)
------------------------------------

The :file:`.gitignore` file tells Git which files to ignore. Ignored files will
never show up as untracked or modified if you run :command:`git status`. This
is ideal for caches, temporary files and build artifacts. Without
:file:`.gitignore`, :command:`git status` would quickly become completely
useless.

While you can create this file yourself, we recommend you download
Python.gitignore_; it is comprehensive and universally used. 

.. _Python.gitignore:
   https://github.com/github/gitignore/blob/master/Python.gitignore

.. warning::
   After downloading the file and putting it inside your project folder, don't
   forget to *rename* it to :file:`.gitignore`!

It is very common to later add project-specific names of temporary and
`glob patterns`_ to this list. Do not hesitate to edit it! It only serves as a
starting point.

.. _glob patterns: https://en.wikipedia.org/wiki/Glob_(programming)

.. note::
   If you use an IDE like `PyCharm`_, it is very common that IDE-specific
   config and manifest files will end up in your project directory. You *could*
   manually add these files to the :file:`.gitignore` file of every single
   project. However, there's an easier way.

   Instead, you can add these file names to a `global gitignore
   <git-excludelist_>`_ file that is specific to your machine (and not your
   project).

.. _PyCharm: https://www.jetbrains.com/pycharm/
.. _git-excludelist:
   https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration#_core_excludesfile

Further reading:

- `A collection of useful .gitignore templates`__ on GitHub.com
- `Ignoring Files`__ in the Git Book
- `Gitignore reference`__

__ https://github.com/github/gitignore/
__ https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository#_ignoring
__ https://git-scm.com/docs/git-check-ignore

Adding :file:`pyproject.toml` (Optional)
----------------------------------------

`Setuptools`_ is still the most common tool used to build and install Python
packages. Traditionally, it expects project data (name, version,
dependencies, …) to be declared in a :file:`setup.py` file.

Many people don't like this approach. Executing arbitrary Python code is a
security risk and it's hard to accommodate alternative, more modern build
tools such as Poetry_, Flit_ or Meson_. For this reason, the Python community
has been slowly moving towards a more neutral format.

.. _Setuptools: https://setuptools.readthedocs.io/
.. _Poetry: https://python-poetry.org/docs/pyproject/#poetry-and-pep-517
.. _Flit: https://flit.pypa.io/en/latest/
.. _Meson: https://thiblahute.gitlab.io/mesonpep517/pyproject.html

This format is the :file:`pyproject.toml` file. It allows a project to declare
the build system that it uses and can be read without executing untrusted
Python code.

In addition, many Python tools (e.g. `Black
<black-toml_>`_, `Isort <isort-toml_>`_, `Pylint <pylint-toml_>`_, `Pytest
<pytest-toml_>`_, `Setuptools-SCM <setuptools-scm-toml_>`_) can be configured
in this file. This reduces clutter in your project directory and makes it
possible to do all configuration using a single file format.

.. _Black-TOML:
   https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html#what-on-earth-is-a-pyproject-toml-file
.. _Isort-TOML: 
   https://pycqa.github.io/isort/docs/configuration/config_files.html#pyprojecttoml-preferred-format
.. _Pylint-TOML:
   https://pylint.pycqa.org/en/latest/user_guide/usage/run.html#command-line-options
.. _Pytest-TOML:
   https://docs.pytest.org/en/latest/reference/customize.html#pyproject-toml
.. _Setuptools-SCM-TOML:
   https://github.com/pypa/setuptools_scm#pyprojecttoml-usage

If you wonder what a TOML_ file is, it is a config file format like YAML or
INI, but with a focus on clarity and simplicity.

.. _TOML: https://toml.io/en/

This is what a minimal :file:`pyproject.toml` file using Setuptools looks like:

.. code-block:: toml

    # pyproject.toml
    [build-system]
    requires = ['setuptools', 'wheel']
    build-backend = 'setuptools.build_meta'

The section ``build-system`` tells Pip how to install our package. The key
``requires`` gives a list of necessary Python packages. The key
``build-backend`` points at a Python function that Pip calls to handle the
rest. Between all of your Python projects, this section will almost never
change.

And this is a slightly more complex :file:`pyproject.toml`, that also
configures a few tools. Note that the file would be only about 20 lines long:

.. code-block:: toml

    # We can require minimum versions and [extras]!
    [build-system]
    requires = [
        'setuptools >= 42',
        'setuptools-scm[toml] ~= 5.0',
        'wheel',
    ]
    build-backend = 'setuptools.build_meta'

    # Tell isort to be compatible with the Black formatting style.
    # This is necessary if you use both tools.
    [tool.isort]
    profile = 'black'

    # Note that there is no section for Black itself. Normally,
    # we don't need to configure a tool just to use it!

    # Setuptools-SCM, however, is a bit quirky. The *presence*
    # of its config block is required to activate it.
    [tool.setuptools_scm]

    # PyTest takes its options in a nested table
    # called `.ini_options`. Here, we tell it to also run
    # doctests, not just unit tests.
    [tool.pytest.ini_options]
    addopts = '--doctest-modules'

    # Pylint splits its configuration across multiple tables.
    # Here, we disable one warning and minimize their report
    # size.
    [tool.pylint.reports]
    reports = false
    score = false

    # Note how we quote 'messages control' because it contains
    # a space character.
    [tool.pylint.'messages control']
    disable = ['similarities']

Further reading:

- `What the heck is pyproject.toml?`__
- `PEP 518 introducting pyproject.toml`__
- `Awesome Pyproject.toml`__

__ https://snarky.ca/what-the-heck-is-pyproject-toml/
__ https://www.python.org/dev/peps/pep-0518/
__ https://github.com/carlosperate/awesome-pyproject

Adding dependencies
-------------------

Once this is done, we can edit the :file:`setup.py` file created for us and
fill in the blanks. This is what the new requirements look like:

.. code-block:: python

    # setup.py
    REQUIREMENTS: dict = {
        "core": [
            "cernml.coi ~= 0.8.0",
            "gym >= 0.21",
            "matplotlib ~= 3.0",
            "numpy ~= 1.0",
            "pyjapc ~= 2.0",
        ],
        "test": [
            "pytest",
        ],
    }

And this is the new ``setup()`` call:

.. code-block:: python

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
        python_requires=">=3.7, <4",
        classifiers=[
            "Programming Language :: Python :: 3",
            "Intended Audience :: Science/Research",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "Topic :: Scientific/Engineering :: Physics",
        ],
        # Rest as before …
    )

Of all these changes, only the *description* and the *requirements* were really
necessary. Things like classifiers are nice-to-have metadata that we could
technically also live without.

Further reading:

- `Packaging of your module`__ in the Acc-Py Wiki
- `Setuptools Quickstart`__
- `Dependency management in Setuptools`__
- `Setuptools keywords`__

__ https://wikis.cern.ch/display/ACCPY/Development+Guidelines#DevelopmentGuidelines-Packagingofyourmodule
__ https://setuptools.readthedocs.io/en/latest/userguide/quickstart.html
__ https://setuptools.readthedocs.io/en/latest/userguide/dependency_management.html
__ https://setuptools.readthedocs.io/en/latest/references/keywords.html

Version Requirements (Digression)
---------------------------------

.. note::
   This section is purely informative. If it bores you, feel free to skip ahead
   to :ref:`Interlude: Test Run`.

When specifying your requirements, you should make sure to put in a
*reasonable* version range for two simple reasons:

- Being **too lax** with your requirements means that a package that you use
  might change something and your code suddenly breaks without warning.
- Being **too strict** with your requirements means that other people will have
  a hard time making your package work in conjunction with theirs, even though
  all the code is correct.

There are two common ways to specify version ranges:

- ``~= 0.4.2`` means: “I am compatible with version :samp:`0.4.2` and higher,
  but **not** with any version :samp:`0.5.{X}`.” This is a good choice if the
  target adheres to `Semantic Versioning`_. (Not all packages do! NumPy
  doesn't, for example!)
- ``>=1.23, <1.49`` means: “I am compatible with version ``1.23`` and higher,
  but not with version ``1.49`` and beyond.” This is a reasonable choice if you
  know a version of the target that works for you and a version that doesn't.

.. _Semantic Versioning: https://semver.org/

:pep:`Other version specifiers <440#version-specifiers>` mainly exist for
strange edge cases. Only use them if you know what you're doing.

Further reading:

- `Dependency and release management`__ in the Acc-Py Wiki

__ https://wikis.cern.ch/display/ACCPY/Dependency+and+release+management

Interlude: Test Run
-------------------

With this minimum in place, your package already can be installed via Pip! Give
it a try:

.. code-block:: shell-session

    $ pip install .  # "." means "the current directory".

Once this is done, your package is installed in your venv and can be imported
by other packages *without* any path hackery:

.. code-block:: python

    >>> import coi_example
    >>> coi_example.__version__
    '0.0.1'
    >>> import pkg_resources
    >>> pkg_resources.get_distribution('coi-example')
    coi-example 0.0.1.dev0 (/opt/home/.../venvs/coi-example/lib/python3.9/site-packages)

Of course, you can always remove your package again:

.. code-block:: shell-session

    $ pip uninstall coi-example

.. warning::
   Installation puts a **copy** of your package into your venv. This means that
   every time you change the code, you have to reinstall it for the changes to
   become visible.

There is also the option to sym-link from your venv to your source directory.
In this case, all changes to the source code become visible *immediately*. This
is bad for a production release, but extremely useful during development. This
feature is called an *editable install*:

.. code-block:: shell-session

    $ pip install --editable .  # or `-e .` for short

Further reading:

- `When would the -e, --editable option be useful with pip install?`__

__ https://stackoverflow.com/questions/35064426

SDists and Wheels (Digression)
------------------------------

.. note::
   This section is purely informative. If it bores you, feel free to skip ahead
   to :ref:`Continuous Integration`.

The act of bringing Python code into a publishable format has a lot of
historical baggage. This section skips most of the history and explains the
terms that are most relevant today.

Python is an interpreted language. As such, one *could* think that there is no
compilation step, and that the source code of a program is enough in order to
run it. However, this assumption is wrong for a number of reasons:

- :doc:`some libraries <np:index>` contain extension code written in C or
  FORTRAN that must be compiled before using them;
- `some libraries <PyTZ_>`_ generate their own Python code during installation;
- *all* libraries must provide :pep:`their metadata <345>` in a certain,
  standardized format.

.. _PyTZ: https://launchpad.net/pytz

As such, even Python packages must be built to some extent before publication.

The publishable result of the build process is a :term:`pkg:distribution package`
(confusingly often called *distribution* or *package* for short). There are
several historical kinds of distribution packages, but only two remain relevant
today: sdists and wheels.

:term:`Sdists <pkg:Source Distribution (or "sdist")>` contain only the above
mentioned metadata and all relevant source files. It does not contain project
files that are not packaged by the author (e.g. :file:`.gitignore` or
:file:`pyproject.toml`). Because it contains source code, any C extensions must
be compiled during installation. For this reason, installation is a bit slower
and may run arbitrary code.

:term:`Wheels <pkg:Wheel>` are a binary distribution format. Under the hood,
they are zip files with a certain directory layout and file name. They come
fully built and any C extensions are already compiled. This makes them faster
and safer to install than sdists. The disadvantage is that *if* your project
contains C extensions, you have to provide one wheel for each supported
platform.

Given that most projects will be written purely in Python, wheels are the
preferred distribution format. Depending on circumstances, it may make sense to
publish an sdist in addition. The way to manually create and upload a
distribution to the package repository is `described elsewhere <Acc-Py package
upload_>`_. See :ref:`Releasing a Package via CI` for the preferred and
supported method at CERN.

.. _Acc-Py package upload:
   https://wikis.cern.ch/display/ACCPY/Development+Guidelines#DevelopmentGuidelines-CreationandUploadofyourpackage

Further reading:

- `What are Python wheels and why should you care?`__
- `Building wheels for Python packages`__ on the Acc-Py Wiki
- :doc:`Python packaging user guides <pkg:guides/index>`
- `Twisted history of Python packaging`__ (2012)

__ https://realpython.com/python-wheels/
__ https://wikis.cern.ch/display/ACCPY/Building+wheels+for+Python+packages
__ https://www.youtube.com/watch?v=lpBaZKSODFA (2012)

Continuous Integration
----------------------

`Continuous integration`_ is a software development strategy that prefers to
merge features into a project's main branch frequently to prevent code
divergence. To facilitate this, websites like Gitlab offer `CI pipelines`_ that
build and test code on each push *automatically*.

.. _Continuous integration:
   https://en.wikipedia.org/wiki/Continuous_integration
.. _CI pipelines: https://gitlab.cern.ch/help/ci/quick_start/index.md

`Continuous delivery`_ takes the practice a step further and also automates the
release of software using the same pipeline. Nowadays, when people talk about
“CI/CD”, they usually refer to having an automated pipeline of tests and
releases.

.. _Continuous delivery: https://en.wikipedia.org/wiki/Continuous_delivery

Why do we care about all of this? Because Gitlab's CI/CD pipeline is the *only*
supported way to put our Python package on the `Acc-Py package index`_.

The Gitlab CI/CD pipeline is configured through a file called
:file:`.gitlab-ci.yml` at the root of your project. Run the command
:command:`acc-py init-ci` to have an automatically generated version of this
file added to your project. It should look somewhat like this:

.. code-block:: yaml

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

The first block (``include``) textually includes a lot of `pre-defined job
templates from Acc-Py <Acc-Py CI templates_>`_. These templates tell Gitlab how
to test or publish a Python package, so you don't have to. You can recognize
these templates by `having a period in front of their name <hidden jobs_>`_
(``.``).

.. _Acc-Py CI templates:
   https://gitlab.cern.ch/acc-co/devops/python/acc-py-devtools/tree/master/acc_py_devtools/templates/gitlab-ci
.. _hidden jobs: https://gitlab.cern.ch/help/ci/jobs/index.md#hide-jobs

The next block (``variables``) defines Acc-Py-specific variables that configure
the job templates we just included. They tell Acc-Py which directory contains
your Python code and which Python version should be used for testing.

Each subsequent block defines a **job** that is run on the Gitlab servers. Each
job has a **trigger** (on each commit, on each Git tag, manually, etc.) and a
**stage** (build → test → deploy). Whenever a trigger fires, all relevant jobs
are collected into a pipeline and run, one stage after the other.

The jobs in our file don't actually define all of this – they simply reuse the
values already set in their respective job template via the ``extends``
keyword. See `here <dev test_>`_ for an example.

Further reading:

- `Get started with GitLab CI/CD`__
- `Keyword reference for the .gitlab-ci.yml file`__

__ https://gitlab.cern.ch/help/ci/quick_start/index.md
__ https://gitlab.cern.ch/help/ci/yaml/index.md

Testing Your Package
--------------------

As you might have noticed, the :command:`acc-py init` call created a subpackage
of your package called “tests”. As a dynamically typed language, Python cannot
rely on compiler type safety to ensure the correctness of your code; unit tests
will have to carry the weight of making sure our code does what we think it
does.

Acc-Py initializes your :file:`.gitlab-ci.yml` file with two jobs for testing:

- a `dev test`_ that runs the tests directly in your source directory,
- an `install test`_ that installs your package and runs the tests in the
  installed copy. This is particularly important, as it ensures that your
  package will work not just for you, but also for your users.

.. _dev test:
   https://gitlab.cern.ch/acc-co/devops/python/acc-py-devtools/-/blob/master/acc_py_devtools/templates/gitlab-ci/dev_testing.yml
.. _install test:
   https://gitlab.cern.ch/acc-co/devops/python/acc-py-devtools/-/blob/master/acc_py_devtools/templates/gitlab-ci/install_test.yml

Both use the same program, Pytest_, to discover and run your unit tests. Click
their respective links to find the exact invocations.

.. _Pytest: https://pytest.org/

The way that Pytest finds your unit tests is simple: It searches for files that
match the pattern :file:`test_*.py` and, inside, searches for functions that
match ``test_*`` and classes that match ``Test*``. All found methods and
functions are run. If they finish without raising an exception, they are
assumed successful, otherwise they have failed.

If you have any non-trivial logic in your code – anything that goes beyond
reading, and setting parameters – it is *highly recommended* to put them into
separate functions. These functions should only depend on their parameters (and
*no global state*). This makes it *much* easier to write tests for them to
ensure that they work as expected – and most importantly, that future changes
won't silently break them!

If you're writing a COI optimization problem that does not depend on JAPC or
LSA, there is one easy test case you can always add: run the COI checker with
your class to catch some common pitfalls:

.. code-block:: python

    # coi_example/tests/test_coi_example.py
    from cernml import coi

    def test_checker():
        env = coi.make("YourEnv-v0")
        coi.check(env, warn=True, headless=True)

If your program is in a very strange niche where it is impossible to test it
reliably, you can also remove the testing code: remove the “tests” package, and
delete the two test jobs from your :file:`.gitlab-ci.yml` file.

Further reading:

- :mod:`std:unittest.mock` standard library module
- :mod:`std:doctest`  standard library module
- `Tests as part of application code`__ on the Acc-Py Wiki
- `GUI testing`__ on the Acc-Py Wiki
- `PAPC – a pure Python PyJapc offline simulator`__ on the Acc-Py Wiki
- `Example CI setup to test projects that rely on Java`__

__ https://docs.pytest.org/en/latest/explanation/goodpractices.html#tests-as-part-of-application-code
__ https://wikis.cern.ch/display/ACCPY/GUI+Testing
__ https://wikis.cern.ch/display/ACCPY/papc+-+a+pure+Python+PyJapc+offline+simulator
__ https://gitlab.cern.ch/scripting-tools/pyjapc/-/blob/master/.gitlab-ci.yml

Releasing a Package via CI
--------------------------

Once CI has been set up and tests have been written (or disabled), your package
is ready for publication! Outside of CERN, Twine_ is the command of choice to
upload a package to PyPI_, but Acc-Py already does this job for us.

.. _Twine: https://twine.readthedocs.io/en/latest/
.. _PyPI: https://pypi.org/

.. warning::
   Publishing a package is **permanent**! Once your code has been uploaded to
   the index, you *cannot* remove it again. And once a project name has been
   claimed, it usually cannot be transferred to another project. Be doubly and
   triply sure that everything is correct before following the next steps!

If your project is not in a Git repository yet, this is the time to check it
in:

.. code-block:: shell-session

    $ git init
    $ git add --all
    $ git commit --message="Initial commit."
    $ git remote add origin ...  # The clone URL of your Gitlab repo
    $ git push --set-upstream origin master

Then, all that is necessary to publish the next (or first) version of your
package is to create a `Git tag`_ and upload it to Gitlab.

.. _Git tag: https://git-scm.com/book/en/v2/Git-Basics-Tagging

.. code-block:: shell-session

    $ # The tag name doesn't actually matter,
    $ # but let's stay consistent.
    $ git tag v0.0.1.dev0
    $ git push --tags

This will trigger a CI pipeline that builds, tests and eventually `releases
<upload on tag_>`_ your code. Once this pipeline has finished successfully
(which includes running your tests), your package is published and immediately
available anywhere inside CERN:

.. _upload on tag:
   https://gitlab.cern.ch/acc-co/devops/python/acc-py-devtools/-/blob/master/acc_py_devtools/templates/gitlab-ci/upload_on_tag.yml

.. code-block:: shell-session

    $ cd ~
    $ pip install coi-example

.. warning::
   The **version of your package** is determined by :file:`setup.py`, *not* by
   the **tag name** you choose! If you tag another commit but don't update the
   version number, and you push this tag, your pipeline will kick off, run
   through to the deploy stage and then fail due to the version conflict.

Further reading:

- `Python package index <Acc-Py Package Index_>`_ on the Acc-Py Wiki

Extra Credit: :file:`setup.cfg`
-------------------------------

.. note::
   You are done! This section, and the ones after, only give a little bit more
   background information on Python packaging, but they are not necessary for
   you to get off the ground. Especially if you're a beginner, feel free to
   stop here and maybe return later.

While :file:`setup.py` is nice and generally gets the work done, there are
several problems with it:

- The logic before the bare ``setup()`` call quickly becomes hard to read.
- It is impossible to extract project metadata without executing arbitrary
  Python code. Security-minded people generally don't like that.
- Most projects don't *need* to execute arbitrary Python code to declare their
  metadata.

For this reason, Setuptools recommends to configure your project using a new
file called :file:`setup.cfg`. It fulfills the same role as :file:`setup.py`,
but as a configuration file, it can be read without executing Python code.
Certain patterns that require Python login in :file:`setup.py` can be handled
via special value types.

For example, this setup script:

.. code-block:: python

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

does the same as this configuration file:

.. code-block:: cfg

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

If you manage to put all your data into :file:`setup.cfg`, your
:file:`setup.py` file can become as simple as:

.. code-block:: python

    # setup.py
    from setuptools import setup
    setup()

If you use setuptools version 40.9 or later (which should be specified :ref:`in
your pyproject.toml file <adding :file:\`pyproject.toml\` (optional)>`), you
can completely remove the :file:`setup.py` file in this case.

Further reading:

- `What's the difference between setup.py and setup.cfg in python projects`__
- :doc:`Setuptools quickstart <setuptools:userguide/quickstart>`
- :doc:`setuptools:userguide/declarative_config`
- :doc:`Setuptools keywords <setuptools:references/keywords>`

__ https://stackoverflow.com/questions/39484863/

Extra Credit: Single-Sourcing Your Version Number
-------------------------------------------------

Over time, it may become annoying to manually bump your version number every
time you release a new version of your package. On top of that, Acc-Py
:ref:`requires us to use Git tags to publish our package <Releasing a Package
via CI>`, but doesn't actually read the name of the tag! It would be nice if we
could co-opt the tag name to automatically denote the version number.

`Setuptools-SCM`_ is a plugin for Setuptools that does precisely that. It
generates your version number automatically based on your Git tags and feeds it
directly into Setuptools. The minimal setup looks as follows:

.. _Setuptools-SCM: https://github.com/pypa/setuptools_scm

.. code-block:: toml

    # pyproject.toml
    [build-system]
    requires = [
        'setuptools>=45',
        'wheel',
        'setuptools_scm[toml]>=6.2',
    ]

    # Add an empty tool section to enable version inference.
    [tool.setuptools_scm]

.. code-block:: cfg

    # setup.cfg
    [metadata]
    name = my_package
    # No version declaration at all!
    # version = automatically generated
    ...

You can also add a key ``write_to`` to your :file:`pyproject.toml` to
automatically generate – *during installation!* – a source file in your package
that contains the version number. This way, your package can expose its version
in a ``__version__`` variable:

.. code-block:: toml

    # pyproject.toml
    [tool.setuptools_scm]
    write_to = 'my_package/version.py'

.. code-block:: python

    # my_package/__init__.py
    from .version import version as __version__
    ...

.. warning::
   Adding a ``__version__`` variable to your package is :pep:`deprecated
   <396#pep-rejection>`! You should not do this in packages. A much more
   reliable way to fetch a package's version is through the
   :mod:`std:importlib.metadata` standard library package (Python 3.8+) or its
   :doc:`backport <importlib_metadata:index>` (Python 3.6+).

Here are some solutions that people come up with that are broken for various
reasons. *Don't* follow these!

1. Importing your own package in :file:`setup.py` and passing
   :samp:`{my_package}.__version__` to ``setup()``. This breaks as
   soon as your package imports any of its dependencies, simply because
   Pip hasn't had *a chance* to install your dependencies yet.
2. Specify :samp:`version = attr: {my_package}.__version__` in
   :file:`setup.cfg`: On setuptools before version 46.4, this does the same as
   the first option – and so has the same problems.
3. Specify :samp:`version = attr: {my_package}.__version__` in
   :file:`setup.cfg` *and* require ``setuptools>=46.4`` in
   :file:`pyproject.toml`: New versions of setuptools textually analyze your
   code and try to find ``__version__`` without running it. If this fails,
   however, setuptools will fall back to importing your package and break
   again.

Further reading:

- :doc:`pkg:guides/single-sourcing-package-version`
- `Zest.releaser <https://zestreleaser.readthedocs.io/en/latest/>`_

Extra Credit: Automatic Code Formatting
---------------------------------------

Although a lot of programmers have needlessly strong opinions on it, good code
formatting has two undeniable advantages:

- it makes it easier to spot typos and related bugs;
- it makes it easier for other people to read your code – if they're familiar
  with the formatting style.

At the same time, it requires a lot of pointless effort to pick, follow and
enforce a particular style guide. Ideally, code formatting would be consistent,
automatic and require as little human input as possible.

:doc:`Black <black:index>` does all of these:

- It is an *automatic* formatter. That means you can write your code however
  messy as you want. You simply let it run over your code base and it edits
  your files in place to be uniformly formatted.
- :doc:`Most IDEs support it <black:integrations/editors>`. This means you can
  configure your IDE such that it runs Black automatically on every save or Git
  commit. With this, you will stop thinking about formatting (almost) entirely.
- It is almost unconfigurable. This obviates pointless style discussions as
  they are known in the C++ world.

.. _Black: https://github.com/psf/black
.. _Black editor integration:
   https://black.readthedocs.io/en/stable/editor_integration.html

On top of it, you may also want to run ISort_ to sort your import statements
for you. To make it compatible with Black, add these lines to your
configuration:

.. _ISort: https://pycqa.github.io/isort/

.. code-block:: python

    # pyproject.toml
    [tool.isort]
    profile = "black"

Further reading:

- :doc:`black:the_black_code_style/current_style`

Extra Credit: Linting
---------------------

As an interpreted and dynamically typed language, Python cannot rely on a
type-checking compiler to verify that your code does what you expect it to do.
Instead, Python developers must rely on *linters*, i.e. static-analysis tools,
to find bugs and anti-patterns.

The simplest choice for beginners Pylint_. It is a general-purpose linter that
catches style and complexity issues as well as outright bugs. In contrast to
Black, Pylint is extremely configurable and encourages users to enable or
disable lints as necessary. Here is an example configuration:

.. _Pylint:
   http://pylint.pycqa.org/

.. code-block:: python

    # pyproject.toml
    [tool.pylint.format]
    max-line-length=88  # Compatibility with Black.
    ignore-long-lines = '<?https?://\S+>?$'  # Ignore long URLs.

    [tool.pylint.reports]
    # Don't show a summary, just print the errors, one per line.
    reports = false
    score = false

    [tool.pylint.'messages control']
    disable = [
        'bad-continuation',
    ]

Sometimes, Pylint gives you a warning that you find generally useful, but
shouldn't apply to an individual piece of code. In this case you can add a
comment like this to suppress the warning:

.. code-block:: python

    # pylint: disable = unused-import

These comments respect scoping. If you put them within a function, they apply
to only that function. If you put them at the end of a line, they only apply to
that line.

You can prevent bugs from silently sneaking into your code by running Pylint in
your :ref:`CI/CD pipeline <continuous integration>` every time you push code to
Gitlab:

.. code-block:: yaml

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

If you write Python code that is used by other people, you might also want to
add :pep:`type annotations <483>` and use a type checker like Mypy_ or
PyRight_.

.. _MyPy: https://mypy.readthedocs.io/en/latest/getting_started.html
.. _PyRight:
   https://github.com/microsoft/pyright/blob/master/docs/getting-started.md

Further reading:

- `Python static code analysis tools`__

__ https://pawamoy.github.io/posts/python-static-code-analysis-tools/
