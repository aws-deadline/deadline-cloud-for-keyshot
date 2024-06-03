# AUTHOR AWS
# VERSION 0.0.6
# Submit to AWS Deadline Cloud

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import glob
import json
import os
import platform
import shlex
import subprocess
import tempfile
from typing import Optional, Tuple

import lux


def construct_job_template(filename: str) -> dict:
    return {
        "specificationVersion": "jobtemplate-2023-09",
        "name": filename,
        "parameterDefinitions": [
            {
                "name": "KeyShotFile",
                "type": "PATH",
                "objectType": "FILE",
                "dataFlow": "IN",
                "userInterface": {
                    "control": "HIDDEN",
                    "label": "KeyShot Package File",
                    "groupLabel": "KeyShot Settings",
                },
                "description": "The KeyShot package file to render.",
                "default": "",  # Workaround for https://github.com/aws-deadline/deadline-cloud/issues/343
            },
            {
                "name": "Frames",
                "type": "STRING",
                "userInterface": {
                    "control": "LINE_EDIT",
                    "label": "Frames",
                    "groupLabel": "KeyShot Settings",
                },
                "description": "The frames to render. E.g. 1-3,8,11-15",
                "minLength": 1,
            },
            {
                "name": "OutputFilePath",
                "type": "PATH",
                "objectType": "FILE",
                "dataFlow": "OUT",
                "userInterface": {
                    "control": "CHOOSE_INPUT_FILE",
                    "label": "Output File Path",
                    "groupLabel": "KeyShot Settings",
                },
                "description": "The render output path.",
            },
            {
                "name": "OutputFormat",
                "type": "STRING",
                "description": "The render output format",
                "allowedValues": [
                    "PNG",
                    "JPEG",
                    "EXR",
                    "TIFF8",
                    "TIFF32",
                    "PSD8",
                    "PSD16",
                    "PSD32",
                ],
                "default": "PNG",
                "userInterface": {
                    "control": "DROPDOWN_LIST",
                    "label": "Output Format(Must match file extension)",
                    "groupLabel": "KeyShot Settings",
                },
            },
        ],
        "steps": [
            {
                "name": "Render",
                "parameterSpace": {
                    "taskParameterDefinitions": [
                        {"name": "Frame", "type": "INT", "range": "{{Param.Frames}}"}
                    ]
                },
                "stepEnvironments": [
                    {
                        "name": "KeyShot",
                        "description": "Runs KeyShot in the background.",
                        "script": {
                            "embeddedFiles": [
                                {
                                    "name": "initData",
                                    "filename": "init-data.yaml",
                                    "type": "TEXT",
                                    "data": (
                                        "scene_file: '{{Param.KeyShotFile}}'\n"
                                        "output_file_path: '{{Param.OutputFilePath}}'\n"
                                        "output_format: 'RENDER_OUTPUT_{{Param.OutputFormat}}'\n"
                                        ""
                                    ),
                                }
                            ],
                            "actions": {
                                "onEnter": {
                                    "command": "KeyShotAdaptor",
                                    "args": [
                                        "daemon",
                                        "start",
                                        "--path-mapping-rules",
                                        "file://{{Session.PathMappingRulesFile}}",
                                        "--connection-file",
                                        "{{Session.WorkingDirectory}}/connection.json",
                                        "--init-data",
                                        "file://{{Env.File.initData}}",
                                    ],
                                    "cancelation": {"mode": "NOTIFY_THEN_TERMINATE"},
                                },
                                "onExit": {
                                    "command": "KeyShotAdaptor",
                                    "args": [
                                        "daemon",
                                        "stop",
                                        "--connection-file",
                                        "{{ Session.WorkingDirectory }}/connection.json",
                                    ],
                                    "cancelation": {"mode": "NOTIFY_THEN_TERMINATE"},
                                },
                            },
                        },
                    }
                ],
                "script": {
                    "embeddedFiles": [
                        {
                            "name": "runData",
                            "filename": "run-data.yaml",
                            "type": "TEXT",
                            "data": "frame: {{Task.Param.Frame}}\n",
                        }
                    ],
                    "actions": {
                        "onRun": {
                            "command": "KeyShotAdaptor",
                            "args": [
                                "daemon",
                                "run",
                                "--connection-file",
                                "{{ Session.WorkingDirectory }}/connection.json",
                                "--run-data",
                                "file://{{ Task.File.runData }}",
                            ],
                            "cancelation": {"mode": "NOTIFY_THEN_TERMINATE"},
                        }
                    },
                },
            }
        ],
    }


def construct_asset_references(
    input_filenames: list[str],
    input_directories: list[str],
    output_directories: list[str],
    referenced_paths: list[str],
) -> dict:
    return {
        "assetReferences": {
            "inputs": {
                "directories": sorted(input_directories),
                "filenames": sorted(input_filenames),
            },
            "outputs": {
                "directories": sorted(output_directories),
            },
            "referencedPaths": sorted(referenced_paths),
        }
    }


def construct_parameter_values(
    scene_file: str, frames: str, output_file_path: str, output_format: str
) -> dict:
    return {
        "parameterValues": [
            {"name": "KeyShotFile", "value": scene_file},
            {"name": "OutputFilePath", "value": output_file_path},
            {"name": "OutputFormat", "value": output_format},
            {"name": "Frames", "value": frames},
        ]
    }


def dump_json_to_dir(contents: dict, directory: str, filename: str) -> None:
    with open(os.path.join(directory, filename), "w") as file:
        file.write(json.dumps(contents))


