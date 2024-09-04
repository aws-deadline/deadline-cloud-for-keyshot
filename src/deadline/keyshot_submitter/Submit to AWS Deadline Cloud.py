# AUTHOR AWS
# VERSION 0.2.0
# Submit to AWS Deadline Cloud

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import json
import os
import platform
import subprocess
import tempfile
import glob
from dataclasses import dataclass
from typing import Any, Optional, Tuple

import lux

RENDER_SUBMITTER_SETTINGS_FILE_EXT = ".deadline_render_settings.json"
SUBMISSION_MODE_KEY = "submission_mode"
# Unique ID required to allow KeyShot to save selections for a dialog
DEADLINE_CLOUD_DIALOG_ID = "e309ce79-3ee8-446a-8308-10d16dfcbb42"


@dataclass
class Settings:
    parameter_values: list[dict[str, Any]]  # [{"name": "my_param_name", "value": X}]
    input_filenames: list[str]
    input_directories: list[str]
    output_directories: list[str]
    referenced_paths: list[str]
    auto_detected_input_filenames: list[str]

    def output_sticky_settings(self):
        return {
            # we always use the current the KeyShotFile
            "parameterValues": [
                param for param in self.parameter_values if param["name"] != "KeyShotFile"
            ],
            "inputFilenames": self.input_filenames,
            "inputDirectories": self.input_directories,
            "outputDirectories": self.output_directories,
            "referencedPaths": self.referenced_paths,
            # Do not include auto-detected inputs and outputs since they should not be sticky
        }

    def apply_sticky_settings(self, sticky_settings: dict):
        input_parameter_values = sticky_settings.get("parameterValues", [])

        updated_parameter_values = {}

        for param in self.parameter_values:
            updated_parameter_values[param["name"]] = param["value"]

        for param in input_parameter_values:
            if param.get("name") and param.get("value"):
                # Don't re-use KeyShotFile param if the render settings are copied from one file to another
                # Don't preserve conda settings so the Keyshot version can be updated by updating the submitter
                if param["name"] in ["KeyShotFile", "CondaPackages", "CondaChannels"]:
                    continue
                updated_parameter_values[param["name"]] = param["value"]

        self.parameter_values = [
            {"name": parameter_name, "value": updated_parameter_values[parameter_name]}
            for parameter_name in updated_parameter_values
        ]

        self.input_filenames = sticky_settings.get("inputFilenames", self.input_filenames)
        self.input_directories = sticky_settings.get("inputDirectories", self.input_directories)
        self.output_directories = sticky_settings.get("outputDirectories", self.output_directories)
        self.referenced_paths = sticky_settings.get("referencedPaths", self.referenced_paths)

    def apply_submitter_settings(self, output: dict):
        job_bundle_history_dir = output.get("jobHistoryBundleDirectory")
        if not job_bundle_history_dir:
            return
        with open(
            os.path.join(job_bundle_history_dir, "parameter_values.json")
        ) as parameter_values_file:
            self.parameter_values = json.load(parameter_values_file).get("parameterValues", [])
        with open(
            os.path.join(job_bundle_history_dir, "asset_references.json")
        ) as asset_references_file:
            asset_references_contents = json.load(asset_references_file)
        asset_references = asset_references_contents.get("assetReferences", {})

        if asset_references.get("inputs", {}).get("filenames"):
            # Persist input files that were not autodetected (i.e. were manually added)
            self.input_filenames = list(
                set(asset_references["inputs"]["filenames"])
                - set(self.auto_detected_input_filenames)
            )
        if asset_references.get("inputs", {}).get("directories"):
            self.input_directories = asset_references["inputs"]["directories"]
        if asset_references.get("outputs", {}).get("directories"):
            self.output_directories = asset_references["outputs"]["directories"]
        if asset_references.get("referencedPaths"):
            self.referenced_paths = asset_references["referencedPaths"]


