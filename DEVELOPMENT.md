# Development documentation

This documentation provides guidance on developer workflows for working with the code in this repository.

Table of Contents:

* [Software Architecture](#software-architecture)
* [Development Environment Setup](#development-environment-setup)
* [The Development Loop](#the-development-loop)
   * [Submitter Development Workflow](#submitter-development-workflow)
      * [Running the Plug-In](#running-the-plug-in)
      * [Making Code Changes](#making-submitter-code-changes)
      * [Running Tests](#running-submitter-tests)

## Software Architecture

If you are not already familiar with the architecture of the KeyShot submitter plugin and adaptor application in this repository
then we suggest going over the [src/README.md](src/README.md) for an overview of the components and how they function.

This package has two active branches:

- `mainline` -- For active development. This branch is not intended to be consumed by other packages. Any commit to this branch may break APIs, dependencies, and so on, and thus break any consumer without notice.
- `release` -- The official release of the package intended for consumers. Any breaking releases will be accompanied with an increase to this package's interface version.

## Development Environment Setup

To develop the Python code in this repository you will need:

1. Python 3.11 or higher. We recommend [mise](https://github.com/jdx/mise) if you would like to run more than one version
   of Python on the same system. When running unit tests against all supported Python versions, for instance.
2. The [hatch](https://github.com/pypa/hatch) package installed (`pip install --upgrade hatch`) into your Python environment.
3. An install of a supported version of Keyshot.
4. A valid AWS Account.
5. An AWS Deadline Cloud Farm to run jobs on with a fleet that has KeyShot Studio installed and licensed.

Development on a Windows or Mac workstation is supported. Linux development support is experimental.

## The Development Loop

We have configured [hatch](https://github.com/pypa/hatch) commands to support a standard development loop. You can run the following
from any directory of this repository:

* `hatch run build` - To build the submitter into `dist`
* `hatch run test` - To run the PyTest unit tests found in the `test/unit` directory. See [Testing](#testing).
* `hatch run all:test` - To run the PyTest unit tests against all available supported versions of Python.
* `hatch run fmt` - To automatically reformat all code to adhere to our formatting standards.
* `hatch run lint` - To check that the package's formatting adheres to our standards.
* `hatch shell` - Enter a shell environment that will have Python set up to import your development version of this package.
* `hatch env prune` - Delete all of your isolated workspace [environments](https://hatch.pypa.io/1.12/environment/)
   for this package.

Note: Hatch uses [environments](https://hatch.pypa.io/1.12/environment/) to isolate the Python development workspace
for this package from your system or virtual environment Python. If your build/test run is not making sense, then
sometimes pruning (`hatch env prune`) all of these environments for the package can fix the issue.

### Development Workflow

The submitter plug-in generates job bundles to submit to AWS Deadline Cloud. Developing a change
to the submitter involves iteratively changing the plug-in code, then running the plug-in within KeyShot
to generate or submit a job bundle, inspecting the generated job bundle to ensure that it is as you expect,
and ultimately running that job to ensure that it works as desired.

#### Running the Plug-In

The KeyShot submitter for Deadline Cloud is a single file `Submit to AWS Deadline Cloud.py`. To run in KeyShot, this file needs to be in the KeyShot scripts folder, which is usually:
- Windows (choose one):
    - User scripts folder e.g. `%USERPROFILE%/Documents/KeyShot/Scripts`
    - System-wide scripts folder e.g. `%PROGRAMFILES%/KeyShot/Scripts`
- Mac: `/Library/Application Support/KeyShot12/` or `/Library/Application Support/KeyShot/` depending on your version of Keyshot.
    - You can navigate to the folder by going to Finder, clicking the menu for Go -> Go to Folder, and typing in the folder path.

#### Making Code Changes

The submitter is built from multiple source files using the `build.py` script. To make changes:

1. **Configure KeyShot Python settings**: Deactivate KeyShot's "Use local Python paths" setting to prevent accidentally using Python libraries that KeyShot doesn't include. Open KeyShot's preferences, click **General**, then unselect the **Use local Python paths** option.

2. Modify the source files in `src/` (submitter.py, session_manager.py, keyshot_bridge.py, etc.)
3. Run the build script to generate the final submitter file:
   ```bash
   hatch run python src/build.py --output "/Library/Application Support/KeyShot Studio/Scripts/Submit to AWS Deadline Cloud.py"
   ```
4. Test your changes by running the submitter in KeyShot

#### Running Tests

This package has both unit tests and integration tests. Unit tests verify business logic, use mocks, and do not involve KeyShot. Integration
tests verify end-to-end functionality, avoid mocks, and use KeyShot to run the submitter, generate bundles, and render scenes.

To run the unit tests, run:
```bash
hatch run test
```

To run the integration tests:
1. Set the environment variable `KEYSHOT_EXECUTABLE` to the location of the `keyshot_headless` application.
   1. `set KEYSHOT_EXECUTABLE=<keyshot_headless location>` on Windows.
      1. Default on Windows is:
         User install: `%USERPROFILE%\AppData\Local\KeyShot Studio\bin\keyshot_headless.exe`
         System install: `%PROGRAMFILES%\KeyShot\bin\keyshot_headless.exe`
   1. `export KEYSHOT_EXECUTABLE=<keyshot location>` on Linux and MacOS.
      1. Default in MacOS user installs: `/Applications/KeyShot Studio.app/Contents/MacOS/keyshot`
1. Ensure licensing is available on your machine for KeyShot
1. Run `hatch run integ:test`

## Testing the installer

1. Download the install builder tool from https://installbuilder.com/ (Evaluation)
2. Run `hatch run build`
3. Run `hatch run installer:build-installer --local-dev`
4. Installer should be built under the installer sub-folder.
5. Double click on the built installer to run it.


## Relevant links
- [Keyshot 2024 scripting documentation](https://media.keyshot.com/scripting/doc/2024.1/lux.html)
