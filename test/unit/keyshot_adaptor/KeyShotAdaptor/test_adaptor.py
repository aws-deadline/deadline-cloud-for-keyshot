# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import json
from pathlib import Path

import pytest

from deadline.keyshot_adaptor.KeyShotAdaptor.adaptor import KeyShotAdaptor

# if this changes, the `integration_data_interface_version` should also be bumped
CURRENT_INIT_DATA_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "scene_file": {"type": "string"},
        "output_file_path": {"type": "string"},
        "output_format": {
            "enum": [
                "RENDER_OUTPUT_PNG",
                "RENDER_OUTPUT_JPEG",
                "RENDER_OUTPUT_EXR",
                "RENDER_OUTPUT_TIFF8",
                "RENDER_OUTPUT_TIFF32",
                "RENDER_OUTPUT_PSD8",
                "RENDER_OUTPUT_PSD16",
                "RENDER_OUTPUT_PSD32",
            ]
        },
    },
    "required": ["scene_file"],
}

# if this changes, the `integration_data_interface_version` should also be bumped
CURRENT_RUN_DATA_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {"frame": {"type": "number"}},
    "required": ["frame"],
}


@pytest.fixture
def init_data() -> dict:
    """
    Pytest Fixture to return an init_data dictionary that passes validation

    Returns:
        dict: An init_data dictionary
    """
    return {
        "scene_file": "C:\\Users\\user123\\test.c4d",
        "output_file_path": "C:\\Users\\user123\\test_render",
        "output_format": "RENDER_OUTPUT_PNG",
    }


def test_if_init_data_and_run_data_schema_are_changed_schema_version_is_bumped(init_data):
    """
    Test to validate that if the init data or run data schema are changed, we also bump the
    integration_data_interface_version
    """
    adaptor = KeyShotAdaptor(init_data)
    semantic_version = adaptor.integration_data_interface_version

    root_directory_path = Path(__file__).parent.parent.parent.parent.parent
    schema_path = root_directory_path.joinpath(
        "src", "deadline", "keyshot_adaptor", "KeyShotAdaptor", "schemas"
    )
    init_data_path = schema_path.joinpath("init_data.schema.json")
    run_data_path = schema_path.joinpath("run_data.schema.json")

    with init_data_path.open() as init_data_schema_file:
        init_data_schema = json.load(init_data_schema_file)
        assert (
            init_data_schema == CURRENT_INIT_DATA_SCHEMA
        ), "If the init_data.schema.json is changed, the integration_data_interface_version must be bumped"

    with run_data_path.open() as run_data_schema_file:
        run_data_schema = json.load(run_data_schema_file)
        assert (
            run_data_schema == CURRENT_RUN_DATA_SCHEMA
        ), "If the run_data.schema.json is changed, the integration_data_interface_version must be bumped"

    # if init_data.schema.json or run_data.schema.json are changed, these must
    # also be bumped
    assert semantic_version.major == 0
    assert semantic_version.minor == 1
