============
Contributing
============

Welcome to ``ecmwf_models`` contributor's guide.

This document focuses on getting any potential contributor familiarized
with the development processes, but `other kinds of contributions`_ are also
appreciated.

If you are new to using git_ or have never collaborated in a project previously,
please have a look at `contribution-guide.org`_. Other resources are also
listed in the excellent `guide created by FreeCodeCamp`_ [#contrib1]_.

Please notice, all users and contributors are expected to be **open,
considerate, reasonable, and respectful**. When in doubt, `Python Software
Foundation's Code of Conduct`_ is a good reference in terms of behavior
guidelines.


Issue Reports
=============

If you experience bugs or general issues with ``ecmwf_models``, please have a look
on the `issue tracker`_. If you don't see anything useful there, please feel
free to fire an issue report.

.. tip::
   Please don't forget to include the closed issues in your search.
   Sometimes a solution was already reported, and the problem is considered
   **solved**.

New issue reports should include information about your programming environment
(e.g., operating system, Python version) and steps to reproduce the problem.
Please try also to simplify the reproduction steps to a very minimal example
that still illustrates the problem you are facing. By removing other factors,
you help us to identify the root cause of the issue.


Documentation Improvements
==========================

You can help improve ``ecmwf_models`` docs by making them more readable and coherent, or
by adding missing information and correcting mistakes.

``ecmwf_models`` documentation uses Sphinx_ as its main documentation compiler.
This means that the docs are kept in the same repository as the project code, and
that any documentation update is done in the same way was a code contribution.

We provide docs in reStructuredText_ format.

When working on documentation changes in your local machine, you can
compile them using::

    python setup.py build_sphinx


and use Python's built-in web server for a preview in your web browser
(``http://localhost:8000``)::

    python3 -m http.server --directory 'docs/_build/html'


Code Contributions
==================

The package consists of three modules for each supported dataset.

1) A download module that implements the command line interface to retrieve
data from ECMWF.
2) A image stack reader to extract information for specific locations for specific
variables from `grib` and `netcdf` files.
3) A reshuffle module to transpose the image stacks into a time series format
for subsequent, performant reading.

Submit an issue
---------------

Before you work on any non-trivial code contribution it's best to first create
a report in the `issue tracker`_ to start a discussion on the subject.
This often provides additional considerations and avoids unnecessary work.

Create an environment
---------------------

Before you start coding, we recommend creating an isolated `virtual
environment`_ to avoid any problems with your installed Python packages.
This can easily be done via Miniconda_::

    conda create -n ecmwf_models python=3.12 pygrib netcdf4 pyresample pykdtree
    conda activate ecmwf_models

Clone the repository
--------------------

#. Create an user account on |the repository service| if you do not already have one.
#. Fork the project repository_: click on the *Fork* button near the top of the
   page. This creates a copy of the code under your account on |the repository service|.
#. Clone this copy to your local disk (note use the `--recurive` flag to dowload test data as well::

    git clone --recusive git@github.com:YourLogin/ecmwf_models.git
    cd ecmwf_models

#. You should run::

    pip install -U pip setuptools -e .

   to be able run ``putup --help``.

#. Install |pre-commit|_::

    pip install pre-commit
    pre-commit install

   ``ecmwf_models`` comes with a lot of hooks configured to automatically help the
   developer to check the code being written.

Implement your changes
----------------------

#. Create a branch to hold your changes::

    git checkout -b my-feature

   and start making changes. Never work on the master branch!

#. Start your work on this branch. Don't forget to add docstrings_ to new
   functions, modules and classes, especially if they are part of public APIs.

#. Add yourself to the list of contributors in ``AUTHORS.rst``.

#. When you’re done editing, do::

    git add <MODIFIED FILES>
    git commit

   to record your changes in git_.

   Please make sure to see the validation messages from |pre-commit|_ and fix
   any eventual issues with the code styling. Note that you can use in line
   commands like `# noqa: E722` to exclude lines under certain conditions.

   .. important:: Don't forget to add unit tests and documentation in case your
      contribution adds an additional feature and is not just a bugfix.

      Moreover, writing a `descriptive commit message`_ is highly recommended.
      In case of doubt, you can check the commit history with::

         git log --graph --decorate --pretty=oneline --abbrev-commit --all

      to look for recurring communication patterns.

#. Please check that your changes don't break any unit tests with::

    pytest

    Note: A common mistake that leads to failing tests is missing test data.
    Make sure that you have downloaded available test data into `tests/ecmwf_models-test-data`.

    In case you forgot the `--recusive` flag when cloning the repo, you can run the
    following commands to get the test data::

        git submodule init
        git submodule update


