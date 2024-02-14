# Amazon Deadline Cloud for KeyShot

This package has two active branches:

- `mainline` -- For active development. This branch is not intended to be consumed by other packages. Any commit to this branch may break APIs, dependencies, and so on, and thus break any consumer without notice.
- `release` -- The official release of the package intended for consumers. Any breaking releases will be accompanied with an increase to this package's interface version.

## Using the KeyShot Submitter

1. Install deadline-cloud and PySide2
2. Copy or link the file `deadline-cloud-for-keyshot/keyshot_script/DeadlineCloudSubmitter.py` to the KeyShot scripts folder.
    - e.g. On Windows `C:/Users/<USER>/Documents/KeyShot 12/Scripts`
3. Set the following environment variables
    - Set the environment variable `DEADLINE_PYTHON` as the path to the Python installation where deadline-cloud and PySide2 were installed in step 1.
      - e.g. On Windows if using Python 3.10 it might be `set DEADLINE_PYTHON="C:/Users/<USER>/AppData/Local/Programs/Python/Python310/python"`
    - Set the environment variable `DEADLINE_KEYSHOT` as the path to the `<PATH TO>/deadline-cloud-for-keyshot/src/deadline/keyshot_submitter` folder
      - e.g. On Windows if the source was on the user's desktop it might be  `set DEADLINE_KEYSHOT="C:/Users/<USER>/Desktop/deadline-cloud-for-keyshot/src/deadline/keyshot_submitter"`
4. Launch KeyShot with the environment variables from step 3. set.
5. The submitter can be launched within KeyShot from `Windows > Scripting Console > DeadlineCloudSubmitter > Run`

## Using the KeyShot Adaptor

1. Build and install `deadline-cloud-for-keyshot` on your workers
2. KeyShot doesn't use PYTHONPATH and has a limited standard library so we explicitly load modules from the paths specified in the environment variable `DEADLINE_CLOUD_PYTHONPATH`. On your workers set the environment variable `DEADLINE_CLOUD_PYTHONPATH` to include paths to the following modules:
  - openjd
  - deadline
  - pywin32_system32
  - win32
  - Pythonwin

    e.g. On Windows running the worker in a virtual environment it might look something like:
    ```
    set DEADLINE_CLOUD_PYTHONPATH=C:/Users/<USER>/workervenv/Lib/site-packages/openjd;C:/Users/<USER>/workervenv/Lib/site-packages/deadline;C:/Users/<USER>/workervenv/Lib/site-packages/pywin32_system32;C:/Users/<USER>/workervenv/Lib/site-packages/win32;C:/Users/<USER>/workervenv/Lib/site-packages/win32/lib;C:/Users/<USER>/workervenv/Lib/site-packages/pythonwin
    ```

## Development

See [DEVELOPMENT](DEVELOPMENT.md) for more information.

## Compatibility

This library requires:

1. Python 3.7 or higher; and
2. Linux, MacOS, or Windows operating system.

## Versioning

This package's version follows [Semantic Versioning 2.0](https://semver.org/), but is still considered to be in its 
initial development, thus backwards incompatible versions are denoted by minor version bumps. To help illustrate how
versions will increment during this initial development stage, they are described below:

1. The MAJOR version is currently 0, indicating initial development. 
2. The MINOR version is currently incremented when backwards incompatible changes are introduced to the public API. 
3. The PATCH version is currently incremented when bug fixes or backwards compatible changes are introduced to the public API. 

## Downloading

You can download this package from:
- [GitHub releases](https://github.com/casillas2/deadline-cloud-for-keyshot/releases)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
