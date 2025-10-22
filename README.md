# AWS Deadline Cloud for KeyShot

[![license](https://img.shields.io/pypi/l/deadline-cloud-for-keyshot.svg?style=flat)](https://github.com/aws-deadline/deadline-cloud-for-keyshot/blob/mainline/LICENSE)

AWS Deadline Cloud for KeyShot is a Python plugin that allows users to create [AWS Deadline Cloud][deadline-cloud] jobs from within KeyShot.

![Screenshot of the KeyShot submitter](./docs/user_guide/images/main-screenshot.png)

[deadline-cloud]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/what-is-deadline-cloud.html
[default-queue-environment]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/create-queue-environment.html#conda-queue-environment
[usage-based-licensing]: https://aws.amazon.com/deadline-cloud/features/
[user-guide]: https://aws-deadline.github.io/keyshot/user-guide/

## User guide

For installation and usage instructions, see the [AWS Deadline Cloud integrations user guide][user-guide]. The user guide covers:
- Installing the KeyShot submitter on Windows and macOS
- Submitting rendering jobs to Deadline Cloud
- Configuring job settings and render options

## Requirements

- KeyShot 2023 - 2025
- Windows or macOS workstation for job submission
- Windows worker for job rendering
- Deadline Cloud queue with job attachments enabled and the [default queue environment][default-queue-environment]

## Architecture

The integration consists of two main components:

1. **Submitter** (`src/submitter.py`) - A KeyShot script that provides a GUI for submitting jobs to Deadline Cloud. It exports the scene to a KeyShot Package (KSP), extracts assets, and generates an OpenJD job bundle.

2. **Adaptor** - A command-line application that runs on worker hosts to execute KeyShot rendering tasks defined in OpenJD job templates.

See the [ARCHITECTURE.md](ARCHITECTURE.md) for more details.

## Development Setup

See [DEVELOPMENT.md](DEVELOPMENT.md) for instructions on setting up a development environment.

## Manual Installation (Development/Testing)

For development or testing purposes, you can manually install the submitter:

1. Install dependencies: `pip install "deadline[gui]"`
2. Copy `src/deadline/keyshot_submitter/Submit to AWS Deadline Cloud.py` to the KeyShot scripts folder:
    - Windows: `%USERPROFILE%/Documents/KeyShot/Scripts` or `%PROGRAMFILES%/KeyShot/Scripts`
    - macOS: `/Library/Application Support/KeyShot12/` or `/Library/Application Support/KeyShot/`
3. Launch KeyShot and access via `Window > Scripting Console > Scripts > Submit to AWS Deadline Cloud > Run`

## Worker Licensing for KeyShot

### Service-Managed Fleets

[Usage based licensing][usage-based-licensing] for KeyShot 2023 and 2024 is available on Deadline Cloud service-managed fleets with no additional setup.

If you prefer to use your own licensing for service-managed fleets, you can also [connect service-managed fleets to a custom license server](https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/smf-byol.html).

### Customer-Managed Fleets

You can use [usage based licensing][usage-based-licensing] on customer-managed fleets by [connecting them to a license endpoint](https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/cmf-ubl.html).

You can also use your own licensing for customer-managed fleets.

> [!NOTE]  
> The KeyShot adaptor uses TCP ports in the range 9000-9099 for internal communication during rendering. These ports only listen on the loopback interface (127.0.0.1) and do not require network access.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for information on reporting security issues and contributing to the project.

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
