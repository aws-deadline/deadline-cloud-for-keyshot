# AWS Deadline Cloud for KeyShot

### [User guide](https://docs.aws.amazon.com/deadline-cloud/latest/userguide/keyshot.html) | [Service documentation](https://docs.aws.amazon.com/deadline-cloud/) | [Deadline Cloud on GitHub](https://github.com/aws-deadline/) 

AWS Deadline Cloud for KeyShot is a Python plugin that allows users to create [AWS Deadline Cloud][deadline-cloud] jobs from within KeyShot.

[deadline-cloud]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/what-is-deadline-cloud.html
[user-guide]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/keyshot.html

## User guide

For usage instructions, see the [AWS Deadline Cloud integrations user guide][user-guide]. The user guide covers:
- Submitting rendering jobs to Deadline Cloud
- Configuring job settings and render options

> [!IMPORTANT]
> The KeyShot submitter is no longer included in the Deadline Cloud submitter installer, and Deadline Cloud no
> longer provides a KeyShot conda package for service-managed fleets. Install the submitter manually (see
> [Installation](#installation)) and provide your own KeyShot conda package for workers (see
> [Worker Setup for KeyShot](#worker-setup-for-keyshot)).

## Requirements

- KeyShot 2023 - 2025
- Windows or macOS workstation for job submission
- Windows worker for job rendering with KeyShot Studio installed and licensed

## Architecture

The integration consists of two main components:

1. **Submitter** (`src/submitter.py`) - A KeyShot script that provides a GUI for submitting jobs to Deadline Cloud. It exports the scene to a KeyShot Package (KSP), extracts assets, and generates an OpenJD job bundle.

2. **Adaptor** - A command-line application that runs on worker hosts to execute KeyShot rendering tasks defined in OpenJD job templates.

See the [ARCHITECTURE.md](ARCHITECTURE.md) for more details.

## Development Setup

See [DEVELOPMENT.md](DEVELOPMENT.md) for instructions on setting up a development environment.

## Installation

The submitter is installed manually on each workstation that submits jobs:

1. Install the Deadline Cloud CLI with GUI support so that `deadline` is on your `PATH`: `pip install "deadline[gui]"`
2. Build the submitter script from a clone of this repository:
    ```sh
    git clone https://github.com/aws-deadline/deadline-cloud-for-keyshot.git
    cd deadline-cloud-for-keyshot
    pip install hatch
    hatch run build
    ```
    This writes the self-contained submitter to `dist/Submit to AWS Deadline Cloud.py`.
3. Copy `dist/Submit to AWS Deadline Cloud.py` to the KeyShot scripts folder:
    - Windows: `%USERPROFILE%/Documents/KeyShot Studio/Scripts` or `%PROGRAMFILES%/KeyShot Studio/Scripts`
    - macOS: `/Library/Application Support/KeyShot Studio/Scripts`
4. Launch KeyShot and access via `Window > Scripting Console > Scripts > Submit to AWS Deadline Cloud > Run`

## Submission Hooks

Because the KeyShot submitter shells out to the external `deadline` CLI (`deadline bundle gui-submit`), it inherits Deadline Cloud's submission hooks — pre-GUI, pre-submission, and post-submission — with no submitter-side code. Hooks are read from the directory named by `DEADLINE_HOOKS_DIR`; enable them with `deadline config set settings.allow_environment_hooks true`.

The one KeyShot-specific requirement is the version of the `deadline` CLI resolved on `PATH` (check with `deadline --version`): the hook mechanism requires **≥ 0.60.1**, and `deadline:` job-property overrides (e.g. `deadline:priority`) require **≥ 0.60.4** because KeyShot submits through the job-bundle `gui-submit` path.

See [deadline-cloud's `docs/submission-hooks.md`](https://github.com/aws-deadline/deadline-cloud/blob/mainline/docs/submission-hooks.md) for full documentation — hook types, the `hooks.yaml` format, examples, and troubleshooting.

## Worker Setup for KeyShot

To run KeyShot jobs on Deadline Cloud, workers must have KeyShot Studio installed and licensed.

Deadline Cloud does not provide a KeyShot conda package in the `deadline-cloud` channel. To run KeyShot on
service-managed fleets, or any fleet that uses a conda queue environment, build your own KeyShot conda package
using the [KeyShot conda recipe in the deadline-cloud-samples repository](https://github.com/aws-deadline/deadline-cloud-samples/tree/mainline/conda_recipes/keyshot-2025)
and host it in your own conda channel, such as an S3 bucket. Then set the queue environment's `CondaChannels` parameter
default to that channel, or enter it in the submitter's job settings. The submitter requests the `keyshot=<major version>.*`
package that matches the version of KeyShot the job is submitted from.

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

See [telemetry](https://docs.aws.amazon.com/deadline-cloud/latest/userguide/opt-out.html) for more information.

## License

This project is licensed under the Apache-2.0 License.
