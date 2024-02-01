# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from __future__ import annotations

import os as os
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
            "frame": self.set_frame,
            "start_render": self.start_render,
        }
        self.render_kwargs = {}
        self.output_path = ""

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
        lux.renderImage(path=output_path, opts=opts)
        print("Finished Rendering %s" % output_path)

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
