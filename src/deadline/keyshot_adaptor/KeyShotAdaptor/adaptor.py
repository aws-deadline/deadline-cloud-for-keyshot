# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from __future__ import annotations

import logging
import os
import re
import sys
import threading
import time
from functools import wraps
from typing import Callable

from deadline.client.api import get_deadline_cloud_library_telemetry_client, TelemetryClient
from openjd.adaptor_runtime._version import version as openjd_adaptor_version
from openjd.adaptor_runtime.adaptors import Adaptor, AdaptorDataValidators, SemanticVersion
from openjd.adaptor_runtime.adaptors.configuration import AdaptorConfiguration
from openjd.adaptor_runtime.process import LoggingSubprocess
from openjd.adaptor_runtime.app_handlers import RegexCallback, RegexHandler
from openjd.adaptor_runtime.application_ipc import ActionsQueue, AdaptorServer
from openjd.adaptor_runtime_client import Action

from .._version import version as adaptor_version

_logger = logging.getLogger(__name__)


class KeyShotNotRunningError(Exception):
    """Error that is raised when attempting to use KeyShot while it is not running"""

    pass


_FIRST_KEYSHOT_ACTIONS = ["scene_file", "output_file_path", "output_format"]

_KEYSHOT_RUN_KEYS = {"frame"}


def _check_for_exception(func: Callable) -> Callable:
    """
    Decorator that checks if an exception has been caught before calling the
    decorated function
    """

    @wraps(func)
    def wrapped_func(self, *args, **kwargs):
        if not self._has_exception:  # Raises if there is an exception  # pragma: no branch
            return func(self, *args, **kwargs)

    return wrapped_func


