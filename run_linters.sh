#!/bin/bash

# This script runs all relevant linters with the correct arguments. If one of
# them fails, the script continues running the rest. Only at the end does the
# script determine whether it has failed or not.

if [[ "$*" ]]; then
  if [[ "$*" == --print-versions ]]; then
    black --version
    isort --version
    pycodestyle --version
    mypy --version
    pylint --version
  else
    echo "Usage: $0 [--print-versions]"
    exit 1
  fi
fi

exit_code=0

black --check . || exit_code=$((exit_code + $?))
isort --check . || exit_code=$((exit_code + $?))
pycodestyle cernml/ examples/ tests/ || exit_code=$((exit_code + $?))
mypy examples/ tests/ || exit_code=$((exit_code + $?))
mypy -p cernml || exit_code=$((exit_code + $?))
pylint cernml/ || exit_code=$((exit_code + $?))
pylint tests/*.py || exit_code=$((exit_code + $?))

exit $exit_code
