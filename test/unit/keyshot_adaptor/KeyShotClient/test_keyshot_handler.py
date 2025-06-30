# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from ... import lux_import_override  # noqa: F401

from deadline.keyshot_adaptor.KeyShotClient.keyshot_handler import KeyShotHandler, lux
from unittest import mock

import pytest

RENDER_ENGINE_PRODUCT = 0
RENDER_ENGINE_INTERIOR = 1
RENDER_ENGINE_PRODUCT_GPU = 3
RENDER_ENGINE_INTERIOR_GPU = 4


@pytest.fixture(autouse=True)
def setup_engine_constants():
    """Set up the engine constants for all tests."""
    lux.RENDER_ENGINE_PRODUCT = RENDER_ENGINE_PRODUCT
    lux.RENDER_ENGINE_INTERIOR = RENDER_ENGINE_INTERIOR
    lux.RENDER_ENGINE_PRODUCT_GPU = RENDER_ENGINE_PRODUCT_GPU
    lux.RENDER_ENGINE_INTERIOR_GPU = RENDER_ENGINE_INTERIOR_GPU
    yield


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
        mock.patch.object(lux, "getRenderEngine", return_value=0),
    ):

        handler = KeyShotHandler()
        handler.render_kwargs = {
            "render_options": {"engine_anti_aliasing": 1, "progressive_max_samples": 10},
            "frame": 1,
            "render_device": "CPU",
            "override_render_device": False,
            "current_device": "CPU",
        }
        handler.output_path = "test_%d.png"

        handler.start_render({})

        get_render_options_mock.assert_not_called()
        render_image_mock.assert_called_once_with(
            path="test_1.png", opts=mock_render_options_obj, format=mock.ANY
        )


def test_set_render_device_gpu_with_gpu_available():
    with (
        mock.patch.object(lux, "getRenderEngine", return_value=0),
        mock.patch.object(lux, "setRenderEngine") as set_render_device_mock,
    ):

        handler = KeyShotHandler()
        handler.render_kwargs = {"override_render_device": True}
        handler.set_render_device({"render_device": "GPU"})

        set_render_device_mock.assert_called_once_with(RENDER_ENGINE_PRODUCT_GPU)


def test_set_render_device_cpu_with_gpu_engine():
    with (
        mock.patch.object(lux, "getRenderEngine", return_value=RENDER_ENGINE_PRODUCT_GPU),
        mock.patch.object(lux, "setRenderEngine") as set_render_device_mock,
    ):

        handler = KeyShotHandler()
        handler.render_kwargs = {"override_render_device": True}
        handler.set_render_device({"render_device": "CPU"})

        set_render_device_mock.assert_called_once_with(RENDER_ENGINE_PRODUCT)


def test_set_render_device_with_override_false():
    with (
        mock.patch.object(lux, "getRenderEngine", return_value=RENDER_ENGINE_PRODUCT),
        mock.patch.object(lux, "setRenderEngine") as set_render_device_mock,
    ):

        handler = KeyShotHandler()
        handler.render_kwargs = {"override_render_device": False}
        handler.set_render_device({"render_device": "GPU"})

        set_render_device_mock.assert_not_called()
        assert handler.render_kwargs["render_device"] == "CPU"