Code styling
------------

To apply pep8 conform styling to any changed files we use yapf.
The correct settings are already set in setup.cfg.
Therefore the following command should be enough::

    yapf file.py --in-place


Afterwards the file should be styled correctly, i.e. the pre-commit hooks should
pass. If there are still issues, they must be fixed manually.


Submit your contribution
------------------------

#. If everything works fine, push your local branch to |the repository service| with::

    git push -u origin my-feature

#. Go to the web page of your fork and click |contribute button|
   to send your changes for review.


Troubleshooting
---------------

The following tips can be used when facing problems to build or test the
package:

#. Make sure to fetch all the tags from the upstream repository_.
   The command ``git describe --abbrev=0 --tags`` should return the version you
   are expecting. If you are trying to run CI scripts in a fork repository,
   make sure to push all the tags.
   You can also try to remove all the egg files or the complete egg folder, i.e.,
   ``.eggs``, as well as the ``*.egg-info`` folders in the ``src`` folder or
   potentially in the root of your project.

Maintainer tasks
================

Releases
--------

If you are part of the group of maintainers you can release a new version of this package.
Make sure all tests are passing on the master branch and the `CHANGELOG.rst` file
is up-to-date, with changes for the new version at the top.

Then draft a new release_ on GitHub. Create a version tag following the
`v{MAJOR}.{MINOR}.{PATCH}` pattern.
This will trigger a new build on GitHub and should push the packages to pypi
after all tests have passed.

If this does not work (tests pass but upload fails) you can download the whl
and dist packages for each workflow run from https://github.com/TUW-GEO/ecmwf_models/actions
(Artifacts) and push them manually to https://pypi.org/project/ecmwf_models/
e.g. using twine (you need to be a package maintainer on pypi for that).


.. [#contrib1] Even though, these resources focus on open source projects and
   communities, the general ideas behind collaborating with other developers
   to collectively create software are general and can be applied to all sorts
   of environments, including private companies and proprietary code bases.


.. |the repository service| replace:: GitHub
.. |contribute button| replace:: "Create pull request"

.. _repository: https://github.com/TUW-GEO/ecmwf_models
.. _release: https://github.com/TUW-GEO/ecmwf_models/releases
.. _issue tracker: https://github.com/TUW-GEO/ecmwf_models/issues


.. |virtualenv| replace:: ``virtualenv``
.. |pre-commit| replace:: ``pre-commit``
.. |tox| replace:: ``tox``


.. _black: https://pypi.org/project/black/
.. _CommonMark: https://commonmark.org/
.. _contribution-guide.org: http://www.contribution-guide.org/
.. _creating a PR: https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request
.. _descriptive commit message: https://chris.beams.io/posts/git-commit
.. _docstrings: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
.. _first-contributions tutorial: https://github.com/firstcontributions/first-contributions
.. _flake8: https://flake8.pycqa.org/en/stable/
.. _git: https://git-scm.com
.. _GitHub's fork and pull request workflow: https://guides.github.com/activities/forking/
.. _guide created by FreeCodeCamp: https://github.com/FreeCodeCamp/how-to-contribute-to-open-source
.. _Miniconda: https://docs.conda.io/en/latest/miniconda.html
.. _MyST: https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html
.. _other kinds of contributions: https://opensource.guide/how-to-contribute
.. _pre-commit: https://pre-commit.com/
.. _PyPI: https://pypi.org/
.. _PyScaffold's contributor's guide: https://pyscaffold.org/en/stable/contributing.html
.. _Pytest can drop you: https://docs.pytest.org/en/stable/usage.html#dropping-to-pdb-python-debugger-at-the-start-of-a-test
.. _Python Software Foundation's Code of Conduct: https://www.python.org/psf/conduct/
.. _reStructuredText: https://www.sphinx-doc.org/en/master/usage/restructuredtext/
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _tox: https://tox.readthedocs.io/en/stable/
.. _virtual environment: https://realpython.com/python-virtual-environments-a-primer/
.. _virtualenv: https://virtualenv.pypa.io/en/stable/

.. _GitHub web interface: https://docs.github.com/en/github/managing-files-in-a-repository/managing-files-on-github/editing-files-in-your-repository
.. _GitHub's code editor: https://docs.github.com/en/github/managing-files-in-a-repository/managing-files-on-github/editing-files-in-your-repository
