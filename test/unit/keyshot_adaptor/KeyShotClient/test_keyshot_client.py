# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from ... import lux_import_override  # noqa: F401

from unittest import mock
import pytest

from deadline.keyshot_adaptor.KeyShotClient.keyshot_client import KeyShotClient, lux


@pytest.fixture(autouse=True)
def mock_get_keyshot_display_version():
    with mock.patch.object(lux, "getKeyShotDisplayVersion") as get_keyshot_display_version_mock:
        get_keyshot_display_version_mock.return_value = "2024", "3"
        yield get_keyshot_display_version_mock


def test_keyshot_client_creation():
    KeyShotClient("127.0.01")
