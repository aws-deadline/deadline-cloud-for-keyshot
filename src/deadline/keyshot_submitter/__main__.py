# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import sys
import os

deadline_keyshot = os.getenv("DEADLINE_KEYSHOT")
if not deadline_keyshot:
    raise Exception("deadline submitter not found")

deadline_keyshot_path = os.path.dirname(deadline_keyshot)
if deadline_keyshot_path not in sys.path:
    sys.path.append(deadline_keyshot_path)


if __name__ == "__main__":
    from deadline.keyshot_submitter.keyshot_render_submitter import show_submitter

    show_submitter(sys.argv[-1])
