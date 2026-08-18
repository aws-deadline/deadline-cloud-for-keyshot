# AWS Deadline Cloud for KeyShot

### [User guide](https://docs.aws.amazon.com/deadline-cloud/latest/userguide/keyshot.html) | [Service documentation](https://docs.aws.amazon.com/deadline-cloud/) | [Deadline Cloud on GitHub](https://github.com/aws-deadline/) 

AWS Deadline Cloud for KeyShot is a Python plugin that allows users to create [AWS Deadline Cloud][deadline-cloud] jobs from within KeyShot.

[deadline-cloud]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/what-is-deadline-cloud.html
[user-guide]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/keyshot.html

## User guide

For installation and usage instructions, see the [AWS Deadline Cloud integrations user guide][user-guide]. The user guide covers:
- Installing the KeyShot submitter on Windows and macOS
- Submitting rendering jobs to Deadline Cloud
- Configuring job settings and render options

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

## Manual Installation (Development/Testing)

For development or testing purposes, you can manually install the submitter:

1. Install dependencies: `pip install "deadline[gui]"`
2. Copy `src/deadline/keyshot_submitter/Submit to AWS Deadline Cloud.py` to the KeyShot scripts folder:
    - Windows: `%USERPROFILE%/Documents/KeyShot Studio/Scripts` or `%PROGRAMFILES%/KeyShot Studio/Scripts`
    - macOS: `/Library/Application Support/KeyShot12/` or `/Library/Application Support/KeyShot/`
3. Launch KeyShot and access via `Window > Scripting Console > Scripts > Submit to AWS Deadline Cloud > Run`

## Submission Hooks (pre-GUI, pre-submission, post-submission)

Deadline Cloud supports [submission hooks](https://github.com/aws-deadline/deadline-cloud/blob/mainline/docs/submission-hooks.md) that run before/after a job is submitted — for example to pre-populate the submitter dialog, enforce a policy, or notify an external system.

**Nothing about the KeyShot integration itself needs to change to use hooks.** Unlike some other DCC submitters that import `deadline` as a library and build the submit dialog in-process, the KeyShot submitter shells out to the external `deadline` CLI (`deadline bundle gui-submit`). All three hook phases run inside that CLI, so KeyShot inherits hook support with no submitter-side code.

Requirements:
- The `deadline` CLI on the submitting workstation's `PATH` must be **≥ 0.60.1** (the release that ships the `deadline.client.ui.pre_gui_hooks` module). Verify with `deadline --version`.
- If a workstation has multiple `deadline` installs on `PATH` (e.g. the Deadline Cloud Monitor's bundled client alongside a `pip install deadline` in a system Python), make sure the one that resolves *first* meets the version floor — KeyShot's submitter uses whichever the shell resolves.

### How to use hooks with KeyShot

1. Create a hooks directory anywhere on disk (e.g. `C:\deadline-hooks` on Windows, `~/deadline-hooks` on macOS) containing a `hooks.yaml` and any script(s) it references:

    ```yaml
    # hooks.yaml
    version: "1.0"
    preGUI:
      - command: python
        args: [pregui_hook.py]
        timeout: 60
    preSubmission:
      - command: python
        args: [presubmit_hook.py]
        timeout: 60
    postSubmission:
      - command: python
        args: [postsubmit_hook.py]
        timeout: 60
    ```

    A minimal pre-GUI hook that pre-fills the dialog:

    ```python
    # pregui_hook.py
    import json, sys
    _ = sys.stdin.read()  # hook stdin is a JSON context object; safe to ignore
    print(json.dumps({
        "name": "My job (pre-filled by hook)",
        "description": "populated by pre-GUI hook",
        "parameters": {
            "deadline:priority": 88,
            "deadline:maxFailedTasksCount": 5,
            "deadline:maxRetriesPerTask": 3,
        },
    }))
    ```

2. Point `DEADLINE_HOOKS_DIR` at that directory *before* launching KeyShot (KeyShot inherits env vars from the process that starts it):
    - Windows: set the machine or user environment variable `DEADLINE_HOOKS_DIR` in **System Properties → Environment Variables**, then launch KeyShot from a fresh shell/Start-menu entry.
    - macOS: `export DEADLINE_HOOKS_DIR="$HOME/deadline-hooks"` in your shell profile, then launch KeyShot from that shell.

3. Launch KeyShot and run the submitter (`Window > Scripting Console > Scripts > Submit to AWS Deadline Cloud > Run`). You should see:
    - A **"Job Submission Confirmation"** dialog listing the hooks the CLI is about to run — click **Yes** to allow them.
    - The Deadline Cloud submitter dialog opens **pre-populated with the values your pre-GUI hook returned** (job name, priority, etc.).
    - On **Submit**, the pre-submission hook runs before the job is uploaded and the post-submission hook runs after the job is created (the created job's `DEADLINE_JOB_ID` is available in the post-submission hook's environment).

### Troubleshooting

- **The confirmation dialog never appears / no fields are pre-populated.** The pre-GUI hook did not run.
    1. Check `deadline --version` from the same shell that launched KeyShot — it must be ≥ 0.60.1.
    2. On Windows with multiple installs, run `where.exe deadline` and confirm the *first* result is a version that satisfies the floor. If not, upgrade the older install (`python -m pip install --upgrade "deadline>=0.60.1,<0.61"`) or reorder `PATH` so the newer client resolves first.
    3. Confirm KeyShot's own process sees `DEADLINE_HOOKS_DIR` — it inherits from the parent process at launch time, so changing the variable *after* KeyShot is running has no effect. Restart KeyShot from a fresh shell.
- **The dialog name/description update but the priority (or other job parameters) don't.** Job parameters such as `deadline:priority`, `deadline:maxFailedTasksCount`, and `deadline:maxRetriesPerTask` must be nested under the `"parameters"` key of the returned JSON (see the sample above). Only `name` and `description` are read from the top level; parameters placed at the top level are ignored.

## Worker Setup for KeyShot

To run KeyShot jobs on Deadline Cloud, workers must have KeyShot Studio installed and licensed. You can create a KeyShot conda package for your fleet using the [sample in the deadline-cloud-samples repository](https://github.com/aws-deadline/deadline-cloud-samples).

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
