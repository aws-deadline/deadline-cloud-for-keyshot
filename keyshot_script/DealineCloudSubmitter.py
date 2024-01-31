# AUTHOR AWS
# VERSION 0.0.0
# Submit to Deadline Cloud

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
# In dev mode: src/deadlne/keyshot_submitter
DEADLINE_KEYSHOT = os.getenv("DEADLINE_KEYSHOT")

# save scene information to json file for submitter module to load
scene_info = lux.getSceneInfo()
opts = lux.getRenderOptions()
opts_dict = opts.getDict()
current_frame = lux.getAnimationFrame()
animation_info = lux.getAnimationInfo()
external_files = lux.getExternalFiles()

lux_info = {
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
