# Development documentation

This documentation provides guidance on developer workflows for working with the code in this repository.

Table of Contents:

* [Software Architecture](#software-architecture)
* [Versioning](#versioning)
* [Development Environment Setup](#development-environment-setup)
* [The Development Loop](#the-development-loop)
   * [Submitter Development Workflow](#submitter-development-workflow)
      * [Running the Plug-In](#running-the-plug-in)
      * [Making Code Changes](#making-submitter-code-changes)
      * [Running Tests](#running-submitter-tests)
   * [Adaptor Development Workflow](#adaptor-development-workflow)
      * [Running the Adaptor Locally](#running-the-adaptor-locally)
      * [Running the Adaptor on a Farm](#running-the-adaptor-on-a-farm)

## Software Architecture

If you are not already familiar with the architecture of the KeyShot submitter plugin and adaptor application in this repository
then we suggest going over the [software architecture](docs/software_arch.md) for an overview of the components and how they function.

This package has two active branches:

- `mainline` -- For active development. This branch is not intended to be consumed by other packages. Any commit to this branch may break APIs, dependencies, and so on, and thus break any consumer without notice.
- `release` -- The official release of the package intended for consumers. Any breaking releases will be accompanied with an increase to this package's interface version.


You'll need to update your worker host with your updated adaptor code to test the changes.

## Versioning

This package's version follows [Semantic Versioning 2.0](https://semver.org/), but is still considered to be in its
initial development, thus backwards incompatible versions are denoted by minor version bumps. To help illustrate how
versions will increment during this initial development stage, they are described below:

1. The MAJOR version is currently 0, indicating initial development.
2. The MINOR version is currently incremented when backwards incompatible changes are introduced to the public API.
3. The PATCH version is currently incremented when bug fixes or backwards compatible changes are introduced to the public API.

## Development Environment Setup

To develop the Python code in this repository you will need:

1. Python 3.9 or higher. We recommend [mise](https://github.com/jdx/mise) if you would like to run more than one version
   of Python on the same system. When running unit tests against all supported Python versions, for instance.
2. The [hatch](https://github.com/pypa/hatch) package installed (`pip install --upgrade hatch`) into your Python environment.
3. An install of a supported version of Keyshot.
4. A valid AWS Account.
5. An AWS Deadline Cloud Farm to run jobs on. We recommend following the quickstart in the Deadline Cloud console to create a
   queue with the default queue environment, and a service-managed fleet.

Development on a Windows or Mac workstation is supported. Linux development support is experimental.

## The Development Loop

We have configured [hatch](https://github.com/pypa/hatch) commands to support a standard development loop. You can run the following
from any directory of this repository:

* `hatch build` - To build the installable Python wheel and sdist packages into the `dist/` directory.
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

### Submitter Development Workflow

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

#### Making Submitter Code Changes

You can modify `Submit to AWS Deadline Cloud.py` directly in the Keyshot scripts folder to test changes. Whenever you modify code for the plug-in, you can run the Keyshot submitter again via the Keyshot scripting console to test the changes.

#### Running Submitter Tests

Unit tests are currently used to test the plug-in.

Unit tests are small tests that are narrowly focused on ensuring that function-level behavior of the
   implementation behaves as it is expected to. These can always be run locally on your workstation without
   requiring an AWS account.

##### Unit Tests

Unit tests are all located under the `test/keyshot_submitter` directory of this repository. If you are adding
or modifying functionality, then you will almost always want to be writing one or more unit tests to demonstrate that your
logic behaves as expected and that future changes do not accidentally break your change.

To run the unit tests, simply use hatch:

```bash
hatch run test
```

### Adaptor Development Workflow

The keyshot adaptor is a command-line application (named `keyshot-openjd`) that interfaces with the KeyShot application.
You will need the `keyshot_headless.exe` executable available in your PATH for the adaptor to be able to run KeyShot.

When developing a change to the KeyShot adaptor we recommend primarily running the adaptor locally on your workstation,
and running and adding to the unit tests until you are comfortable that your change looks like it is working as you expect.
Testing locally like this will allow you to iterate faster on your change than the alternative of testing by
submitting jobs to Deadline Cloud to run using your modified adaptor. Then, test it out on a real render farm only once
you think that your change is functioning as you'd like.

#### Running the Adaptor Locally

To run the adaptor you will first need to create two files:

1. An `init-data.yaml` (or `init-data.json`) file that contains the information passed to the adaptor
   during its initialization phase. The schema for this file can be found at
   `src/deadline/keyshot_adaptor/KeyShotAdaptor/schemas/init_data.schema.json`
2. A `run-data.yaml` (or `run-data.json`) file that contains the information passed to the adaptor
   to do a single Task run. The schema for this file can be found at
   `src/deadline/keyshot_adaptor/KeyShotAdaptor/schemas/run_data.schema.json`

To run the adaptor once you have created an `init-data.yaml` and `run-data.yaml` file to test with:

1. Ensure that `keyshot_headless` can be run directly in your terminal by putting its location in your PATH environment variable.
2. Enter the hatch shell development environment by running `hatch shell`
3. Run the `keyshot-openjd` commmand-line with arguments that exercise your code change.

The adaptor has two modes of operation:

1. Running directly via the `keyshot-openjd run` subcommand; or
2. Running as a background daemon via subcommands of the `keyshot-openjd daemon` subcommand.

We recommend primarily developing using the `keyshot-openjd run` subcommand as it is simpler to operate
for rapid development iterations, but that you should also ensure that your change works with the background
daemon mode with multiple `run` commands before calling your change complete.

The basic command to run the `keyshot-openjd` run command will look like:

```bash
keyshot-openjd run \
  --init-data file://<absolute-path-to-init-data.yaml> \
  --run-data file://<absolute-path-to-run-data.yaml>
```

The equivalent run with the `keyshot-openjd daemon` subcommand looks like:

```bash
# The daemon start command requires that the connection-info file not already exist.
test -f connection-info.json || rm connection-info.json

# This starts up a background process running the adaptor, and runs the `on_init` and `on_start`
# methods of the adaptor.
keyshot-openjd daemon start \
  --init-data file://<absolute-path-to-init-data.yaml> \
  --connection-file file://connection-info.json

# This connects to the already running adaptor, via the information in the connection-info.json file,
# and runs the adaptor's `on_run` method.
# When testing, we suggest doing multiple "daemon run" commands with different inputs before
# running "daemon stop". This will help identify problems caused by data carrying over from a previous
# run.
keyshot-openjd daemon run \
  --run-data file://<absolute-path-to-run-data.yaml> \
  --connection-file file://connection-info.json

# This connects to the already running adaptor to instruct it to shutdown the keyshot application
# and then exit.
keyshot-openjd daemon stop \
  --connection-file file://connection-info.json
```

#### Running the Adaptor on a Farm

If you have made modifications to the adaptor and wish to test your modifications on a live Deadline Cloud Farm
with real jobs, then we recommend using a [customer-managed fleet](https://docs.aws.amazon.com/deadline-cloud/latest/userguide/manage-cmf.html)
for your testing. We recommend performing this style of test if you have made any modifications that might interact with Deadline Cloud's
job attachments feature, or that could interact with path mapping in any way.

## Relevant links
- [Keyshot 2024 scripting documentation](https://media.keyshot.com/scripting/doc/2024.1/lux.html)
