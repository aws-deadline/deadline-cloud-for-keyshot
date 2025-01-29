# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

from pathlib import Path

import pytest

from .helpers.test_runners import run_keyshot_test


@pytest.mark.parametrize("scene_name", ["cube"])
def test_cube_scene_test(scene_name: str, keyshot_location: Path) -> None:
    scene_path = Path(__file__).parent / scene_name
    run_keyshot_test(keyshot_location, scene_path)
