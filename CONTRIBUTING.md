# Contributing

## Style Guide

### Setting up `pre-commit`

This project uses the [`pre-commit`](https://pre-commit.com/) framework to
setup [`git hooks`](https://git-scm.com/book/ms/v2/Customizing-Git-Git-Hooks)
for formatting the source code. All configuration files required to
setup the `git hooks` through `pre-commit` are included in the project.

#### Installing `pre-commit`

Using pip:

```
pip install pre-commit
```

To verify that `pre-commit` is installed and working properly, run:

```
pre-commit --version
```

You should see what version you're using

```
$ pre-commit --version
pre-commit 4.1.0
```

#### Installing the `git hook` scripts

`cd` into the project directory and run:

```
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

You should see the following output:

```
$ pre-commit install --hook-type pre-commit --hook-type commit-msg
pre-commit installed at .git/hooks/pre-commit
pre-commit installed at .git/hooks/commit-msg
```
