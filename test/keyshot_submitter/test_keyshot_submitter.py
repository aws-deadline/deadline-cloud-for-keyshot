# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from unittest.mock import Mock
import mock_lux  # type: ignore[import-not-found] # noqa: F401

import json
import os
import tempfile
import pytest


deadline = __import__("deadline.keyshot_submitter.Submit to AWS Deadline Cloud")
submitter = getattr(deadline.keyshot_submitter, "Submit to AWS Deadline Cloud")


def test_construct_job_template():
    filename = "test_filename"

    job_template = submitter.construct_job_template(filename)

    assert job_template["name"] == filename


def test_construct_asset_references():
    settings = submitter.Settings(
        parameter_values=[
            {"name": "KeyShotFile", "value": "test_scene_file"},
            {"name": "OutputFilePath", "value": r"test_scene_file.%d.png"},
            {"name": "OutputFormat", "value": "PNG"},
            {"name": "Frames", "value": "10-17"},
        ],
        input_filenames=["test_filename_1"],
        auto_detected_input_filenames=["test_filename_2"],
        input_directories=["test_directory_1", "test_directory_2"],
        output_directories=["test_directory_3"],
        auto_detected_output_directories=["test_directory_4"],
        referenced_paths=["reference_path_1", "reference_path_2"],
    )

    asset_references = submitter.construct_asset_references(settings)

    assert asset_references["assetReferences"]["inputs"]["filenames"] == [
        "test_filename_1",
        "test_filename_2",
    ]
    assert (
        asset_references["assetReferences"]["inputs"]["directories"] == settings.input_directories
    )
    assert asset_references["assetReferences"]["outputs"]["directories"] == [
        "test_directory_3",
        "test_directory_4",
    ]
    assert asset_references["assetReferences"]["referencedPaths"] == settings.referenced_paths


def test_construct_parameter_values():
    settings = submitter.Settings(
        parameter_values=[
            {"name": "KeyShotFile", "value": "test_scene_file"},
            {"name": "OutputFilePath", "value": r"test_scene_file.%d.png"},
            {"name": "OutputFormat", "value": "PNG"},
            {"name": "Frames", "value": "10-17"},
        ],
        input_filenames=[],
        auto_detected_input_filenames=[],
        input_directories=[],
        output_directories=[],
        auto_detected_output_directories=[],
        referenced_paths=[],
    )

    parameter_values = submitter.construct_parameter_values(settings)

    assert parameter_values == {
        "parameterValues": [
            {"name": "KeyShotFile", "value": "test_scene_file"},
            {"name": "OutputFilePath", "value": r"test_scene_file.%d.png"},
            {"name": "OutputFormat", "value": "PNG"},
            {"name": "Frames", "value": "10-17"},
        ]
    }


def test_settings_serialize_correctly():
    settings = submitter.Settings(
        parameter_values=[
            {"name": "KeyShotFile", "value": "test_scene_file"},
            {"name": "OutputFilePath", "value": r"test_scene_file.%d.png"},
            {"name": "OutputFormat", "value": "PNG"},
            {"name": "Frames", "value": "10-17"},
        ],
        input_filenames=["test_filename_1"],
        auto_detected_input_filenames=["test_directory_3"],
        input_directories=["test_directory_1"],
        output_directories=["test_directory_2"],
        auto_detected_output_directories=[],
        referenced_paths=["test_ref_path"],
    )

    assert settings.output_sticky_settings() == {
        "parameterValues": [
            {"name": "OutputFilePath", "value": r"test_scene_file.%d.png"},
            {"name": "OutputFormat", "value": "PNG"},
            {"name": "Frames", "value": "10-17"},
        ],
        "inputFilenames": ["test_filename_1"],
        "inputDirectories": ["test_directory_1"],
        "outputDirectories": ["test_directory_2"],
        "referencedPaths": ["test_ref_path"],
    }


