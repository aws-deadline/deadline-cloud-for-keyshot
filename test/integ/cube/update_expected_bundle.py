#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Script to update the expected bundle from the actual bundle.
Run this after making changes to the submitter to update test expectations.

Usage:
    hatch run integ:test  # Run integ tests to generate a bundle using the current submitter
    hatch run python test/integ/cube/update_expected_bundle.py  # Generate a new expected bundle from it
"""

import json
import os
from pathlib import Path


def main():
    script_dir = Path(__file__).parent
    actual_bundle_dir = script_dir / "actual_bundle"
    expected_bundle_dir = script_dir / "expected_bundle"

    if not actual_bundle_dir.exists():
        print("ERROR: actual_bundle directory not found. Run the integration test first.")
        return 1

    expected_bundle_dir.mkdir(exist_ok=True)

    # Get the path prefix to replace
    prefix_path = os.path.abspath(expected_bundle_dir).split("deadline-cloud-for-keyshot")[0]

    for json_file in ["template.json", "parameter_values.json", "asset_references.json"]:
        source_file = actual_bundle_dir / json_file
        dest_file = expected_bundle_dir / json_file

        with open(source_file, "r") as f:
            content = f.read()

        # Replace hardcoded path prefix with placeholder
        content = content.replace(prefix_path, "PATH_TO_BE_REPLACED/")

        # Parse and write compact JSON (to match submitter output format)
        data = json.loads(content)
        with open(dest_file, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Copied {json_file}")

    print(f"Updated expected bundle from {actual_bundle_dir}")

    return 0


if __name__ == "__main__":
    exit(main())
