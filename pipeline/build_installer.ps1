$ErrorActionPreference = "Stop"

hatch run build
hatch run installer:build-installer @args
