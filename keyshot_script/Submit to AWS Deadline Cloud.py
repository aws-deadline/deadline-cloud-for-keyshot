# AUTHOR AWS
# VERSION 0.0.6
# Submit to AWS Deadline Cloud

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import os
import subprocess
import json
import tempfile
import lux

# TODO: installed artifact needs to find python and the keyshot main module,
# for now use use these 2 environment variables DEADLINE_PYTHON, DEADLINE_KEYSHOT

# Python binary to execute keyshot submitter __main__ modiule
DEADLINE_PYTHON = os.getenv("DEADLINE_PYTHON")
# Path to keyshot submitter __main__ module
# In dev mode: src/deadline/keyshot_submitter
DEADLINE_KEYSHOT = os.getenv("DEADLINE_KEYSHOT")

if not DEADLINE_PYTHON:
    raise RuntimeError(
        "Environment variable DEADLINE_PYTHON not set. Please set DEADLINE_PYTHON to point to an installed version of Python with Pyside2."
    )

if not DEADLINE_KEYSHOT:
    raise RuntimeError(
        "Environment variable DEADLINE_KEYSHOT not set. Please set DEADLINE_KEYSHOT to point to the keyshot_submitter folder."
    )

# save scene information to json file for submitter module to load
keyshot_version = ".".join([str(v) for v in lux.getKeyShotVersion()])
scene_info = lux.getSceneInfo()
opts = lux.getRenderOptions()
opts_dict = opts.getDict()
current_frame = lux.getAnimationFrame()
animation_info = lux.getAnimationInfo()
external_files = lux.getExternalFiles()

lux_info = {
    "version": keyshot_version,
    "scene": scene_info,
    "render": opts_dict,
    "frame": current_frame,
    "animation": animation_info,
    "files": external_files,
}

_, info_file = tempfile.mkstemp(suffix=".json")
with open(info_file, "w") as f:
    json.dump(lux_info, f)


def show_submitter():
    subprocess.run([DEADLINE_PYTHON, DEADLINE_KEYSHOT, info_file])


show_submitter()
