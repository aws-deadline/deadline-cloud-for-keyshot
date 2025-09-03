# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import sys
from unittest import mock
import pytest

# Mock lux module before importing our code
sys.modules["lux"] = mock.MagicMock()
import lux  # noqa: E402

# Set up the engine constants BEFORE importing our module
RENDER_ENGINE_PRODUCT = 0
RENDER_ENGINE_INTERIOR = 1
RENDER_ENGINE_PRODUCT_GPU = 3
RENDER_ENGINE_INTERIOR_GPU = 4

lux.RENDER_ENGINE_PRODUCT = RENDER_ENGINE_PRODUCT
lux.RENDER_ENGINE_INTERIOR = RENDER_ENGINE_INTERIOR
lux.RENDER_ENGINE_PRODUCT_GPU = RENDER_ENGINE_PRODUCT_GPU
lux.RENDER_ENGINE_INTERIOR_GPU = RENDER_ENGINE_INTERIOR_GPU
lux.RENDER_OUTPUT_PNG = 1

from keyshot_command_handler import (  # noqa: E402
    handle_render,
    handle_stop,
    apply_render_device_override,
)


def test_apply_render_device_override_gpu_with_override():
    with (
        mock.patch.object(lux, "getRenderEngine", return_value=RENDER_ENGINE_PRODUCT),
        mock.patch.object(lux, "setRenderEngine") as set_render_engine_mock,
        mock.patch("builtins.print"),
    ):
        result = apply_render_device_override("GPU", True)

        set_render_engine_mock.assert_called_once_with(RENDER_ENGINE_PRODUCT_GPU)
        assert result == "GPU"


def test_apply_render_device_override_cpu_with_gpu_engine():
    with (
        mock.patch.object(lux, "getRenderEngine", return_value=RENDER_ENGINE_PRODUCT_GPU),
        mock.patch.object(lux, "setRenderEngine") as set_render_engine_mock,
        mock.patch("builtins.print"),
    ):
        result = apply_render_device_override("CPU", True)

        set_render_engine_mock.assert_called_once_with(RENDER_ENGINE_PRODUCT)
        assert result == "CPU"


def test_apply_render_device_override_with_override_false():
    with (
        mock.patch.object(lux, "getRenderEngine", return_value=RENDER_ENGINE_PRODUCT),
        mock.patch.object(lux, "setRenderEngine") as set_render_engine_mock,
        mock.patch("builtins.print"),
    ):
        result = apply_render_device_override("GPU", False)

        set_render_engine_mock.assert_not_called()
        assert result == "CPU"  # Should return current device


def test_apply_render_device_override_gpu_unavailable():
    with (
        mock.patch.object(lux, "getRenderEngine", return_value=RENDER_ENGINE_PRODUCT),
        mock.patch.object(lux, "setRenderEngine", side_effect=Exception("GPU not available")),
        mock.patch("builtins.print"),
    ):
        with pytest.raises(
            RuntimeError, match="GPU rendering was requested but no compatible GPU is available"
        ):
            apply_render_device_override("GPU", True)


def test_handle_render_uses_passed_render_options():
    mock_render_options_obj = mock.MagicMock()
    with (
        mock.patch.object(lux, "renderImage") as render_image_mock,
        mock.patch.object(lux, "setAnimationFrame"),
        mock.patch.object(lux, "getRenderOptions") as get_render_options_mock,
        mock.patch.object(lux, "RenderOptions", return_value=mock_render_options_obj),
        mock.patch.object(lux, "getRenderEngine", return_value=0),
        mock.patch("builtins.print"),
    ):

        params = {
            "frame": 1,
            "output_path": "test_1.png",
            "render_device": "CPU",
            "override_render_device": False,
            "render_options": {"engine_anti_aliasing": 1, "progressive_max_samples": 10},
        }

        handle_render(params)

        get_render_options_mock.assert_not_called()
        render_image_mock.assert_called_once_with(
            path="test_1.png", opts=mock_render_options_obj, format=lux.RENDER_OUTPUT_PNG
        )


def test_handle_stop():
    with mock.patch("sys.exit") as exit_mock:
        handle_stop()
        exit_mock.assert_called_once_with(0)


def test_handle_render_exception_handling():
    with (
        mock.patch.object(lux, "getRenderEngine", return_value=RENDER_ENGINE_PRODUCT),
        mock.patch.object(lux, "setAnimationFrame", side_effect=Exception("Test error")),
        mock.patch("builtins.print") as print_mock,
    ):

        params = {
            "frame": 1,
            "output_path": "test_1.png",
            "render_device": "CPU",
            "override_render_device": False,
        }

        # Should not raise an exception
        handle_render(params)

        # Check that error message was printed
        error_calls = [call for call in print_mock.call_args_list if "error" in str(call)]
        assert len(error_calls) > 0
