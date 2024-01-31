# Amazon Deadline Cloud for KeyShot

This package has two active branches:

- `mainline` -- For active development. This branch is not intended to be consumed by other packages. Any commit to this branch may break APIs, dependencies, and so on, and thus break any consumer without notice.
- `release` -- The official release of the package intended for consumers. Any breaking releases will be accompanied with an increase to this package's interface version.

## Use Submitter in KeyShot

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

## Development

See [DEVELOPMENT](DEVELOPMENT.md) for more information.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
