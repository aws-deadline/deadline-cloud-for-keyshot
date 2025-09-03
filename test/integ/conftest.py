# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def keyshot_location() -> Path:
    if "KEYSHOT_EXECUTABLE" in os.environ:
        return Path(os.environ["KEYSHOT_EXECUTABLE"])

    # Auto-detect KeyShot executable on macOS if possible
    mac_path = Path("/Applications/KeyShot Studio.app/Contents/MacOS/keyshot")
    if mac_path.exists():
        # Set the environment variable for the bridge to use
        os.environ["KEYSHOT_EXECUTABLE"] = str(mac_path)
        return mac_path

    raise RuntimeError(
        "KEYSHOT_EXECUTABLE env var must be defined for integration tests or KeyShot Studio must be installed in /Applications"
    )
