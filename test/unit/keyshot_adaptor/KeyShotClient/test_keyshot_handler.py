# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from ... import lux_import_override  # noqa: F401

from deadline.keyshot_adaptor.KeyShotClient.keyshot_handler import KeyShotHandler, lux
from unittest import mock


def test_keyshot_handler_creation():
    KeyShotHandler()


def test_set_render_options():
    handler = KeyShotHandler()
    mock_render_options = {"engine_anti_aliasing": 1, "progressive_max_samples": 10}
    handler.set_render_options({"render_options": mock_render_options})
    assert handler.render_kwargs["render_options"] == mock_render_options


def test_start_render_uses_passed_render_options():
    mock_render_options_obj = mock.MagicMock()
    with (
        mock.patch.object(lux, "renderImage") as render_image_mock,
        mock.patch.object(lux, "setAnimationFrame"),
        mock.patch.object(lux, "getRenderOptions") as get_render_options_mock,
        mock.patch.object(lux, "RenderOptions", return_value=mock_render_options_obj),
    ):

        handler = KeyShotHandler()
        handler.render_kwargs = {
            "render_options": {"engine_anti_aliasing": 1, "progressive_max_samples": 10},
            "frame": 1,
        }
        handler.output_path = "test_%d.png"

        handler.start_render({})

        get_render_options_mock.assert_not_called()
        render_image_mock.assert_called_once_with(
            path="test_1.png", opts=mock_render_options_obj, format=mock.ANY
        )
