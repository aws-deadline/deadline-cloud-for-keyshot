# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import sys
from unittest.mock import MagicMock

# we must mock UI code
mock_modules = [
    "deadline.client.ui.deadline_authentication_status",
    "qtpy",
    "qtpy.QtCore",
    "qtpy.QtWidgets",
    "qtpy.QtGui",
]

for module in mock_modules:
    sys.modules[module] = MagicMock()
