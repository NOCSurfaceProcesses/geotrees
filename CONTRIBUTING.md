# Contributing

Please contribute your features to this repository. You should ideally do this with a new branch and
ask a user with write permissions to review and merge. If you are a user with write permissions,
please ask another user with write permissions to review and merge.

## Formatting

It is recommended that you use `ruff` to format your code. This will follow the conventions within
the `pyproject.toml` file.

`ruff` can be found at [https://github.com/astral-sh/ruff](https://github.com/astral-sh/ruff)

## Tests

Please write tests for your code, add these to the `test` directory. We use `pytest` to do testing.

## Issues

Please file issues as they arise. Describe the problem, the steps to reproduce, and provide any
output.

# Contributing to `GeoTrees`

If you wish to contribute please make sure you are working on your own branches (not main), ideally
you should work on your own fork. If you wish to work on a particular module you could name your
branch `module-user` where `module` would be replaced by the name of the module you are working on,
and `user` would be your user name. However you can name your branch as you see fit, but it is a
good idea to name it something that relates to what you are working on. If you are working on an
issue please reference the issue number in the branch name and associated Merge request. It is
generally easier to make a merge request and create a branch from the issue.

If you wish to merge to `main` please create a merge request and assign it to `josidd`,
and/or `ricorne` - either to perform the merge and/or review/approve the request. Please provide a
summary of the main changes that you have made so that there is context for us to review the
changes.

## Changelog

The changelog is `CHANGES.md`. Please add your changes to the changelog in your merge request.

## Commit Messages

We are trying to use a consistent and informative approach for writing commit messages in this
repository. We have adopted the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
standard for commit messages. Whilst we won't enforce this standard upon others, we do recommend the
approach. Otherwise please ensure that your messages are descriptive and not just `changes` or
similar.

## Development Instructions

We recommend [uv](https://docs.astral.sh/uv/) for development purposes.

Clone the repository and create your development branch

```bash
git clone git@github.com:NOCSurfaceProcesses/geotrees.git /path/to/geotrees
cd /path/to/geotrees
git checkout -b new-branch-name  # if not a new branch exclude the '-b'
```

Create a virtual environment and install the dependencies

```bash
uv venv --python 3.12  # recommended version >= 3.9 is supported
source .venv/bin/activate  # assuming bash or zsh
```

To install the dependencies run:

```bash
uv sync
```

Or to install all development dependencies and dependencies run:

```bash
uv sync --extra all --dev
```

## Standards

We recommend the use of [ruff](https://docs.astral.sh/ruff/) as a linter/formatter. The
`pyproject.toml` file includes all the settings for `ruff` for `GeoTrees`.

```bash
uvx ruff check
uvx ruff check --fix
uvx ruff format
```

[codespell](https://github.com/codespell-project/codespell) is also used to check spelling/bad
names.

We use [pre-commit](https://pre-commit.com/) as part of out CI/CD processing. I recommend using
pre-commit in your hooks, to avoid the pre-commit stage of the CI/CD failing:

```bash
pip install pre-commit
pre-commit install
```

This will run the pre-commit stage of the CI/CD on each commit - the commit will fail if the CI/CD
fails.

## Tests

If you create new functionality please write and perform unit-tests on your code. The current
implementation of `GeoTrees` uses the `pytest` library.

New tests do not need to be comprehensive, but I likely won't merge if your changes fails testing,
especially the pre-existing tests. You will need to include (and reference) any data that is
needed for testing.

We have a CI/CD pipeline that will automatically implement testing as part of merge requests.

We welcome additions/improvements to the current tests. New python test files should be placed in
the `test` directory and filenames must be prefixed with `test_`.

To perform tests you will need to have the environment set-up and active. Then run:

```
uv run pytest test/test_*.py
```

from the main/top directory for the repository.
