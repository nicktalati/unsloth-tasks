#!/bin/bash
set -ex
VERSION=$(cat .python-version)
pyenv install -s "$VERSION"
pyenv local "$VERSION"
python -m venv venv && source venv/bin/activate && pip install -e ".[dev]"
set +ex
