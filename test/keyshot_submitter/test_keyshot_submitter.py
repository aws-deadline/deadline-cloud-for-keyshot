# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import os
import tempfile
import mock_lux  # noqa: F401

deadline = __import__("deadline.keyshot_submitter.Submit to AWS Deadline Cloud")
submitter = getattr(deadline.keyshot_submitter, "Submit to AWS Deadline Cloud")


def test_construct_job_template():
    filename = "test_filename"

    job_template = submitter.construct_job_template(filename)

    assert job_template["name"] == filename


def test_construct_asset_references():
    input_filenames = ["test_filename_1", "test_filename_2"]
    input_directories = ["test_directory_1", "test_directory_2"]
    output_directories = ["test_directory_3", "test_directory_4"]
    referenced_paths = ["reference_path_1", "reference_path_2"]

    asset_references = submitter.construct_asset_references(
        input_filenames=input_filenames,
        input_directories=input_directories,
        output_directories=output_directories,
        referenced_paths=referenced_paths,
    )

    assert asset_references["assetReferences"]["inputs"]["filenames"] == input_filenames
    assert asset_references["assetReferences"]["inputs"]["directories"] == input_directories
    assert asset_references["assetReferences"]["outputs"]["directories"] == output_directories
    assert asset_references["assetReferences"]["referencedPaths"] == referenced_paths


def test_construct_parameter_values():
    scene_file = "test_scene_file"
    frames = "10-17"
    output_file_path = r"test_scene_file.%d.png"
    output_format = "PNG"

    parameter_values = submitter.construct_parameter_values(
        scene_file=scene_file,
        frames=frames,
        output_file_path=output_file_path,
        output_format=output_format,
    )

    assert parameter_values == {
        "parameterValues": [
            {"name": "KeyShotFile", "value": scene_file},
            {"name": "OutputFilePath", "value": output_file_path},
            {"name": "OutputFormat", "value": output_format},
            {"name": "Frames", "value": frames},
        ]
    }


def test_get_settings_from_bundle_loads_bundle_settings_correctly():
    with tempfile.TemporaryDirectory() as temp_dir:
        submitter.dump_json_to_dir(
            submitter.construct_parameter_values(
                scene_file="scene",
                frames="10-17",
                output_file_path=r"output.%d.png",
                output_format="PNG",
            ),
            temp_dir,
            "parameter_values.json",
        )
        submitter.dump_json_to_dir(
            submitter.construct_asset_references(
                input_filenames=["file1"],
                input_directories=["dir1"],
                output_directories=["dir2"],
                referenced_paths=["refpath"],
            ),
            temp_dir,
            "asset_references.json",
        )
        prev_parameters, prev_references = submitter.get_settings_from_bundle(temp_dir)

    assert prev_parameters["Frames"] == "10-17"
    assert prev_parameters["OutputFilePath"] == r"output.%d.png"
    assert prev_parameters["OutputFormat"] == "PNG"
    assert prev_references["inputs"]["filenames"] == ["file1"]
    assert prev_references["inputs"]["directories"] == ["dir1"]
    assert prev_references["outputs"]["directories"] == ["dir2"]
    assert prev_references["referencedPaths"] == ["refpath"]


def test_get_settings_from_bundle_returns_none_for_missing_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        prev_parameters, prev_references = submitter.get_settings_from_bundle(temp_dir)

    assert prev_parameters is None
    assert prev_references is None


def test_get_settings_from_bundle_returns_none_for_invalid_json():
    with tempfile.TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, "parameter_values.json"), "w") as file:
            file.write("not json")
        with open(os.path.join(temp_dir, "asset_references.json"), "w") as file:
            file.write("not json")

        prev_parameters, prev_references = submitter.get_settings_from_bundle(temp_dir)

    assert prev_parameters is None
    assert prev_references is None