def find_latest_scene_file_submission_bundle(scene_filename: str) -> Optional[str]:
    """
    Find the most recent submitted bundle that has the same name as this scene file

    Naming logic copied from the Deadline library but strips out the extension in case the user
    adds a suffix to their job names, e.g. for different parameters
    https://github.com/aws-deadline/deadline-cloud/blob/2d5f2d43f7c2adaba1f53b5b34d405b445a611c1/src/deadline/client/job_bundle/__init__.py#L38-L39
    """
    bundle_directory_name = "".join(
        char for char in scene_filename.split(".")[0] if char.isalnum() or char in " -_"
    )
    bundle_directory_name = bundle_directory_name[:128]

    matching_templates = glob.glob(
        os.path.expanduser(f"~/.deadline/job_history/*/*/*{bundle_directory_name}*/template.*")
    )

    if not matching_templates:
        return None

    # Find the most recent template with a matching scene name, including across farms. Use file ctime
    # instead of sorting based on path name because files are organized by farm before date.
    latest_template = max(matching_templates, key=os.path.getctime)
    latest_bundle, _ = os.path.split(latest_template)
    return latest_bundle


def get_settings_from_bundle(latest_bundle: str) -> Tuple[Optional[dict[str, str]], Optional[dict]]:
    parameters = None
    asset_references = None

    try:
        with open(os.path.join(latest_bundle, "parameter_values.json")) as f:
            parameter_values = json.load(f)

        parameters = {}
        for param in parameter_values.get("parameterValues", []):
            parameters[param["name"]] = param["value"]
    except FileNotFoundError:
        # No previous parameter values found, so there's nothing to load.
        pass
    except Exception as e:
        print(f"Unable to load parameter values from latest bundle {latest_bundle}: {e}")

    try:
        with open(os.path.join(latest_bundle, "asset_references.json")) as f:
            asset_references = json.load(f)["assetReferences"]
    except FileNotFoundError:
        # No previous asset refernces found, so there's nothing to load.
        pass
    except Exception as e:
        print(f"Unable to load asset references from latest bundle {latest_bundle}: {e}")

    return parameters, asset_references


def gui_submit(bundle_directory: str) -> None:
    try:
        if platform.system() == "Darwin" or platform.system() == "Linux":
            # Execute the command using an bash in interactive mode so it loads loads the bash profile to set
            # the PATH correctly. Attempting to run `deadline` directly will probably fail since Keyshot's default
            # PATH likely doesn't include the Deadline client.
            shell_executable = os.environ.get("SHELL", "/bin/bash")
            subprocess.run(
                [
                    shell_executable,
                    "-i",
                    "-c",
                    f"deadline bundle gui-submit {shlex.quote(bundle_directory)}",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            subprocess.run(
                ["deadline", "bundle", "gui-submit", str(bundle_directory)],
                check=True,
                capture_output=True,
                text=True,
            )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"AWS Deadline Cloud KeyShot submitter could not open: {e.stderr}")


def main():
    scene_file = lux.getSceneInfo()["file"]
    external_files = lux.getExternalFiles()
    current_frame = lux.getAnimationFrame()
    frame_count = lux.getAnimationInfo().get("frames")

    frames = f"1-{frame_count}" if frame_count else f"{current_frame}"
    input_filenames = [*external_files, scene_file]
    input_directories: list[str] = []
    output_directories = [str(os.path.dirname(scene_file))]
    referenced_paths: list[str] = []

    _, filename = os.path.split(scene_file)

    output_file_path = f"{scene_file}.%d.png"
    output_format = "PNG"

    latest_bundle = find_latest_scene_file_submission_bundle(filename)
    if latest_bundle:
        prev_parameters, prev_references = get_settings_from_bundle(latest_bundle)

        if prev_parameters:
            if prev_parameters.get("Frames"):
                frames = prev_parameters["Frames"]
            if prev_parameters.get("OutputFilePath"):
                output_file_path = prev_parameters["OutputFilePath"]
            if prev_parameters.get("OutputFormat"):
                output_format = prev_parameters["OutputFormat"]

        if prev_references:
            if prev_references.get("inputs", {}).get("filenames"):
                input_filenames = list(
                    set([*input_filenames, *prev_references["inputs"]["filenames"]])
                )
            if prev_references.get("inputs", {}).get("directories"):
                input_directories = list(
                    set([*input_directories, *prev_references["inputs"]["directories"]])
                )
            if prev_references.get("outputs", {}).get("directories"):
                output_directories = list(
                    set([*output_directories, *prev_references["outputs"]["directories"]])
                )
            if prev_references.get("referencedPaths"):
                referenced_paths = list(
                    set([*referenced_paths, *prev_references["referencedPaths"]])
                )

    job_template = construct_job_template(filename)
    asset_references = construct_asset_references(
        input_filenames=input_filenames,
        input_directories=input_directories,
        output_directories=output_directories,
        referenced_paths=referenced_paths,
    )
    parameter_values = construct_parameter_values(
        scene_file=scene_file,
        frames=frames,
        output_file_path=output_file_path,
        output_format=output_format,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        dump_json_to_dir(job_template, temp_dir, "template.json")
        dump_json_to_dir(asset_references, temp_dir, "asset_references.json")
        dump_json_to_dir(parameter_values, temp_dir, "parameter_values.json")

        gui_submit(temp_dir)


if __name__ == "__main__":
    main()
