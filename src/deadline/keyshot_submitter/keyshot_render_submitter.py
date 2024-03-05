# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import os
import json
from pathlib import Path
from typing import Any, Optional
import yaml  # type: ignore[import]
from copy import deepcopy

from PySide2 import QtWidgets

from deadline.client.job_bundle.submission import AssetReferences
from deadline.client.job_bundle._yaml import deadline_yaml_dump
from deadline.client.ui.dialogs.submit_job_to_deadline_dialog import (  # pylint: disable=import-error
    SubmitJobToDeadlineDialog,
    JobBundlePurpose,
)
from deadline.client.exceptions import DeadlineOperationError
from PySide2.QtCore import Qt  # pylint: disable=import-error

from .data_classes import (
    RenderSubmitterUISettings,
)
from .ui.components.scene_settings_tab import SceneSettingsWidget
from ._version import version_tuple as adaptor_version_tuple


def show_submitter(info_file):
    if not os.path.exists(info_file):
        raise Exception("info file not found: %s" % info_file)
    with open(info_file) as f:
        lux_data = json.load(f)
    try:
        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication([])
            app.setQuitOnLastWindowClosed(False)
            app.aboutToQuit.connect(app.deleteLater)
        w = _show_submitter(lux_data)
        w.exec_()
    except Exception:
        print("Deadline UI launch failed")
        import traceback

        traceback.print_exc()


def _get_parameter_values(
    settings: RenderSubmitterUISettings,
    queue_parameters: list[dict[str, Any]],
    frames: str,
    scene_name: str,
) -> list[dict[str, Any]]:
    parameter_values: list[dict[str, Any]] = []

    # Set the scene file value
    parameter_values.append({"name": "KeyShotFile", "value": scene_name})

    # Output
    parameter_values.append({"name": "OutputFilePath", "value": settings.output_file_path})
    parameter_values.append({"name": "OutputFormat", "value": settings.output_format})

    if settings.override_frame_range:
        frame_list = settings.frame_list
    else:
        frame_list = frames
    parameter_values.append({"name": "Frames", "value": frame_list})

    # Check for any overlap between the job parameters we've defined and the
    # queue parameters. This is an error, as we weren't synchronizing the values
    # between the two different tabs where they came from.
    parameter_names = {param["name"] for param in parameter_values}
    queue_parameter_names = {param["name"] for param in queue_parameters}
    parameter_overlap = parameter_names.intersection(queue_parameter_names)
    if parameter_overlap:
        raise DeadlineOperationError(
            "The following queue parameters conflict with the keyshot job parameters:\n"
            + f"{', '.join(parameter_overlap)}"
        )

    parameter_values.extend(
        {"name": param["name"], "value": param["value"]} for param in queue_parameters
    )

    return parameter_values


def _get_job_template(
    default_job_template: dict[str, Any], settings: RenderSubmitterUISettings
) -> dict[str, Any]:
    job_template = deepcopy(default_job_template)

    # Set the job's name
    job_template["name"] = settings.name

    # Replicate the default step, once per render take, and adjust its settings
    default_step = job_template["steps"][0]
    job_template["steps"] = []

    step = deepcopy(default_step)
    job_template["steps"].append(step)

    step["name"] = "Render"

    return job_template


def _show_submitter(data, parent=None, f=Qt.WindowFlags()):
    with open(Path(__file__).parent / "adaptor_keyshot_job_template.yaml") as fh:
        default_job_template = yaml.safe_load(fh)

    render_settings = RenderSubmitterUISettings()
    keyshot_version: str = data["version"]
    scene_name = data["scene"]["file"]
    if data["animation"].get("frames", None):
        frames = "%s-%s" % (1, data["animation"]["frames"])
    else:
        frames = "%s" % data["frame"]

    # Set the setting defaults that come from the scene
    render_settings.output_folder = str(Path(scene_name).parent)
    render_settings.output_name = data["scene"]["name"]
    render_settings.name = Path(scene_name).name
    render_settings.frame_list = frames

    # Load the sticky settings
    render_settings.load_sticky_settings(scene_name)

    def on_create_job_bundle_callback(
        widget: SubmitJobToDeadlineDialog,
        job_bundle_dir: str,
        settings: RenderSubmitterUISettings,
        queue_parameters: list[dict[str, Any]],
        asset_references: AssetReferences,
        host_requirements: Optional[dict[str, Any]] = None,
        purpose: JobBundlePurpose = JobBundlePurpose.SUBMISSION,
    ) -> None:
        job_bundle_path = Path(job_bundle_dir)

        job_template = _get_job_template(
            default_job_template,
            settings,
        )
        parameter_values = _get_parameter_values(settings, queue_parameters, frames, scene_name)

        # If "HostRequirements" is provided, inject it into each of the "Step"
        if host_requirements:
            # for each step in the template, append the same host requirements.
            for step in job_template["steps"]:
                step["hostRequirements"] = host_requirements

        with open(job_bundle_path / "template.yaml", "w", encoding="utf8") as f:
            deadline_yaml_dump(job_template, f, indent=1)

        with open(job_bundle_path / "parameter_values.yaml", "w", encoding="utf8") as f:
            deadline_yaml_dump({"parameterValues": parameter_values}, f, indent=1)

        with open(job_bundle_path / "asset_references.yaml", "w", encoding="utf8") as f:
            deadline_yaml_dump(asset_references.to_dict(), f, indent=1)

        # Save Sticky Settings
        attachments: AssetReferences = widget.job_attachments.attachments
        settings.input_filenames = sorted(attachments.input_filenames)
        settings.input_directories = sorted(attachments.input_directories)
        settings.input_filenames = sorted(attachments.input_filenames)

        settings.save_sticky_settings(scene_name)

    auto_detected_attachments = AssetReferences()
    auto_detected_attachments.input_filenames.add(scene_name)
    auto_detected_attachments.input_filenames.update(data["files"])

    attachments = AssetReferences(
        input_filenames=set(render_settings.input_filenames),
        input_directories=set(render_settings.input_directories),
        output_directories=set(render_settings.output_directories),
    )

    keyshot_major_version: str = keyshot_version.split(".")[0]
    adaptor_version: str = ".".join(str(v) for v in adaptor_version_tuple[:2])
    conda_packages: str = f"keyshot={keyshot_major_version}.* keyshot-openjd={adaptor_version}.*"

    submitter_dialog = SubmitJobToDeadlineDialog(
        job_setup_widget_type=SceneSettingsWidget,
        initial_job_settings=render_settings,
        initial_shared_parameter_values={
            "CondaPackages": conda_packages,
        },
        auto_detected_attachments=auto_detected_attachments,
        attachments=attachments,
        on_create_job_bundle_callback=on_create_job_bundle_callback,
        parent=parent,
        f=f,
        show_host_requirements_tab=True,
    )

    return submitter_dialog
