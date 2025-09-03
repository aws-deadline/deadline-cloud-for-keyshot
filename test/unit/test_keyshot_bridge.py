# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import os
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from keyshot_bridge import get_keyshot_executable, start_socket_server


class TestKeyShotBridge:

    def test_keyshot_executable_discovery(self):
        with patch.dict(os.environ, {"KEYSHOT_EXECUTABLE": "test_keyshot"}):
            with patch("shutil.which", return_value="/path/to/test_keyshot"):
                result = get_keyshot_executable()
                assert result == "/path/to/test_keyshot"

        with patch.dict(os.environ, {"KEYSHOT_LOCATION": "C:\\KeyShot"}, clear=True):
            with patch("shutil.which") as mock_which:
                mock_which.side_effect = lambda x: (
                    "/path/to/keyshot" if "keyshot_headless.exe" in x else None
                )
                result = get_keyshot_executable()
                assert result == "/path/to/keyshot"

        with patch.dict(os.environ, {}, clear=True):
            with patch("shutil.which", return_value=None):
                with pytest.raises(Exception, match="Cannot find KeyShot executable"):
                    get_keyshot_executable()

    @pytest.mark.asyncio
    async def test_socket_server_binds_to_loopback(self):
        mock_process = AsyncMock()
        with patch("asyncio.start_server") as mock_start_server:
            await start_socket_server(mock_process, 8080)
            mock_start_server.assert_called_once()
            args, kwargs = mock_start_server.call_args
            assert args[1] == "127.0.0.1"  # Verify loopback binding
