# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from __future__ import annotations
import lux
import sys
import os

print("KeyShot Python Version: %s" % sys.version)

# KeyShot doesn't use PYTHONPATH and has a limited standard library
# we explicitly load modules here from DEADLINE_CLOUD_PYTHONPATH search path
if "openjd" not in sys.modules.keys():
    python_path = os.getenv("DEADLINE_CLOUD_PYTHONPATH", "")
    python_paths = python_path.split(os.pathsep)
    for p in python_paths:
        if sys.platform == "win32":
            try:
                os.add_dll_directory(p)
            except Exception:
                print("add_dll_directory failed: %s" % p)
        sys.path.append(p)


from types import FrameType  # noqa: E402
from typing import Optional  # noqa: E402

from openjd.adaptor_runtime_client import ClientInterface  # noqa: E402
from deadline.keyshot_adaptor.KeyShotClient.keyshot_handler import KeyShotHandler  # noqa: E402

try:
    import lux  # type: ignore  # noqa: F401
except ImportError:  # pragma: no cover
    raise OSError("Could not find the KeyShot module. Are you running this inside of KeyShot?")


class KeyShotClient(ClientInterface):
    """
    Client that runs in KeyShot for the KeyShot Adaptor
    """

    def __init__(self, server_path: str) -> None:
        super().__init__(server_path=server_path)
        version_str: str = ".".join(str(v) for v in lux.getKeyShotVersion()[:3])
        print(f"KeyShotClient: KeyShot Version {version_str}")
        self.actions.update(KeyShotHandler().action_dict)

    def close(self, args: Optional[dict] = None) -> None:
        sys.exit(0)

    def graceful_shutdown(self, signum: int, frame: FrameType | None):
        sys.exit(0)


def main():
    server_path = os.environ.get("KEYSHOT_ADAPTOR_SERVER_PATH")
    if not server_path:
        raise OSError(
            "KeyShotClient cannot connect to the Adaptor because the environment variable "
            "KEYSHOT_ADAPTOR_SERVER_PATH does not exist"
        )

    if not os.path.exists(server_path):
        raise OSError(
            "KeyShotClient cannot connect to the Adaptor because the server path defined by "
            "the environment variable KEYSHOT_ADAPTOR_SERVER_PATH does not exist. Got: "
            f"{os.environ['KEYSHOT_ADAPTOR_SERVER_PATH']}"
        )

    client = KeyShotClient(server_path)
    client.poll()


if __name__ == "__main__":  # pragma: no cover
    main()
