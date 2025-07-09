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
            "render_options": self.set_render_options,
            "override_render_device": self.set_override_render_device,
            "render_device": self.set_render_device,
            "start_render": self.start_render,
        }
        self.render_kwargs = {}
        self.output_path = ""
        self.output_format_code = lux.RENDER_OUTPUT_PNG  # Default to PNG
        self.original_render_device_param = None

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

        engine_names = {
            0: "RENDER_ENGINE_PRODUCT",
            1: "RENDER_ENGINE_INTERIOR",
            3: "RENDER_ENGINE_PRODUCT_GPU",
            4: "RENDER_ENGINE_INTERIOR_GPU",
        }

        current_engine = lux.getRenderEngine()
        engine_name = engine_names[current_engine]

        current_device = self.render_kwargs.get("current_device", get_current_render_device())
        render_device = self.render_kwargs.get("render_device", current_device)
        override_chosen = self.render_kwargs.get("override_render_device", False)

        if override_chosen:
            print("Option to override the Keyshot render device was selected.")
            if current_device == render_device:
                print(
                    f"KeyShot render device {render_device} is already selected. Chosen override option matches Keyshot setting.\n"
                )
            else:
                print(f"Overriding {current_device} with {render_device}...\n")
        else:
            print("Option to override the Keyshot render device was NOT selected.")
            if (
                current_device != self.original_render_device_param
                and self.original_render_device_param is not None
            ):
                print(
                    f"WARNING: RenderDevice value from the submitter ({self.original_render_device_param}) will be ignored since override is not selected.\n"
                )

        print(f"Selected render engine: {engine_name}")
        print(f"Selected render device: {render_device}")

        print("Starting Render...")
        frame = self.render_kwargs["frame"]

        if "render_options" in self.render_kwargs:
            opts = lux.RenderOptions(dict=self.render_kwargs["render_options"])
        else:
            opts = lux.getRenderOptions()

        opts.setAddToQueue(False)
        lux.setAnimationFrame(frame)
        output_path = self.output_path.replace("%d", str(frame))
        pprint(f"KeyShot Render Options: {opts}", indent=4)
        print(f"KeyShot Render Output Format: {self.output_format_code}")

        try:
            lux.renderImage(path=output_path, opts=opts, format=self.output_format_code)
        except Exception as e:
            error_message = str(e)
            if "This scene was saved using a newer version" in error_message:
                updated_error_message = "This scene was saved using a newer version. Opening it in an older version may cause some information to be lost."
                print(f"WARNING: Version mismatch detected but continuing: {updated_error_message}")
            else:
                raise
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

    def set_render_options(self, data: dict) -> None:
        """
        Sets the render options for the render

        Args:
            data (dict): The data given from the Adaptor. Keys expected: ['render_options']
        """
        if "render_options" in data:
            self.render_kwargs["render_options"] = data["render_options"]

    def set_override_render_device(self, data: dict) -> None:
        """
        Sets the override render device flag

        Args:
            data (dict): The data given from the Adaptor. Keys expected: ['override_render_device']
        """
        self.render_kwargs["override_render_device"] = data.get("override_render_device", False)

    def set_render_device(self, data: dict) -> None:
        """
        Sets the render engine (CPU or GPU) based on the parameter value.

        Args:
            data (dict): The data given from the Adaptor. Keys expected: ['render_device']

        Raises:
            RuntimeError: If GPU rendering is requested but no compatible GPU is available
        """
        override_render_device = self.render_kwargs.get("override_render_device", False)
        self.original_render_device_param = data["render_device"]
        current_engine = lux.getRenderEngine()

        self.render_kwargs["current_device"] = get_current_render_device()
        self.render_kwargs["render_device"] = (
            data["render_device"]
            if override_render_device
            else self.render_kwargs["current_device"]
        )

        if (
            self.render_kwargs["render_device"] == "GPU"
            and self.render_kwargs["current_device"] == "CPU"
        ):
            engine_map = {
                lux.RENDER_ENGINE_PRODUCT: lux.RENDER_ENGINE_PRODUCT_GPU,
                lux.RENDER_ENGINE_INTERIOR: lux.RENDER_ENGINE_INTERIOR_GPU,
            }
            if current_engine in engine_map:
                try:
                    lux.setRenderEngine(engine_map[current_engine])
                except Exception:
                    raise RuntimeError(
                        "GPU rendering was requested but no compatible GPU is available on this worker. Please manually set min GPUs to 1 under 'Host requirements' in the KeyShot integrated submitter."
                    )
        elif (
            self.render_kwargs["render_device"] == "CPU"
            and self.render_kwargs["current_device"] == "GPU"
        ):
            engine_map = {
                lux.RENDER_ENGINE_PRODUCT_GPU: lux.RENDER_ENGINE_PRODUCT,
                lux.RENDER_ENGINE_INTERIOR_GPU: lux.RENDER_ENGINE_INTERIOR,
            }
            if current_engine in engine_map:
                lux.setRenderEngine(engine_map[current_engine])


def get_current_render_device() -> str:
    current_engine = lux.getRenderEngine()
    is_gpu = current_engine in [lux.RENDER_ENGINE_PRODUCT_GPU, lux.RENDER_ENGINE_INTERIOR_GPU]
    return "GPU" if is_gpu else "CPU"
