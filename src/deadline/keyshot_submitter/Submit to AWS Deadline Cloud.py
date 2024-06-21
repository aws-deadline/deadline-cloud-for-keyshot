# AUTHOR AWS
# VERSION 0.0.6
# Submit to AWS Deadline Cloud

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from dataclasses import dataclass
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import tempfile
from typing import Any, Optional

import lux

RENDER_SUBMITTER_SETTINGS_FILE_EXT = ".deadline_render_settings.json"


@dataclass
class Settings:
    scene_file: str
    frames: str
    output_file_path: str
    output_format: str
    input_filenames: list[str]
    input_directories: list[str]
    output_directories: list[str]
    referenced_paths: list[str]
    auto_detected_input_filenames: list[str]
    auto_detected_output_directories: list[str]

    def to_dict(self):
        return {
            "frames": self.frames,
            "outputFilePath": self.output_file_path,
            "outputFormat": self.output_format,
            "inputFilenames": self.input_filenames,
            "inputDirectories": self.input_directories,
            "outputDirectories": self.output_directories,
            "referencedPaths": self.referenced_paths,
            # Do not include auto-detected inputs and outputs since they should not be sticky
        }

    def apply_sticky_settings(self, sticky_settings: dict):
        self.frames = sticky_settings.get("frames", self.frames)
        self.output_file_path = sticky_settings.get("outputFilePath", self.output_file_path)
        self.output_format = sticky_settings.get("outputFormat", self.output_format)
        self.input_filenames = sticky_settings.get("inputFilenames", self.input_filenames)
        self.input_directories = sticky_settings.get("inputDirectories", self.input_directories)
        self.output_directories = sticky_settings.get("outputDirectories", self.output_directories)
        self.referenced_paths = sticky_settings.get("referencedPaths", self.referenced_paths)

    def apply_submitter_settings(self, output: dict):
        parameters: dict[str, str] = {}
        for parameter in output.get("parameterValues", []):
            parameters[parameter["name"]] = parameter["value"]

        if parameters.get("Frames"):
            self.frames = parameters["Frames"]
        if parameters.get("OutputFilePath"):
            self.output_file_path = parameters["OutputFilePath"]
        if parameters.get("OutputFormat"):
            self.output_format = parameters["OutputFormat"]
        if parameters.get("Frames"):
            self.frames = parameters["Frames"]
        if output.get("assetReferences", {}).get("inputs", {}).get("filenames"):
            # Persist input files that were not autodetected (i.e. were manually added)
            self.input_filenames = list(
                set(output["assetReferences"]["inputs"]["filenames"])
                - set(self.auto_detected_input_filenames)
            )
        if output.get("assetReferences", {}).get("inputs", {}).get("directories"):
            self.input_directories = output["assetReferences"]["inputs"]["directories"]
        if output.get("assetReferences", {}).get("outputs", {}).get("directories"):
            # Persist output directories that were not autodetected (i.e. were manually added)
            self.output_directories = list(
                set(output["assetReferences"]["outputs"]["directories"])
                - set(self.auto_detected_output_directories)
            )
        if output.get("assetReferences", {}).get("referencedPaths"):
            self.referenced_paths = output["assetReferences"]["referencedPaths"]


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


def construct_asset_references(settings: Settings) -> dict:
    return {
        "assetReferences": {
            "inputs": {
                "directories": sorted(settings.input_directories),
                "filenames": sorted(
                    list(set([*settings.input_filenames, *settings.auto_detected_input_filenames]))
                ),
            },
            "outputs": {
                "directories": sorted(
                    list(
                        set(
                            [
                                *settings.output_directories,
                                *settings.auto_detected_output_directories,
                            ]
                        )
                    )
                ),
            },
            "referencedPaths": sorted(settings.referenced_paths),
        }
    }