def construct_job_template(filename: str) -> dict:
    """
    Constructs and returns a dict containing a valid job template for the KeyShot job.
    The return value is safe to convert/dump to JSON or YAML.
    """
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
                    "control": "CHOOSE_OUTPUT_FILE",
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
    """
    Constructs and returns the asset references in a dict that is safe to convert/dump to JSON or YAML.
    """
    return {
        "assetReferences": {
            "inputs": {
                "directories": sorted(settings.input_directories),
                "filenames": sorted(
                    list(set([*settings.input_filenames, *settings.auto_detected_input_filenames]))
                ),
            },
            "outputs": {"directories": sorted(settings.output_directories)},
            "referencedPaths": sorted(settings.referenced_paths),
        }
    }


def construct_parameter_values(settings: Settings) -> dict:
    """
    Constructs and returns the parameter values in a dict that is safe to convert/dump to JSON or YAML.
    """
    return {
        "parameterValues": settings.parameter_values,
    }


def dump_json_to_dir(contents: dict, directory: str, filename: str) -> None:
    with open(os.path.join(directory, filename), "w") as file:
        file.write(json.dumps(contents))


def substitute_suffix(path: str, suffix: str) -> str:
    root, _ext = os.path.splitext(path)
    return root + suffix


def load_sticky_settings(scene_filename: str) -> Optional[dict]:
    sticky_settings_filename = substitute_suffix(scene_filename, RENDER_SUBMITTER_SETTINGS_FILE_EXT)
    if os.path.exists(sticky_settings_filename) and os.path.isfile(sticky_settings_filename):
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
    return None


def save_sticky_settings(scene_file: str, settings: Settings):
    sticky_settings_filename = substitute_suffix(scene_file, RENDER_SUBMITTER_SETTINGS_FILE_EXT)
    with open(sticky_settings_filename, "w", encoding="utf8") as f:
        json.dump(settings.output_sticky_settings(), f, indent=2)


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
                    f"echo \"START_DEADLINE_OUTPUT\";deadline bundle gui-submit '{bundle_directory}' --output json",
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
                ],
                check=True,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
            )
            output = result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"AWS Deadline Cloud KeyShot submitter could not open: {e.stderr}")
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        print(f"Error parsing deadline CLI output as json: {e}")
        return None


def options_dialog() -> dict[str, Any]:
    """
    Builds and displays a dialog within KeyShot to get the submission options
    reuired before the main gui submission window is opened outside of KeyShot.
    Options:
        Option 1: Dropdown to select whether to submit just the scene file itself
                  or all external file references as well by packing/unpacking a
                  KSP bundle before submission.
    Returns a dictionary of the selected option values in the format:
        {'SUBMISSION_MODE_KEY': [1, 'only the scene BIP file']}
    """
    dialog_items = [
        (
            SUBMISSION_MODE_KEY,
            lux.DIALOG_ITEM,
            "What files would you like to attach to the job?",
            0,
            ["The scene BIP file and all external files references", "Only the scene BIP file"],
        )
    ]
    selections = lux.getInputDialog(
        title="AWS Deadline Cloud Submission Options",
        values=dialog_items,
        id=DEADLINE_CLOUD_DIALOG_ID,
    )

    return selections


def save_ksp_bundle(directory: str, bundle_name: str) -> str:
    """
    Saves out the current scene and any file references to a ksp bundle in a
    directory.
    Returns the file path where the bundle was saved to.
    """
    full_ksp_path = os.path.join(directory, bundle_name)

    if not lux.savePackage(path=full_ksp_path):
        raise RuntimeError("KSP was not able to be saved!")

    return full_ksp_path


