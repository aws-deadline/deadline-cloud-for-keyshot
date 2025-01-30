# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from ... import lux_import_override  # noqa: F401

from deadline.keyshot_adaptor.KeyShotClient.keyshot_handler import KeyShotHandler


def test_keyshot_handler_creation():
    KeyShotHandler()
