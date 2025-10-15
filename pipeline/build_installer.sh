#!/bin/sh
# Set the -e option
set -e

hatch run build
hatch run installer:build-installer $@