def construct_parameter_values(settings: Settings) -> dict:
    return {
        "parameterValues": [
            {"name": "KeyShotFile", "value": settings.scene_file},
            {"name": "OutputFilePath", "value": settings.output_file_path},
            {"name": "OutputFormat", "value": settings.output_format},
            {"name": "Frames", "value": settings.frames},
        ]
    }


def dump_json_to_dir(contents: dict, directory: str, filename: str) -> None:
    with open(os.path.join(directory, filename), "w") as file:
        file.write(json.dumps(contents))


def load_sticky_settings(scene_filename: str) -> Optional[dict]:
    sticky_settings_filename = Path(scene_filename).with_suffix(RENDER_SUBMITTER_SETTINGS_FILE_EXT)
    if sticky_settings_filename.exists() and sticky_settings_filename.is_file():
        try:
            with open(sticky_settings_filename, encoding="utf8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            # Fall back to defaults if there's an error loading sticky settings
            import traceback

            traceback.print_exc()
            print(
                f"WARNING: Failed to load {sticky_settings_filename}. Reverting to the default settings."
            )
            pass
    return None


def save_sticky_settings(scene_file: str, settings: Settings):
    sticky_settings_filename = Path(scene_file).with_suffix(RENDER_SUBMITTER_SETTINGS_FILE_EXT)
    with open(sticky_settings_filename, "w", encoding="utf8") as f:
        json.dump(settings.to_dict(), f, indent=2)


def gui_submit(bundle_directory: str) -> Optional[dict[str, Any]]:
    try:
        if platform.system() == "Darwin" or platform.system() == "Linux":
            # Execute the command using an bash in interactive mode so it loads loads the bash profile to set
            # the PATH correctly. Attempting to run `deadline` directly will probably fail since Keyshot's default
            # PATH likely doesn't include the Deadline client.
            shell_executable = os.environ.get("SHELL", "/bin/bash")
            result = subprocess.run(
                [
                    shell_executable,
                    "-i",
                    "-c",
                    f'echo "START_DEADLINE_OUTPUT";deadline bundle gui-submit {shlex.quote(bundle_directory)} --output json --extra-info',
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            # Hack to ignore any output from the bash profile script
            output = result.stdout.split("START_DEADLINE_OUTPUT")[-1]
        else:
            result = subprocess.run(
                [
                    "deadline",
                    "bundle",
                    "gui-submit",
                    str(bundle_directory),
                    "--output",
                    "json",
                    "--extra-info",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            output = result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"AWS Deadline Cloud KeyShot submitter could not open: {e.stderr}")
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        print(f"Error parsing settings file: {e}")
        return None


def main():
    scene_file = lux.getSceneInfo()["file"]
    external_files = lux.getExternalFiles()
    current_frame = lux.getAnimationFrame()
    frame_count = lux.getAnimationInfo().get("frames")

    settings = Settings(
        scene_file=scene_file,
        frames=f"1-{frame_count}" if frame_count else f"{current_frame}",
        input_filenames=[],
        auto_detected_input_filenames=[*external_files, scene_file],
        input_directories=[],
        output_directories=[],
        auto_detected_output_directories=[str(os.path.dirname(scene_file))],
        referenced_paths=[],
        output_file_path=f"{scene_file}.%d.png",
        output_format="PNG",
    )

    _, filename = os.path.split(scene_file)

    sticky_settings = load_sticky_settings(scene_file)
    if sticky_settings:
        settings.apply_sticky_settings(sticky_settings)

    job_template = construct_job_template(filename)
    asset_references = construct_asset_references(settings)
    parameter_values = construct_parameter_values(settings)

    with tempfile.TemporaryDirectory() as temp_dir:
        dump_json_to_dir(job_template, temp_dir, "template.json")
        dump_json_to_dir(asset_references, temp_dir, "asset_references.json")
        dump_json_to_dir(parameter_values, temp_dir, "parameter_values.json")

        output = gui_submit(temp_dir)

    if output:
        settings.apply_submitter_settings(output)
        save_sticky_settings(scene_file, settings)


if __name__ == "__main__":
    main()
