#!/bin/sh
# Set the -e option
set -e

pip install --upgrade pip
pip install --upgrade hatch
hatch -v run lint
hatch run test
hatch -v build
