# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
import json

RENDER_SUBMITTER_SETTINGS_FILE_EXT = ".deadline_render_settings.json"


@dataclass
class RenderSubmitterUISettings:
    """
    Settings that the submitter UI will use
    """

    submitter_name: str = field(default="KeyShot")

    name: str = field(default="", metadata={"sticky": True})
    description: str = field(default="", metadata={"sticky": True})

    override_frame_range: bool = field(default=False, metadata={"sticky": True})
    frame_list: str = field(default="", metadata={"sticky": True})
    output_name: str = field(default="", metadata={"sticky": True})
    output_folder: str = field(default="", metadata={"sticky": True})
    output_format: str = field(default="", metadata={"sticky": True})
    output_file_path: str = field(default="", metadata={"sticky": True})

    input_filenames: list[str] = field(default_factory=list, metadata={"sticky": True})
    input_directories: list[str] = field(default_factory=list, metadata={"sticky": True})
    output_directories: list[str] = field(default_factory=list, metadata={"sticky": True})

    include_alpha: bool = field(default=False, metadata={"sticky": True})
    render_layers: bool = field(default=False, metadata={"sticky": True})

    # developer options
    include_adaptor_wheels: bool = field(default=False, metadata={"sticky": True})

    def load_sticky_settings(self, scene_filename: str):
        sticky_settings_filename = Path(scene_filename).with_suffix(
            RENDER_SUBMITTER_SETTINGS_FILE_EXT
        )
        if sticky_settings_filename.exists() and sticky_settings_filename.is_file():
            try:
                with open(sticky_settings_filename, encoding="utf8") as fh:
                    sticky_settings = json.load(fh)

                if isinstance(sticky_settings, dict):
                    sticky_fields = {
                        field.name: field
                        for field in dataclasses.fields(self)
                        if field.metadata.get("sticky")
                    }
                    for name, value in sticky_settings.items():
                        # Only set fields that are defined in the dataclass
                        if name in sticky_fields:
                            setattr(self, name, value)
            except (OSError, json.JSONDecodeError):
                # If something bad happened to the sticky settings file,
                # just use the defaults instead of producing an error.
                import traceback

                traceback.print_exc()
                print(
                    f"WARNING: Failed to load sticky settings file {sticky_settings_filename}, reverting to the default settings."
                )
                pass

    def save_sticky_settings(self, scene_filename: str):
        sticky_settings_filename = Path(scene_filename).with_suffix(
            RENDER_SUBMITTER_SETTINGS_FILE_EXT
        )
        with open(sticky_settings_filename, "w", encoding="utf8") as fh:
            obj = {
                field.name: getattr(self, field.name)
                for field in dataclasses.fields(self)
                if field.metadata.get("sticky")
            }
            json.dump(obj, fh, indent=1)


@dataclass
class KeyShotOutputFormat:
    """
    Mapping between the display name on the submitter UI, the file extension
    to use for the output file, and the name of the KeyShot scripting property
    used to lookup the numeric code needed to set the output format in the call
    to lux.renderImage()
    """

    display_name: str
    file_extension: str
    keyshot_property_name: str
