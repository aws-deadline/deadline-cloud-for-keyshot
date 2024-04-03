# AWS Deadline Cloud for KeyShot

[![pypi](https://img.shields.io/pypi/v/deadline-cloud-for-keyshot.svg?style=flat)](https://pypi.python.org/pypi/deadline-cloud-for-keyshot)
[![python](https://img.shields.io/pypi/pyversions/deadline-cloud-for-keyshot.svg?style=flat)](https://pypi.python.org/pypi/deadline-cloud-for-keyshot)
[![license](https://img.shields.io/pypi/l/deadline-cloud-for-keyshot.svg?style=flat)](https://github.com/aws-deadline/deadline-cloud-for-keyshot/blob/mainline/LICENSE)

AWS Deadline Cloud for KeyShot is a python package that allows users to create [AWS Deadline Cloud][deadline-cloud] jobs from within KeyShot. Using the [Open Job Description (OpenJD) Adaptor Runtime][openjd-adaptor-runtime] this package also provides a command line application that adapts KeyShot's command line interface to support the [OpenJD specification][openjd].

[deadline-cloud]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/what-is-deadline-cloud.html
[deadline-cloud-client]: https://github.com/aws-deadline/deadline-cloud
[openjd]: https://github.com/OpenJobDescription/openjd-specifications/wiki
[openjd-adaptor-runtime]: https://github.com/OpenJobDescription/openjd-adaptor-runtime-for-python
[openjd-adaptor-runtime-lifecycle]: https://github.com/OpenJobDescription/openjd-adaptor-runtime-for-python/blob/release/README.md#adaptor-lifecycle

## Compatibility

This library requires:
1. KeyShot 2023
1. Python 3.9 or higher; and
1. Windows, or a macOS operating system.

## Submitter

This package provides a KeyShot plugin script that creates jobs for AWS Deadline Cloud using the [AWS Deadline Cloud client library][deadline-cloud-client]. Based on the loaded scene it determines the files required, allows the user to specify render options with KeyShot's render interface, and builds an [OpenJD template][openjd] that defines the workflow.

### Using the KeyShot Submitter

1. Install deadline-cloud and PySide2
2. Copy or link the file `deadline-cloud-for-keyshot/keyshot_script/Submit to AWS Deadline Cloud.py` to the KeyShot scripts folder.
    - e.g. On Windows `C:/Users/<USER>/Documents/KeyShot 12/Scripts`
3. Set the following environment variables
    - Set the environment variable `DEADLINE_PYTHON` as the path to the Python installation where deadline-cloud and PySide2 were installed in step 1.
      - e.g. On Windows if using Python 3.10 it might be `set DEADLINE_PYTHON=C:/Users/<USER>/AppData/Local/Programs/Python/Python310/python`
    - Set the environment variable `DEADLINE_KEYSHOT` as the path to the `<PATH TO>/deadline-cloud-for-keyshot/src/deadline/keyshot_submitter` folder
      - e.g. On Windows if the source was on the user's desktop it might be  `set DEADLINE_KEYSHOT=C:/Users/<USER>/Desktop/deadline-cloud-for-keyshot/src/deadline/keyshot_submitter`
4. Launch KeyShot with the environment variables from step 3. set.
5. The submitter can be launched within KeyShot from `Windows > Scripting Console > Submit to AWS Deadline Cloud > Run`

## Adaptor

The KeyShot Adaptor implements the [OpenJD][openjd-adaptor-runtime] interface that allows render workloads to launch KeyShot and feed it commands. This gives the following benefits:
* a standardized render application interface,
* sticky rendering, where the application stays open between tasks

Jobs created by the submitter use this adaptor by default.

### Using the KeyShot Adaptor

1. Build and install `deadline-cloud-for-keyshot` on your workers
    - The adaptor can be installed by the standard python packaging mechanisms:
      ```sh
      $ pip install deadline-cloud-for-keyshot
      ```
    - After installation it can then be used as a command line tool:
      ```sh
      $ keyshot-openjd --help
      ```
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
3. Configure licensing for KeyShot by setting the environment variable `LUXION_LICENSE_FILE=<PORT>:<ADDRESS>` to point towards the license server to use
    - e.g. `setx LUXION_LICENSE_FILE "2703@127.0.0.1"`
4. The adaptor expects the keyshot_headless executable is available through the PATH environment variable.
    - e.g. Local install: `setx PATH "%LOCALAPPDATA%\KeyShot12\bin;%PATH%"`
    - e.g. System install: `setx PATH "%PROGRAMFILES%\KeyShot12\bin;%PATH%"`
    - Verify by running `keyshot_headless -h`

## Versioning

This package's version follows [Semantic Versioning 2.0](https://semver.org/), but is still considered to be in its 
initial development, thus backwards incompatible versions are denoted by minor version bumps. To help illustrate how
versions will increment during this initial development stage, they are described below:

1. The MAJOR version is currently 0, indicating initial development. 
2. The MINOR version is currently incremented when backwards incompatible changes are introduced to the public API. 
3. The PATCH version is currently incremented when bug fixes or backwards compatible changes are introduced to the public API. 

## Security

See [CONTRIBUTING](https://github.com/aws-deadline/deadline-cloud-for-keyshot/blob/release/CONTRIBUTING.md#security-issue-notifications) for more information.

## Telemetry

See [telemetry](https://github.com/aws-deadline/deadline-cloud-for-keyshot/blob/release/docs/telemetry.md) for more information.

## License

This project is licensed under the Apache-2.0 License.
