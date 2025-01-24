#!/usr/bin/env bash
set -xeou pipefail

PACKAGEDIR=$PREFIX/Lib
mkdir -p $PACKAGEDIR

PYTHON_VERSION=3.11
PYPI_PLATFORM="win_amd64"

unset PIP_NO_INDEX
unset PIP_NO_DEPENDENCIES

rm -rf dist
hatch build

pip install \
    --target $PACKAGEDIR \
    --platform $PYPI_PLATFORM \
    --python-version $PYTHON_VERSION \
    --ignore-installed \
    --no-deps \
    openjd-adaptor-runtime

# Install these two at the same time otherwise they overwrite eachother
pip install \
    --target $PACKAGEDIR \
    --platform $PYPI_PLATFORM \
    --python-version $PYTHON_VERSION \
    --ignore-installed \
    --only-binary=:all: \
    dist/*.whl deadline

# Copy scripts.
mkdir -p $SCRIPTS
cp $RECIPE_DIR/KeyShotAdaptor.bat $SCRIPTS/KeyShotAdaptor.bat
cp $RECIPE_DIR/keyshot-openjd.bat $SCRIPTS/keyshot-openjd.bat
cp $RECIPE_DIR/keyshot-openjd-script.py $SCRIPTS/keyshot-openjd-script.py

mkdir -p "$PREFIX/etc/conda/activate.d"
mkdir -p "$PREFIX/etc/conda/deactivate.d"
cp $RECIPE_DIR/activate.sh "$PREFIX/etc/conda/activate.d/$PKG_NAME-$PKG_VERSION-vars.sh"
cp $RECIPE_DIR/activate.bat "$PREFIX/etc/conda/activate.d/$PKG_NAME-$PKG_VERSION-vars.bat"
cp $RECIPE_DIR/deactivate.sh "$PREFIX/etc/conda/deactivate.d/$PKG_NAME-$PKG_VERSION-vars.sh"
cp $RECIPE_DIR/deactivate.bat "$PREFIX/etc/conda/deactivate.d/$PKG_NAME-$PKG_VERSION-vars.bat"
