# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import mock_lux  # type: ignore[import-not-found] # noqa: F401

deadline = __import__("deadline.keyshot_submitter.Submit to AWS Deadline Cloud")
submitter = getattr(deadline.keyshot_submitter, "Submit to AWS Deadline Cloud")


def test_construct_job_template():
    filename = "test_filename"

    job_template = submitter.construct_job_template(filename)

    assert job_template["name"] == filename


def test_construct_asset_references():
    settings = submitter.Settings(
        scene_file="test_scene_file",
        frames="10-17",
        input_filenames=["test_filename_1"],
        auto_detected_input_filenames=["test_filename_2"],
        input_directories=["test_directory_1", "test_directory_2"],
        output_directories=["test_directory_3"],
        auto_detected_output_directories=["test_directory_4"],
        referenced_paths=["reference_path_1", "reference_path_2"],
        output_file_path=r"test_scene_file.%d.png",
        output_format="PNG",
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
        scene_file="test_scene_file",
        frames="10-17",
        input_filenames=[],
        auto_detected_input_filenames=[],
        input_directories=[],
        output_directories=[],
        auto_detected_output_directories=[],
        referenced_paths=[],
        output_file_path=r"test_scene_file.%d.png",
        output_format="PNG",
    )

    parameter_values = submitter.construct_parameter_values(settings)

    assert parameter_values == {
        "parameterValues": [
            {"name": "KeyShotFile", "value": settings.scene_file},
            {"name": "OutputFilePath", "value": settings.output_file_path},
            {"name": "OutputFormat", "value": settings.output_format},
            {"name": "Frames", "value": settings.frames},
        ]
    }


def test_settings_serialize_correctly():
    settings = submitter.Settings(
        scene_file="test_scene_file",
        frames="10-17",
        input_filenames=["test_filename_1"],
        auto_detected_input_filenames=["test_directory_3"],
        input_directories=["test_directory_1"],
        output_directories=["test_directory_2"],
        auto_detected_output_directories=[],
        referenced_paths=["test_ref_path"],
        output_file_path=r"test_scene_file.%d.png",
        output_format="PNG",
    )

    assert settings.to_dict() == {
        "frames": "10-17",
        "outputFilePath": r"test_scene_file.%d.png",
        "outputFormat": "PNG",
        "inputFilenames": ["test_filename_1"],
        "inputDirectories": ["test_directory_1"],
        "outputDirectories": ["test_directory_2"],
        "referencedPaths": ["test_ref_path"],
    }


def test_settings_apply_sticky_settings():
    settings = submitter.Settings(
        scene_file="test_scene_file",
        frames="10-17",
        input_filenames=["test_filename_1"],
        auto_detected_input_filenames=["test_filename_2"],
        input_directories=["test_directory_1"],
        output_directories=["test_directory_2"],
        auto_detected_output_directories=[],
        referenced_paths=["test_ref_path"],
        output_file_path=r"test_scene_file.%d.png",
        output_format="PNG",
    )
    initial_settings = settings.to_dict()

    settings.apply_sticky_settings({})
    assert settings.to_dict() == initial_settings

    settings.apply_sticky_settings(
        {
            "frames": "20-27",
            "outputFilePath": "test_scene_file2",
            "outputFormat": "JPEG",
            "inputFilenames": ["test_filename_10"],
            "inputDirectories": ["test_directory_11"],
            "outputDirectories": ["test_directory_12"],
            "referencedPaths": ["test_ref_path_2"],
        }
    )

    assert settings.frames == "20-27"
    assert settings.output_file_path == "test_scene_file2"
    assert settings.output_format == "JPEG"
    assert settings.input_filenames == ["test_filename_10"]
    assert settings.input_directories == ["test_directory_11"]
    assert settings.output_directories == ["test_directory_12"]
    assert settings.referenced_paths == ["test_ref_path_2"]


def test_settings_apply_submitter_settings():
    settings = submitter.Settings(
        scene_file="test_scene_file",
        frames="10-17",
        input_filenames=["test_filename_1"],
        auto_detected_input_filenames=["test_filename_2"],
        input_directories=["test_directory_1"],
        output_directories=["test_directory_2"],
        auto_detected_output_directories=["test_directory_3"],
        referenced_paths=["test_ref_path"],
        output_file_path=r"test_scene_file.%d.png",
        output_format="PNG",
    )

    settings.apply_submitter_settings(
        {
            "assetReferences": {
                "inputs": {
                    "filenames": ["test_filename_1", "test_filename_2", "test_filename_3"],
                    "directories": ["test_directory_2"],
                },
                "outputs": {
                    "directories": ["test_directory_2", "test_directory_3", "test_directory_4"]
                },
                "referencedPaths": ["test_ref_path_2"],
            },
            "parameterValues": [
                {"name": "Frames", "value": "20-27"},
                {"name": "OutputFilePath", "value": "test_scene_file2"},
                {"name": "OutputFormat", "value": "JPEG"},
            ],
        }
    )

    assert settings.frames == "20-27"
    assert settings.output_file_path == "test_scene_file2"
    assert settings.output_format == "JPEG"
    assert sorted(settings.input_filenames) == ["test_filename_1", "test_filename_3"]
    assert sorted(settings.input_directories) == ["test_directory_2"]
    assert sorted(settings.output_directories) == ["test_directory_2", "test_directory_4"]
    assert sorted(settings.referenced_paths) == ["test_ref_path_2"]