def test_settings_apply_sticky_settings():
    settings = submitter.Settings(
        parameter_values=[
            {"name": "KeyShotFile", "value": "test_scene_file"},
            {"name": "OutputFilePath", "value": r"test_scene_file.%d.png"},
            {"name": "OutputFormat", "value": "PNG"},
            {"name": "Frames", "value": "10-17"},
        ],
        input_filenames=["test_filename_1"],
        auto_detected_input_filenames=["test_filename_2"],
        input_directories=["test_directory_1"],
        output_directories=["test_directory_2"],
        auto_detected_output_directories=[],
        referenced_paths=["test_ref_path"],
    )
    initial_settings = settings.output_sticky_settings()

    settings.apply_sticky_settings({})
    assert settings.output_sticky_settings() == initial_settings

    settings.apply_sticky_settings(
        {
            "parameterValues": [
                {"name": "OutputFilePath", "value": "test_output_2"},
                {"name": "OutputFormat", "value": "JPEG"},
                {"name": "Frames", "value": "20-27"},
            ],
            "inputFilenames": ["test_filename_10"],
            "inputDirectories": ["test_directory_11"],
            "outputDirectories": ["test_directory_12"],
            "referencedPaths": ["test_ref_path_2"],
        }
    )

    assert settings.parameter_values == [
        {"name": "KeyShotFile", "value": "test_scene_file"},
        {"name": "OutputFilePath", "value": "test_output_2"},
        {"name": "OutputFormat", "value": "JPEG"},
        {"name": "Frames", "value": "20-27"},
    ]
    assert settings.input_filenames == ["test_filename_10"]
    assert settings.input_directories == ["test_directory_11"]
    assert settings.output_directories == ["test_directory_12"]
    assert settings.referenced_paths == ["test_ref_path_2"]

    settings.apply_sticky_settings(
        {
            "parameterValues": [
                # input KeyShotFile from sticky settings should be ignored
                {"name": "KeyShotFile", "value": "scene_file_from_sticky_settings"},
            ],
            "inputFilenames": ["test_filename_20"],
            "inputDirectories": ["test_directory_21"],
            "outputDirectories": ["test_directory_22"],
            "referencedPaths": ["test_ref_path_3"],
        }
    )

    assert settings.parameter_values == [
        {"name": "KeyShotFile", "value": "test_scene_file"},
        {"name": "OutputFilePath", "value": "test_output_2"},
        {"name": "OutputFormat", "value": "JPEG"},
        {"name": "Frames", "value": "20-27"},
    ]
    assert settings.input_filenames == ["test_filename_20"]
    assert settings.input_directories == ["test_directory_21"]
    assert settings.output_directories == ["test_directory_22"]
    assert settings.referenced_paths == ["test_ref_path_3"]


def test_settings_apply_submitter_settings():
    settings = submitter.Settings(
        parameter_values=[
            {"name": "KeyShotFile", "value": "scene_file_from_scene"},
            {"name": "OutputFilePath", "value": r"test_scene_file.%d.png"},
            {"name": "OutputFormat", "value": "PNG"},
            {"name": "Frames", "value": "10-17"},
        ],
        input_filenames=["test_filename_1"],
        auto_detected_input_filenames=["test_filename_2"],
        input_directories=["test_directory_1"],
        output_directories=["test_directory_2"],
        auto_detected_output_directories=["test_directory_3"],
        referenced_paths=["test_ref_path"],
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, "parameter_values.json"), "w") as parameter_values_file:
            json.dump(
                {
                    "parameterValues": [
                        {"name": "KeyShotFile", "value": "scene_file_from_gui_submit"},
                        {"name": "Frames", "value": "20-27"},
                        {"name": "OutputFilePath", "value": "test_output_2"},
                        {"name": "OutputFormat", "value": "JPEG"},
                    ],
                },
                parameter_values_file,
            )
        with open(os.path.join(temp_dir, "asset_references.json"), "w") as asset_references_file:
            json.dump(
                {
                    "assetReferences": {
                        "inputs": {
                            "filenames": [
                                "test_filename_1",
                                "test_filename_2",
                                "test_filename_3",
                            ],
                            "directories": ["test_directory_2"],
                        },
                        "outputs": {
                            "directories": [
                                "test_directory_2",
                                "test_directory_3",
                                "test_directory_4",
                            ]
                        },
                        "referencedPaths": ["test_ref_path_2"],
                    },
                },
                asset_references_file,
            )
        settings.apply_submitter_settings({"jobHistoryBundleDirectory": temp_dir})

    assert settings.parameter_values == [
        {"name": "KeyShotFile", "value": "scene_file_from_gui_submit"},
        {"name": "Frames", "value": "20-27"},
        {"name": "OutputFilePath", "value": "test_output_2"},
        {"name": "OutputFormat", "value": "JPEG"},
    ]
    assert sorted(settings.input_filenames) == ["test_filename_1", "test_filename_3"]
    assert sorted(settings.input_directories) == ["test_directory_2"]
    assert sorted(settings.output_directories) == ["test_directory_2", "test_directory_4"]
    assert sorted(settings.referenced_paths) == ["test_ref_path_2"]


def test_unsaved_changes_prompt():
    local_mock_lux = Mock()
    local_mock_lux.isSceneChanged.return_value = True
    with pytest.raises(Exception):
        submitter.main(local_mock_lux)
        local_mock_lux.getMessageBox.assert_called()
