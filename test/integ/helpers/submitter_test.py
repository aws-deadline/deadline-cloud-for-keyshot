# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import os
import sys
from argparse import ArgumentParser

try:
    import lux
except ModuleNotFoundError:
    # so that other tests run outside of KeyShot python skip over this file
    pass


def run_submitter_test(scene_location: str, output_location: str) -> None:
    # Add the dist directory to the path to import the built submitter
    dist_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "dist")
    sys.path.insert(0, dist_path)

    # Import the built submitter directly
    # We can't use traditional imports due to spaces in the file name.
    # The spaces are necessary because KeyShot uses the file name as the script name.
    submitter = __import__("Submit to AWS Deadline Cloud")

    # create the scene
    lux.newScene()
    scene_usda = os.path.join(scene_location, "scene.usda")
    lux.importFile(path=scene_usda)
    lux.saveFile(path=scene_usda.replace(".usda", ".bip"))  # scene.bip

    # run the submitter
    submitter.main(show_gui=False, export_dir=output_location)

    # Force script to end, which should cause KeyShot to exit
    sys.exit(0)


if __name__ == "__main__":
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--scene-location", type=str, required=True)
    arg_parser.add_argument("--output-location", type=str, required=True)
    parsed_args = arg_parser.parse_args()
    run_submitter_test(parsed_args.scene_location, parsed_args.output_location)
