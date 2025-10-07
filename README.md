# AWS Deadline Cloud for KeyShot

[![pypi](https://img.shields.io/pypi/v/deadline-cloud-for-keyshot.svg?style=flat)](https://pypi.python.org/pypi/deadline-cloud-for-keyshot)
[![python](https://img.shields.io/pypi/pyversions/deadline-cloud-for-keyshot.svg?style=flat)](https://pypi.python.org/pypi/deadline-cloud-for-keyshot)
[![license](https://img.shields.io/pypi/l/deadline-cloud-for-keyshot.svg?style=flat)](https://github.com/aws-deadline/deadline-cloud-for-keyshot/blob/mainline/LICENSE)

AWS Deadline Cloud for KeyShot is a python package that allows users to create [AWS Deadline Cloud][deadline-cloud] jobs from within KeyShot. Using the [Open Job Description (OpenJD) Adaptor Runtime][openjd-adaptor-runtime] this package also provides a command line application that adapts KeyShot's command line interface to support the [OpenJD specification][openjd].

For instructions on installing and using this integration, visit the [user guide](https://aws-deadline.github.io/deadline-cloud-for-keyshot).

[deadline-cloud]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/what-is-deadline-cloud.html
[deadline-cloud-client]: https://github.com/aws-deadline/deadline-cloud
[openjd]: https://github.com/OpenJobDescription/openjd-specifications/wiki
[openjd-adaptor-runtime]: https://github.com/OpenJobDescription/openjd-adaptor-runtime-for-python
[openjd-adaptor-runtime-lifecycle]: https://github.com/OpenJobDescription/openjd-adaptor-runtime-for-python/blob/release/README.md#adaptor-lifecycle
[default-queue-environment]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/create-queue-environment.html#conda-queue-environment
[deadline-cloud-submitter]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/submitter.html
[deadline-cloud-monitor]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/monitor-onboarding.html
[usage-based-licensing]: https://aws.amazon.com/deadline-cloud/features/
[service-managed-fleets]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/smf-manage.html

## Compatibility

This library requires:
1. KeyShot 2023 or 2024
1. Python 3.11 or higher; and
1. Windows or macOS operating system for job submission and Windows operating system for job rendering
1. A Deadline Cloud queue with job attachments configured

> [!NOTE]  
> Deadline Cloud service-managed fleets have built-in support for KeyShot 2024 only. When submitting a job from KeyShot 2023, you can still render your job on KeyShot 2024 by updating the "Conda Packages" field in the submitter specify `keyshot=2024.*`.

## Getting Started

The KeyShot integration for Deadline Cloud has two components that you will need to install:

1. The KeyShot submitter extension must be installed on the workstation that you will use to submit jobs; and
2. The KeyShot adaptor must be installed on all of your Deadline Cloud worker hosts that will be running the KeyShot jobs that you submit.

Before submitting any large, complex, or otherwise compute-heavy Keyshot render jobs to your farm using the submitter and adaptor that you
set up, we strongly recommend that you construct a simple test scene that can be rendered quickly and submit renders of that scene to your farm to ensure that your setup is functioning correctly.

## Submitter

The KeyShot submitter extension creates a runnable script in KeyShot (`Window` > `Scripting Console` > `Scripts` > `Submit to AWS Deadline Cloud` > `Run`) that can be used to submit jobs to Deadline Cloud. Using this script reveals an interface to submit a job to Deadline Cloud.
It automatically determines the files required based on the loaded scene, allows the user to specify render options, builds an
[Open Job Description template][openjd] that defines the workflow, and submits the job to the farm and queue of your choosing.

There are two installation options:
1. The [official Deadline Cloud submitter installer][deadline-cloud-submitter] (recommended)
2. Manual installation

After installing, you can access the submitter in the KeyShot interface via `Window` > `Scripting Console` > `Scripts` > `Submit to AWS Deadline Cloud` > `Run`.

For most setups, you will also want to install the [Deadline Cloud monitor][deadline-cloud-monitor].

### Manually installing the submitter

1. Run `pip install "deadline[gui]"`
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
    - The open scene file and all external files referenced in the BIP are included
    as job attachments. The submitter exports the open scene to a
    KeyShot Package (KSP) that turns all file paths in the scene into relative
    paths and creates a flattened directory with all of the external files directly
    beside the scene file. The KSP is then unzipped, and the new scene file with
    the relative paths and all external files are submitted with the job.
    The temporary directory used to save the KSP will be deleted after each
    submission.
1. Attach `Only the scene BIP file`
    - Only the open scene file is attached to the submission. Any
    external files referenced in the scene must be available to the workers
    through network storage or another method.



## Worker Licensing for KeyShot

### Service-Managed Fleets

[Usage based licensing][usage-based-licensing] for KeyShot 2023 and 2024 is available on Deadline Cloud service-managed fleets with no additional setup.

If you prefer to use your own licensing for service-managed fleets, you can also [connect service-managed fleets to a custom license server](https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/smf-byol.html).

### Customer-Managed Fleets

You can use [usage based licensing][usage-based-licensing] on customer-managed fleets by [connecting them to a license endpoint](https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/cmf-ubl.html).

You can also use your own licensing for customer-managed fleets.

> [!NOTE]  
> The KeyShot adaptor uses TCP ports in the range 9000-9099 for internal communication during rendering. These ports only listen on the loopback interface (127.0.0.1) and do not require network access.

## Viewing the Job Bundle that will be submitted

To submit a job, the submitter first generates a [Job Bundle][job-bundle], and then uses functionality from the
[Deadline client library][deadline-cloud-client] package to submit the Job Bundle to your render farm to run. If you would like to see
the job that will be submitted to your farm, then you can use the "Export Bundle" button in the submitter to export the
Job Bundle to a location of your choice. If you want to submit the job from the export, rather than through the
submitter plug-in then you can use the [Deadline Cloud application][deadline-cloud-client] to submit that bundle to your farm.

[job-bundle]: https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/build-job-bundle.html

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
