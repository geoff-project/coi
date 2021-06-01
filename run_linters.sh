#!/bin/bash

# This script runs all relevant linters with the correct arguments. If one of
# them fails, the script continues running the rest. Only at the end does the
# script determine whether it has failed or not.

exit_code=0

pylint --version
pylint cernml/ || exit_code=$((exit_code + $?))
pylint tests/*.py || exit_code=$((exit_code + $?))
black --version
black --check . || exit_code=$((exit_code + $?))
isort --version
isort --check . || exit_code=$((exit_code + $?))
pycodestyle --version
pycodestyle . || exit_code=$((exit_code + $?))
mypy --version
mypy -p cernml || exit_code=$((exit_code + $?))
mypy examples/ tests/ || exit_code=$((exit_code + $?))

exit $exit_code