def get_ksp_bundle_files(directory: str) -> Tuple[str, list[str]]:
    """
    Creates a ksp bundle from the current scene containing the scene file and
    any external file references. The bundle is unpacked into a directory passed
    in.
    Returns the scene file and a list of the external files from the directory
    where the ksp was extracted to.
    """

    ksp_dir = os.path.join(directory, "ksp")
    unpack_dir = os.path.join(directory, "unpack")
    ksp_archive = save_ksp_bundle(ksp_dir, "temp_deadline_cloud.zip")
    if platform.system() == "Darwin" or platform.system() == "Linux":
        subprocess.run(
            ["unzip", ksp_archive, "-d", unpack_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    else:
        subprocess.run(
            [
                "PowerShell",
                "-Command",
                '$ProgressPreference = "SilentlyContinue"',  # don't display progress bar, up to 4x speedup
                ";",
                "Expand-Archive",
                "-Path",
                ksp_archive,
                "-DestinationPath",
                unpack_dir,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    input_filenames = [
        os.path.join(unpack_dir, file)
        for file in os.listdir(unpack_dir)
        if not file.endswith(".bip")
    ]

    bip_files = glob.glob(os.path.join(unpack_dir, "*.bip"))

    if not bip_files:
        raise RuntimeError("No .bip files found in the KSP bundle.")
    elif len(bip_files) > 1:
        raise RuntimeError("Multiple .bip files found in the KSP bundle.")

    bip_file = bip_files[0]

    return bip_file, input_filenames


def main(lux):
    if lux.isSceneChanged():
        result = lux.getInputDialog(
            title="Unsaved changes",
            values=[(lux.DIALOG_LABEL, "You have unsaved changes. Do you want to save your file?")],
        )
        # result is {} if the user clicks Ok and None if the user clicks cancel
        if result is None:
            # Raise an exception so Keyshot shows the script's result status as "Failure" instead of "Success"
            raise Exception("Changes must be saved before submitting.")
        else:
            lux.saveFile()

    dialog_selections = options_dialog()

    if not dialog_selections:
        # Dialog was canceled. Raise an exception so Keyshot does not show the script's result status as "Success"
        raise Exception("Submission was canceled.")

    scene_info = lux.getSceneInfo()
    scene_file = scene_info["file"]
    scene_name, _ = os.path.splitext(scene_info["name"])
    current_frame = lux.getAnimationFrame()
    frame_count = lux.getAnimationInfo().get("frames")

    settings = Settings(
        parameter_values=[
            {
                "name": "Frames",
                "value": f"1-{frame_count}" if frame_count else f"{current_frame}",
            },
            {
                "name": "OutputFilePath",
                "value": os.path.join(os.path.dirname(scene_file), f"{scene_name}.%d.png"),
            },
            {
                "name": "OutputFormat",
                "value": "PNG",
            },
        ],
        input_filenames=[],
        auto_detected_input_filenames=[],
        input_directories=[],
        output_directories=[],
        referenced_paths=[],
    )

    sticky_settings = load_sticky_settings(scene_file)
    if sticky_settings:
        settings.apply_sticky_settings(sticky_settings)

    with tempfile.TemporaryDirectory() as bundle_temp_dir:
        # {'submission_mode': [0, 'the scene BIP file and all external files references']}
        if not dialog_selections[SUBMISSION_MODE_KEY][0]:
            temp_scene_file, input_filenames = get_ksp_bundle_files(bundle_temp_dir)
            settings.auto_detected_input_filenames = input_filenames
            settings.parameter_values.append({"name": "KeyShotFile", "value": temp_scene_file})
        else:
            settings.parameter_values.append({"name": "KeyShotFile", "value": scene_file})

        # Add default values for Conda
        major_version, minor_version = lux.getKeyShotDisplayVersion()
        settings.parameter_values.append(
            {"name": "CondaPackages", "value": f"keyshot={major_version}.* keyshot-openjd=0.2.*"}
        )
        settings.parameter_values.append({"name": "CondaChannels", "value": "deadline-cloud"})

        job_template = construct_job_template(scene_name)
        asset_references = construct_asset_references(settings)
        parameter_values = construct_parameter_values(settings)

        dump_json_to_dir(job_template, bundle_temp_dir, "template.json")
        dump_json_to_dir(asset_references, bundle_temp_dir, "asset_references.json")
        dump_json_to_dir(parameter_values, bundle_temp_dir, "parameter_values.json")

        output = gui_submit(bundle_temp_dir)

    if output:
        if output.get("status") == "CANCELED":
            # Raise an exception so Keyshot does not show the script's result status as "Success"
            raise Exception("Submission was canceled.")

        settings.apply_submitter_settings(output)
        save_sticky_settings(scene_file, settings)


if __name__ == "__main__":
    main(lux)
