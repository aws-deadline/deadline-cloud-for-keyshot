# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from __future__ import annotations

import os as os
from pprint import pprint
from typing import Any, Callable, Dict

try:
    import lux  # type: ignore
except ImportError:  # pragma: no cover
    raise OSError("Could not find the KeyShot module. Are you running this inside of KeyShot?")


class KeyShotHandler:
    action_dict: Dict[str, Callable[[Dict[str, Any]], None]] = {}
    render_kwargs: Dict[str, Any]

    def __init__(self) -> None:
        """
        Constructor for the keyshot -headless handler. Initializes action_dict and render variables
        """
        self.action_dict = {
            "scene_file": self.set_scene_file,
            "output_file_path": self.set_output_file_path,
            "output_format": self.set_output_format,
            "frame": self.set_frame,
            "start_render": self.start_render,
        }
        self.render_kwargs = {}
        self.output_path = ""
        self.output_format_code = lux.RENDER_OUTPUT_PNG  # Default to PNG

    def set_output_file_path(self, data: dict) -> None:
        """
        Sets the output file path.

        Args:
            data (dict): The data given from the Adaptor. Keys expected: ['output_file_path']
        """
        render_dir = data.get("output_file_path")
        if render_dir:
            self.output_path = render_dir

    def start_render(self, data: dict) -> None:
        """
        Call the "Render Image" command

        Args:
            data (dict):

        Raises:
            RuntimeError: .
        """
        print("Starting Render...")
        frame = self.render_kwargs["frame"]
        opts = lux.getRenderOptions()
        opts.setAddToQueue(False)
        lux.setAnimationFrame(frame)
        output_path = self.output_path.replace("%d", str(frame))
        pprint(f"KeyShot Render Options: {opts}", indent=4)
        print(f"KeyShot Render Output Format: {self.output_format_code}")
        lux.renderImage(path=output_path, opts=opts, format=self.output_format_code)
        print(f"Finished Rendering {output_path}")

    def set_output_format(self, data: dict) -> None:
        """
        Sets the output format for the render

        Args:
            data (dict):

        Raises:
            RuntimeError: If the output format does not exist for KeyShot or if
                          called without an output_format set
        """
        if "output_format" in data:
            output_format = data["output_format"]
            try:
                self.output_format_code = getattr(lux, output_format)
            except AttributeError:
                raise RuntimeError(
                    f"The output format {output_format} is not valid. Valid formats are defined in the init data schema file."
                )
        else:
            raise RuntimeError("set_output_format called without an output_format specified.")

    def set_frame(self, data: dict) -> None:
        """
        Sets the frame to render

        Args:
            data (dict):

        """
        self.render_kwargs["frame"] = int(data.get("frame", ""))

    def set_scene_file(self, data: dict) -> None:
        """
        Opens the scene file in KeyShot.

        Args:
            data (dict): The data given from the Adaptor. Keys expected: ['scene_file']

        Raises:
            FileNotFoundError: If path to the scene file does not yield a file
        """
        scene_file = data.get("scene_file", "")
        print("scene_file", scene_file)
        if not os.path.isfile(scene_file):
            raise FileNotFoundError(f"The scene file '{scene_file}' does not exist")
        lux.openFile(scene_file)
