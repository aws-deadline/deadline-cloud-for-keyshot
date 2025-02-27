# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import os
import sys
from argparse import ArgumentParser

try:
    import lux
except ModuleNotFoundError:
    # so that other tests run outside of KeyShot python skip over this file
    pass


def add_deadline_to_path() -> None:
    src_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "src")
    if sys.platform == "win32":
        try:
            os.add_dll_directory(src_path)
        except Exception:
            print("add_dll_directory failed: %s" % src_path)
    sys.path.append(src_path)


def run_submitter_test(scene_location: str, output_location: str) -> None:
    # setup deadline imports
    add_deadline_to_path()
    # We can't use traditional imports due to spaces in the file name.
    # The spaces are necessary because KeyShot uses the file name as the script name.
    deadline = __import__("deadline.keyshot_submitter.Submit to AWS Deadline Cloud")
    submitter = getattr(deadline.keyshot_submitter, "Submit to AWS Deadline Cloud")

    # create the scene
    lux.newScene()
    scene_usda = os.path.join(scene_location, "scene.usda")
    lux.importFile(path=scene_usda)
    lux.saveFile(path=scene_usda.replace(".usda", ".bip"))  # scene.bip

    # run the submitter
    submitter.main(show_gui=False, export_dir=output_location)


if __name__ == "__main__":
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--scene-location", type=str, required=True)
    arg_parser.add_argument("--output-location", type=str, required=True)
    parsed_args = arg_parser.parse_args()
    run_submitter_test(parsed_args.scene_location, parsed_args.output_location)
