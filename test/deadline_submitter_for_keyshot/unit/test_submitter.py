# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
import tempfile
import deadline.keyshot_submitter.keyshot_render_submitter as submitter_module
from deadline.keyshot_submitter.data_classes import RenderSubmitterUISettings


def test_render_settings():
    a = RenderSubmitterUISettings()
    a.name = "Test Name"
    a.description = "Test Submitter Description"
    a.override_frame_range = True
    a.frame_list = "1-45"
    a.output_file_path = "Test Output File Path"
    a.input_filenames = ["Test Input Filenames"]
    a.input_directories = ["Test Input Directories"]
    a.output_directories = ["Test Output Directories"]
    a.include_adaptor_wheels = True
    _, path = tempfile.mkstemp(suffix="json", text=True)
    a.save_sticky_settings(path)
    b = RenderSubmitterUISettings()
    b.load_sticky_settings(path)
    assert a == b


def test_get_job_template():
    module_dir = Path(submitter_module.__file__).parent
    with open(module_dir / "default_keyshot_job_template.yaml") as fh:
        default_job_template = yaml.safe_load(fh)
    settings = RenderSubmitterUISettings()
    settings.output_file_path = "/tmp/foo.%d.tif"
    job_template = submitter_module._get_job_template(
        default_job_template,
        settings,
    )
    assert job_template["steps"]


def test_get_parameter_values():
    settings = RenderSubmitterUISettings()
    queue: list[dict[str, Any]] = []
    frames = "1-5"
    scene_name = "foo"
    params = submitter_module._get_parameter_values(settings, queue, frames, scene_name)
    assert params is not None
    for param in params:
        if param["name"] == "Frames":
            assert param["value"] == "1-5"
        if param["name"] == "KeyShotFile":
            assert param["value"] == "foo"
