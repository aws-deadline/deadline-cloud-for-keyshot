# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import json
import os
import re
import subprocess
from difflib import unified_diff
from pathlib import Path

from .image_comparison import assert_all_images_close

DIR_NAME_FOR_EXPECTED_BUNDLE = "expected_bundle"
DIR_NAME_FOR_ACTUAL_BUNDLE = "actual_bundle"
DIR_NAME_FOR_EXPECTED_OUTPUT_IMAGES = "expected_output"
DIR_NAME_FOR_ACTUAL_OUTPUT_IMAGES = "actual_output"


def run_keyshot_test(
    keyshot_location: Path,
    test_scene_location: Path,
) -> None:
    bundle_output_location = test_scene_location / DIR_NAME_FOR_ACTUAL_BUNDLE
    run_keyshot_submitter_test(keyshot_location, test_scene_location, bundle_output_location)
    run_keyshot_adaptor_test(test_scene_location, bundle_output_location)


def run_keyshot_submitter_test(
    keyshot_location: Path,
    test_scene_location: Path,
    bundle_output_location: Path,
) -> None:
    args = [
        str(keyshot_location),
        "-floating_feature",
        "keyshot2",
        "-script",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "submitter_test.py")),
        "--scene-location",
        os.path.abspath(os.path.join(test_scene_location)),
        "--output-location",
        os.path.abspath(os.path.join(bundle_output_location)),
    ]

    output = run_command(args)

    assert output.returncode == 0
    assert is_valid_template(bundle_output_location / "template.json")

    assert_expected_job_bundle_and_generated_job_bundle_are_equal(
        test_scene_location / DIR_NAME_FOR_EXPECTED_BUNDLE, bundle_output_location
    )


def run_keyshot_adaptor_test(
    test_scene_location: Path,
    bundle_location: Path,
) -> None:
    # TODO: run output job bundle used keyshot-openjd
    template_path = bundle_location / "template.json"
    output_path = test_scene_location / DIR_NAME_FOR_ACTUAL_OUTPUT_IMAGES

    with open(template_path, "r") as f:
        content = f.read().replace("progressive_max_samples: 0", "progressive_max_samples: 1000")

    with open(template_path, "w") as f:
        f.write(content)

    with open(template_path, "r") as f:
        template = json.loads(f.read())

    job_params = {}
    with open(bundle_location / "parameter_values.json") as f:
        for param in json.loads(f.read())["parameterValues"]:
            if param["name"] == "OutputFilePath":
                original_output_path = Path(param["value"])
                param["value"] = str(output_path / original_output_path.name)
            job_params[param["name"]] = param["value"]

    # these are queue env params
    job_params.pop("CondaChannels", None)
    job_params.pop("CondaPackages", None)

    paths_to_add_to_deadline_cloud_pythonpath = [
        str(Path(__file__).parent.parent.parent.parent / "src"),  # deadline import
    ]
    if "VIRTUAL_ENV" in os.environ:
        # VIRTUAL_ENV env var comes from hatch env
        paths_to_add_to_deadline_cloud_pythonpath.append(
            str(
                Path(os.environ["VIRTUAL_ENV"]).parent / "integ" / "Lib" / "site-packages"
            )  # openjd import
        )

    os.environ["DEADLINE_CLOUD_PYTHONPATH"] = os.pathsep.join(
        paths_to_add_to_deadline_cloud_pythonpath
    )

    for step in template["steps"]:
        output = run_command(
            [
                "openjd",
                "run",
                str(template_path),
                "--step",
                step["name"],
                "--job-param",
                json.dumps(job_params),
            ]
        )
        assert output.returncode == 0

    assert_all_images_close(
        expected_image_directory=test_scene_location / DIR_NAME_FOR_EXPECTED_OUTPUT_IMAGES,
        actual_image_directory=test_scene_location / DIR_NAME_FOR_ACTUAL_OUTPUT_IMAGES,
    )
    assert os.path.isfile(output_path / "scene.0.png")


def run_command(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    output = subprocess.run(args, capture_output=True, check=False)

    print(f"Ran the following: {' '.join(output.args)}")
    print(f"\nstdout:\n\n{output.stdout.decode('utf-8', errors='replace')}")
    print(f"\nstderr:\n\n{output.stderr.decode('utf-8', errors='replace')}")

    return output


def is_valid_template(template_location: Path) -> bool:
    output = run_command(["openjd", "check", str(template_location), "--output", "json"])
    output_json = json.loads(output.stdout)
    return output_json["status"] == "success"


def assert_expected_job_bundle_and_generated_job_bundle_are_equal(
    expected_job_bundle_dir_path: Path, generated_job_bundle_dir_path: Path
) -> None:
    """
    Assert that the generated job bundle matches with the expected job bundle.
    """

    results: dict[str, list[str]] = {
        "different_content": [],
        "identical_files": [],
    }

    # So that we can replace PATH_TO_BE_REPLACED in the expected job bundle.
    prefix_path = os.path.abspath(expected_job_bundle_dir_path).split("deadline-cloud-for-keyshot")[
        0
    ]

    # Get list of files in both directories
    expected_job_bundle_files = set(
        f.name for f in expected_job_bundle_dir_path.glob("*") if f.is_file()
    )
    generated_job_bundle_files = set(
        f.name for f in generated_job_bundle_dir_path.glob("*") if f.is_file()
    )
    # Compare contents of files that exist in both directories
    common_files = expected_job_bundle_files.intersection(generated_job_bundle_files)

    for file in common_files:
        file1_path = expected_job_bundle_dir_path / file
        file2_path = generated_job_bundle_dir_path / file

        # Read files and compare their contents directly
        with open(file1_path, encoding="utf-8") as f1, open(file2_path, encoding="utf-8") as f2:
            content1 = f1.read().strip()  # strip() removes trailing whitespace
            content2 = f2.read().strip()

            # Normalize line endings
            content1 = content1.replace("\r\n", "\n")
            content2 = content2.replace("\r\n", "\n")

            # Replace the prefix path in the generated job bundle files.
            content1 = content1.replace("PATH_TO_BE_REPLACED", prefix_path)
            content1 = replace_backslashes(content1)
            content2 = replace_backslashes(content2)
            if file == "parameter_values.json":
                # generalize to all versions of KeyShot and the adaptor
                content2 = re.sub(
                    r"keyshot=202[3-9].\* keyshot-openjd=0.\d.\*",
                    "keyshot=2024.* keyshot-openjd=0.4.*",
                    content2,
                )

            content1_loaded = json.loads(content1)
            content2_loaded = json.loads(content2)

            if content1_loaded == content2_loaded:
                results["identical_files"].append(file)
            else:
                results["different_content"].append(file)
                diff = "\n".join(
                    unified_diff(content1.splitlines(), content2.splitlines(), lineterm="")
                )
                print(diff)

    assert len(results["different_content"]) == 0
    assert len(results["identical_files"]) == 3
    assert "template.json" in results["identical_files"]
    assert "parameter_values.json" in results["identical_files"]
    assert "asset_references.json" in results["identical_files"]


def replace_backslashes(content: str) -> str:
    """
    Replaces backslashes that are path separators.
    Note: This also preserves the backslashes in unicode characters.
    """
    content = re.sub(
        r"\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2})", r"UNICODE_ESCAPE\1", content
    )  # To avoid unicode '\' getting replaced
    content = re.sub(r"\\+", "/", content)
    content = content.replace("UNICODE_ESCAPE", "\\")  # Add unicode escape back
    return content
