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
[default-queue-environment]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/create-queue-environment.html#conda-queue-environment
[deadline-cloud-submitter]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/submitter.html
[deadline-cloud-monitor]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/monitor-onboarding.html
[usage-based-licensing]: https://aws.amazon.com/deadline-cloud/features/

## Compatibility

This library requires:
1. KeyShot 2023 or 2024
1. Python 3.9 or higher; and
1. Windows or macOS operating system for job submission and Windows operating system for job rendering

> [!NOTE]  
> Deadline Cloud service-managed fleets have built-in support for KeyShot 2024 only. When submitting a job from KeyShot 2023, you can still render your job on KeyShot 2024 by updating the "Conda Packages" field in the submitter specify `keyshot=2024.*`.

## Getting Started

The KeyShot integration for Deadline Cloud has two components that you will need to install:

1. The KeyShot submitter extension must be installed on the workstation that you will use to submit jobs; and
2. The KeyShot adaptor must be installed on all of your Deadline Cloud worker hosts that will be running the KeyShot jobs that you submit.

Before submitting any large, complex, or otherwise compute-heavy Keyshot render jobs to your farm using the submitter and adaptor that you
set up, we strongly recommend that you construct a simple test scene that can be rendered quickly and submit renders of that scene to your farm to ensure that your setup is functioning correctly.

## Submitter

The KeyShot submitter extension creates a button in KeyShot (`Window` > `Scripting Console` > `Scripts` > `Submit to AWS Deadline Cloud` > `Run`) that can be used to submit jobs to Deadline Cloud. Clicking this button reveals an interface to submit a job to Deadline Cloud.
It automatically determines the files required based on the loaded scene, allows the user to specify render options, builds an
[Open Job Description template][openjd] that defines the workflow, and submits the job to the farm and queue of your choosing.

There are two installation options:
1. Windows-only: install the submitter using the official Deadline Cloud submitter installer
2. Windows or Mac: manually install the submitter

For most setups, you will also need to install the [Deadline Cloud monitor](deadline-cloud-monitor).

### Install the submitter using the official Deadline Cloud submitter installer

The [official Deadline Cloud submitter installer](deadline-cloud-submitter) for Windows includes the KeyShot submitter. After installing, you can access the submitter in the KeyShot interface via `Window` > `Scripting Console` > `Scripts` > `Submit to AWS Deadline Cloud` > `Run`.

### Manually installing the submitter

1. Run `pip install deadline[gui]`
2. Copy the file `deadline-cloud-for-keyshot/src/deadline/keyshot_submitter/Submit to AWS Deadline Cloud.py` to the KeyShot scripts folder for your OS:
    - Windows (choose one):
        - User scripts folder e.g. `%USERPROFILE%/Documents/KeyShot/Scripts`
        - System-wide scripts folder e.g. `%PROGRAMFILES%/KeyShot/Scripts`
    - Mac: `/Library/Application Support/KeyShot12/` or `/Library/Application Support/KeyShot/` depending on your version of Keyshot.
        - You can navigate to the folder by going to Finder, clicking the menu for Go -> Go to Folder, and typing in the folder path.
3. Launch KeyShot. The submitter can be launched within KeyShot from `Window > Scripting Console > Scripts > Submit to AWS Deadline Cloud > Run`

## Submission Modes

There are two submission modes for the KeyShot submitter which a dialog will ask you to select from before opening the submitter UI.

1. Attach `The scene BIP file and all external files references`
    - The open scene file and all external files referenced within will be included
    as job attachments. The submitter will export the open scene to a
    KSP(KeyShot Package) which turns all file paths in the scene into relative
    paths and creates a flattened directory with all of the external files directly
    beside the scene file. The KSP is then unzipped, and the new scene file with
    the relative paths and all external files will be submitted with the job.
    The temporary directory used to save the KSP will be deleted after each
    submission.
1. Attach `Only the scene BIP file`
    - Only the open scene file will be attached to the submission. The expectation is that any
    external files referenced within the scene will be available to the workers
    through network storage or some other method.

## Adaptor

Jobs created by the KeyShot submitter require the adaptor to be installed on your worker hosts.

The KeyShot Adaptor implements the [OpenJD][openjd-adaptor-runtime] interface that allows render workloads to launch KeyShot and feed it commands. This gives the following benefits:
* a standardized render application interface,
* sticky rendering, where the application stays open between tasks

Both fleet types in Deadline Cloud support the KeyShot adaptor:
1. Service-managed fleets
2. Customer-managed fleets

The KeyShot integration for Deadline Cloud is supported on Windows fleets (service-managed and customer-managed).
Linux support is experimental and can only be done on customer-managed fleets.

### Service-managed fleets

On [service-managed fleets](service-managed-fleets), the KeyShot adaptor is automatically available via the `deadline-cloud` Conda channel with the [default Queue Environment][default-queue-environment].

### Customer-managed fleets

Keyshot must be manually installed on worker hosts of customer-managed fleets.

#### Manually installing on worker hosts

Both the installed adaptor and the KeyShot executable (`keyshot_headless.exe`) must be available on the PATH of the user that will be running your jobs.

You can also set the `KEYSHOT_EXECUTABLE` to point to the KeyShot executable. The adaptor must still be on the PATH.

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
    - e.g. Local install: `setx PATH "%LOCALAPPDATA%\KeyShot\bin;%PATH%"`
    - e.g. System install: `setx PATH "%PROGRAMFILES%\KeyShot\bin;%PATH%"`
    - Verify by running `keyshot_headless -h`

## Worker Licensing for KeyShot

### Service-Managed Fleets

[Usage based licensing](usage-based-licensing) for KeyShot 2023 and 2024 is available on Deadline Cloud service-managed fleets with no additional setup.

If you prefer to use your own licensing for service-managed fleets, you can also [connect service-managed fleets to a custom license server](https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/smf-byol.html).

### Customer-Managed Fleets

You can use [usage based licensing](usage-based-licensing) on customer-managed fleets by [connecting them to a license endpoint](https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/cmf-ubl.html).

You can also use your own licensing for customer-managed fleets.

## Viewing the Job Bundle that will be submitted

To submit a job, the submitter first generates a [Job Bundle][job-bundle], and then uses functionality from the
[Deadline client library][deadline-cloud-client] package to submit the Job Bundle to your render farm to run. If you would like to see
the job that will be submitted to your farm, then you can use the "Export Bundle" button in the submitter to export the
Job Bundle to a location of your choice. If you want to submit the job from the export, rather than through the
submitter plug-in then you can use the [Deadline Cloud application][deadline-cloud-client] to submit that bundle to your farm.

[job-bundle]: https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/build-job-bundle.html

## Security

See [CONTRIBUTING](https://github.com/aws-deadline/deadline-cloud-for-keyshot/blob/release/CONTRIBUTING.md#security-issue-notifications) for more information.

## Telemetry

See [telemetry](https://github.com/aws-deadline/deadline-cloud-for-keyshot/blob/release/docs/telemetry.md) for more information.

## License

This project is licensed under the Apache-2.0 License.
