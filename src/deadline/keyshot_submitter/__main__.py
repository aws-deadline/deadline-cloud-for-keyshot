# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import sys
import os

# Retrieve the value of the environment variable DEADLINE_KEYSHOT that was
# passed as part of subprocess.run() in DeadlineCloudSubmitter.py
deadline_keyshot = sys.argv[-2]

if not deadline_keyshot:
    raise Exception("deadline submitter not found")

deadline_keyshot_path = os.path.dirname(deadline_keyshot)
if deadline_keyshot_path not in sys.path:
    sys.path.append(deadline_keyshot_path)


if __name__ == "__main__":
    from keyshot_submitter.keyshot_render_submitter import (  #  type: ignore
        show_submitter,
    )

    # Launch the submitter using the info file passed from the call to
    # subprocess.run() in DeadlineCloudSubmitter.py
    show_submitter(sys.argv[-1])