class KeyShotAdaptor(Adaptor[AdaptorConfiguration]):
    """
    Adaptor that creates a session in KeyShot to Render interactively.
    """

    _SERVER_START_TIMEOUT_SECONDS = 30
    _SERVER_END_TIMEOUT_SECONDS = 30
    _KEYSHOT_START_TIMEOUT_SECONDS = 300
    _KEYSHOT_END_TIMEOUT_SECONDS = 30

    _server: AdaptorServer | None = None
    _server_thread: threading.Thread | None = None
    _keyshot_client: LoggingSubprocess | None = None
    _action_queue = ActionsQueue()
    _is_rendering: bool = False
    # If a thread raises an exception we will update this to raise in the main thread
    _exc_info: Exception | None = None
    _performing_cleanup = False
    _regex_callbacks: list | None = None
    _validators: AdaptorDataValidators | None = None
    _telemetry_client: TelemetryClient | None = None
    _keyshot_version: str = ""

    # Variables used for keeping track of produced outputs for progress reporting.
    # Will be optionally changed after the scene is set.
    _expected_outputs: int = 1  # Total number of renders to perform.
    _produced_outputs: int = 0  # Counter for tracking number of complete renders.

    @property
    def integration_data_interface_version(self) -> SemanticVersion:
        return SemanticVersion(major=0, minor=1)

    @staticmethod
    def _get_timer(timeout: int | float) -> Callable[[], bool]:
        """
        Given a timeout length, returns a lambda which returns False until the timeout occurs.

        Args:
            timeout (int): The amount of time (in seconds) to wait before timing out.
        """
        timeout_time = time.time() + timeout
        return lambda: time.time() >= timeout_time

    @property
    def _has_exception(self) -> bool:
        """Property which checks the private _exc_info property for an exception

        Raises:
            self._exc_info: An exception if there is one

        Returns:
            bool: False there is no exception waiting to be raised
        """
        if self._exc_info and not self._performing_cleanup:
            raise self._exc_info
        return False

    @property
    def _keyshot_is_running(self) -> bool:
        """Property which indicates that the KeyShot client is running

        Returns:
            bool: True if the KeyShot client is running, false otherwise
        """
        return self._keyshot_client is not None and self._keyshot_client.is_running

    @property
    def _keyshot_is_rendering(self) -> bool:
        """Property which indicates if KeyShot is rendering

        Returns:
            bool: True if KeyShot is rendering, false otherwise
        """
        return self._keyshot_is_running and self._is_rendering

    @_keyshot_is_rendering.setter
    def _keyshot_is_rendering(self, value: bool) -> None:
        """Property setter which updates the private _is_rendering boolean.

        Args:
            value (bool): A boolean indicating if KeyShot is rendering.
        """
        self._is_rendering = value

    def _wait_for_server(self) -> str:
        """
        Performs a busy wait for the server path that the adaptor server is running on, then
        returns it.

        Raises:
            RuntimeError: If the server does not finish initializing

        Returns:
            str: The server path where the adaptor server is running.
        """
        is_timed_out = self._get_timer(self._SERVER_START_TIMEOUT_SECONDS)
        while (self._server is None or self._server.server_path is None) and not is_timed_out():
            time.sleep(0.01)

        if self._server is not None and self._server.server_path is not None:
            return self._server.server_path

        raise RuntimeError(
            "Could not find a server path because the server did not finish initializing"
        )

    def _start_keyshot_server(self) -> None:
        """
        Starts a server with the given ActionsQueue, attaches the server to the adaptor and serves
        forever in a blocking call.
        """
        self._server = AdaptorServer(self._action_queue, self)
        self._server.serve_forever()

    def _start_keyshot_server_thread(self) -> None:
        """
        Starts the KeyShot adaptor server in a thread.
        Sets the environment variable "KEYSHOT_ADAPTOR_SERVER_PATH" to
        the server path where the server is running after the server has
        finished starting.
        """
        self._server_thread = threading.Thread(
            target=self._start_keyshot_server, name="KeyShotAdaptorServerThread"
        )
        self._server_thread.start()
        os.environ["KEYSHOT_ADAPTOR_SERVER_PATH"] = self._wait_for_server()

    @property
    def validators(self) -> AdaptorDataValidators:
        if not self._validators:
            cur_dir = os.path.dirname(__file__)
            schema_dir = os.path.join(cur_dir, "schemas")
            self._validators = AdaptorDataValidators.for_adaptor(schema_dir)
        return self._validators

    def _get_regex_callbacks(self) -> list[RegexCallback]:
        """
        Returns a list of RegexCallbacks used by the KeyShot Adaptor

        Returns:
            list[RegexCallback]: List of Regex Callbacks to add
        """
        if not self._regex_callbacks:
            callback_list = []

            completed_regexes = [re.compile(".*Finished Rendering.*")]
            progress_regexes = [re.compile(".*Rendering: ([0-9]+)%.*")]
            error_regexes = [re.compile(".*Error: .*|.*\\[Error\\].*", re.IGNORECASE)]
            video_output_error_regexes = [
                re.compile(
                    ".*You cannot use EXR, TIFF 32 or PSD for the frames when encoding a movie!.*"
                )
            ]
            # Capture the major minor patch version.
            version_regexes = [re.compile("KeyShotClient: KeyShot Version ([0-9]+.[0-9]+.[0-9]+)")]

            callback_list.append(RegexCallback(completed_regexes, self._handle_complete))
            callback_list.append(RegexCallback(progress_regexes, self._handle_progress))
            if self.init_data.get("strict_error_checking", False):
                callback_list.append(RegexCallback(error_regexes, self._handle_error))
            callback_list.append(
                RegexCallback(video_output_error_regexes, self._handle_video_encode_error)
            )
            callback_list.append(RegexCallback(version_regexes, self._handle_version))

            self._regex_callbacks = callback_list
        return self._regex_callbacks

    def _handle_logging(self, match: re.Match) -> None:
        print(match.group(0))

    @_check_for_exception
    def _handle_complete(self, match: re.Match) -> None:
        """
        Callback for stdout that indicate completeness of a render. Updates progress to 100
        Args:
            match (re.Match): The match object from the regex pattern that was matched in the
                              message.
        """
        self._keyshot_is_rendering = False
        self.update_status(progress=100)

    @_check_for_exception
    def _handle_progress(self, match: re.Match) -> None:
        """
        Callback for stdout that indicate progress of a render.
        Args:
            match (re.Match): The match object from the regex pattern that was matched in the
                              message.
        """
        text = match.group(0)
        parts = text.split(" ")
        percent = parts[-1]
        if percent.endswith("%"):
            percent = percent[0:-1]
        progress = int(percent)
        self.update_status(progress=progress)

    def _handle_error(self, match: re.Match) -> None:
        """
        Callback for stdout that indicates an error or warning.
        Args:
            match (re.Match): The match object from the regex pattern that was matched in the
                              message

        Raises:
            RuntimeError: Always raises a runtime error to halt the adaptor.
        """
        self._exc_info = RuntimeError(f"KeyShot Encountered an Error: {match.group(0)}")

    def _handle_video_encode_error(self, match: re.Match) -> None:
        """
        Callback for stdout that indicates video output was selected during submission.
        There is an interaction in KeyShot 12 where having video output selected before
        submitting results in KeyShot warning that video encoding can't be performed
        with certain output formats, despite the adaptor never calling lux.encodeVideo()

        Args:
            match (re.Match): The match object from the regex pattern that was matched in the message

        Raises:
            RuntimeError: Always raises a runtime error to halt the adaptor.
        """
        self._exc_info = RuntimeError(
            f"{match.group(0)}\n"
            "This error is usually the result of Video Output being selected"
            "in KeyShot under Render->Animation->Video Output before submitting.\n"
            "To resolve please uncheck Video Output before submitting again."
        )

    def _handle_version(self, match: re.Match) -> None:
        """
        Callback for stdout that records the KeyShot version.
        Args:
            match (re.Match): The match object from the regex pattern that was matched the message
        """
        self._keyshot_version = match.groups()[0]

    def _get_keyshot_client_path(self) -> str:
        """
        Obtains the keyshot_client.py path by searching directories in sys.path

        Raises:
            FileNotFoundError: If the keyshot_client.py file could not be found.

        Returns:
            str: The path to the keyshot_client.py file.
        """
        for dir_ in sys.path:
            path = os.path.join(
                dir_, "deadline", "keyshot_adaptor", "KeyShotClient", "keyshot_client.py"
            )
            if os.path.isfile(path):
                return path
        raise FileNotFoundError(
            "Could not find keyshot_client.py. Check that the "
            "KeyShotClient package is in one of the "
            f"following directories: {sys.path[1:]}"
        )

    def _start_keyshot_client(self) -> None:
        """
        Starts the keyshot client by launching KeyShot with the keyshot_client.py file.

        Raises:
            FileNotFoundError: If the keyshot_client.py file or the scene file could not be found.
        """
        # KeyShot has a bug where it must be started with an absolute path
        # or the render will hang (on macOS at least). The worker env can set
        # this varirable to override the path
        keyshot_exe_env = os.getenv("DEADLINE_KEYSHOT_EXE", "")
        args = []
        if not keyshot_exe_env:
            if sys.platform == "win32":
                keyshot_exe = "keyshot_headless.exe"
                args.append(keyshot_exe)
            else:
                keyshot_exe = "keyshot"
                args.append(keyshot_exe)
                args.append("-headless")
        else:
            keyshot_exe = keyshot_exe_env
            args.append(keyshot_exe)

        regexhandler = RegexHandler(self._get_regex_callbacks())

        keyshot_client_path = self._get_keyshot_client_path()
        args.append("-progress")
        args.append("-floating_feature")
        args.append("keyshot2")
        args.append("-script")
        args.append(keyshot_client_path)

        self._keyshot_client = LoggingSubprocess(
            args=args,
            stdout_handler=regexhandler,
            stderr_handler=regexhandler,
        )

    def on_start(self) -> None:
        """
        For job stickiness. Will start everything required for the Task. Will be used for all
        SubTasks.

        Raises:
            jsonschema.ValidationError: When init_data fails validation against the adaptor schema.
            jsonschema.SchemaError: When the adaptor schema itself is nonvalid.
            RuntimeError: If KeyShot did not complete initialization actions due to an exception
            TimeoutError: If KeyShot did not complete initialization actions due to timing out.
            FileNotFoundError: If the keyshot_client.py file could not be found.
            KeyError: If a configuration for the given platform and version does not exist.
        """
        self.validators.init_data.validate(self.init_data)
        self.update_status(progress=0, status_message="Initializing KeyShot")
        self._start_keyshot_server_thread()
        self._populate_action_queue()
        self._start_keyshot_client()

        is_timed_out = self._get_timer(self._KEYSHOT_START_TIMEOUT_SECONDS)
        while self._keyshot_is_running and not self._has_exception and len(self._action_queue) > 0:
            if is_timed_out():
                raise TimeoutError(
                    "KeyShot did not complete initialization actions in "
                    f"{self._KEYSHOT_START_TIMEOUT_SECONDS} seconds and failed to start."
                )

            time.sleep(0.1)  # busy wait for keyshot to finish initialization

        self._get_deadline_telemetry_client().record_event(
            event_type="com.amazon.rum.deadline.adaptor.runtime.start", event_details={}
        )

        if len(self._action_queue) > 0:
            raise RuntimeError(
                "KeyShot encountered an error and was not able to complete initialization actions."
            )

    def on_run(self, run_data: dict) -> None:
        """
        This starts a render in KeyShot for the given frame, scene and layer(s) and
        performs a busy wait until the render completes.
        """

        if not self._keyshot_is_running:
            raise KeyShotNotRunningError("Cannot render because KeyShot is not running.")

        run_data["frame"] = int(run_data["frame"])
        self.validators.run_data.validate(run_data)
        self._is_rendering = True

        for name in _KEYSHOT_RUN_KEYS:
            if name in run_data:
                self._action_queue.enqueue_action(Action(name, {name: run_data[name]}))

        self._action_queue.enqueue_action(Action("start_render", {"frame": run_data["frame"]}))

        while self._keyshot_is_rendering and not self._has_exception:
            time.sleep(0.1)  # busy wait so that on_cleanup is not called

        if not self._keyshot_is_running and self._keyshot_client:  # Client will always exist here.
            #  This is always an error case because the KeyShot Client should still be running and
            #  waiting for the next command. If the thread finished, then we cannot continue
            exit_code = self._keyshot_client.returncode
            raise KeyShotNotRunningError(
                "KeyShot exited early and did not render successfully, please check render logs. "
                f"Exit code {exit_code}"
            )

    def on_stop(self) -> None:
        """ """
        self._action_queue.enqueue_action(Action("close"), front=True)
        return

    def on_cleanup(self):
        """
        Cleans up the adaptor by closing the KeyShot client and adaptor server.
        """
        self._performing_cleanup = True

        self._action_queue.enqueue_action(Action("close"), front=True)
        is_timed_out = self._get_timer(self._KEYSHOT_END_TIMEOUT_SECONDS)
        while self._keyshot_is_running and not is_timed_out():
            time.sleep(0.1)
        if self._keyshot_is_running and self._keyshot_client:
            _logger.error(
                "KeyShot did not complete cleanup actions and failed to gracefully shutdown. "
                "Terminating."
            )
            self._keyshot_client.terminate()

        if self._server:
            self._server.shutdown()

        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=self._SERVER_END_TIMEOUT_SECONDS)
            if self._server_thread.is_alive():
                _logger.error("Failed to shutdown the KeyShot Adaptor server.")

        self._performing_cleanup = False

    def on_cancel(self):
        """
        Cancels the current render if KeyShot is rendering.
        """
        _logger.info("CANCEL REQUESTED")
        if not self._keyshot_client or not self._keyshot_is_running:
            _logger.info("Nothing to cancel because KeyShot is not running")
            return

        self._keyshot_client.terminate(grace_time_s=0)

    def _populate_action_queue(self) -> None:
        """
        Populates the adaptor server's action queue with actions from the init_data that the KeyShot
        Client will request and perform. The action must be present in the _FIRST_KEYSHOT_ACTIONS
        set to be added to the action queue.
        """
        for name in _FIRST_KEYSHOT_ACTIONS:
            if name in self.init_data:
                self._action_queue.enqueue_action(Action(name, {name: self.init_data[name]}))

    def _get_deadline_telemetry_client(self):
        """
        Wrapper around the Deadline Client Library telemetry client, in order to set package-specific information
        """
        if not self._telemetry_client:
            self._telemetry_client = get_deadline_cloud_library_telemetry_client()
            self._telemetry_client.update_common_details(
                {
                    "deadline-cloud-for-keyshot-adaptor-version": adaptor_version,
                    "keyshot-version": self._keyshot_version,
                    "open-jd-adaptor-runtime-version": openjd_adaptor_version,
                }
            )
        return self._telemetry_client
