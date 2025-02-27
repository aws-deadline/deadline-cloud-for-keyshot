# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def keyshot_location() -> Path:
    if "KEYSHOT_EXECUTABLE" not in os.environ:
        raise RuntimeError("KEYSHOT_EXECUTABLE env var must be defined for integration tests")
    return Path(os.environ["KEYSHOT_EXECUTABLE"])
