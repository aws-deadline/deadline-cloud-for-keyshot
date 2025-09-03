#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
KeyShot Bridge

This script opens the KeyShot subprocess and forwards data from socket clients to the
processes's STDIN. It runs for the duration of the session.
"""

import argparse
import asyncio
from asyncio import Server, StreamReader, StreamWriter
from asyncio.subprocess import Process, PIPE
import os
import sys
from pathlib import Path
import shutil


def get_keyshot_executable() -> str:
    """Find the KeyShot executable in the system."""
    possible_exes = [
        os.environ.get("KEYSHOT_EXECUTABLE"),
        f"{os.environ.get('KEYSHOT_LOCATION')}\\bin\\keyshot_headless.exe",
        "keyshot_headless.exe",
        "keyshot_headless",
        "keyshot",
    ]

    for possible_exe in possible_exes:
        if possible_exe:
            found_exe = shutil.which(possible_exe)
            if found_exe:
                return found_exe

    raise FileNotFoundError("Cannot find KeyShot executable. Looked for: " + str(possible_exes))


async def start_socket_server(process: Process, port: int) -> Server:
    async def client_handler(reader: StreamReader, writer: StreamWriter) -> None:
        print("Client connected")
        await handle_client(reader, writer, process)
        print("Client disconnected")

    # Bind to loopback interface only to prevent external network access
    return await asyncio.start_server(client_handler, "127.0.0.1", port)


async def handle_client(reader: StreamReader, writer: StreamWriter, process: Process) -> None:
    async def forward_lines(source: StreamReader, destination: StreamWriter, label: str) -> None:
        """Forwards lines from a source stream to a destination stream."""
        while process.returncode is None:
            try:
                if line := await source.readline():
                    print(f"[{label}] {line.decode().strip()}")
                    destination.write(line)
                    await destination.drain()
                else:
                    break
            except Exception as e:
                print(f"[{label}] Exception: {e}")
                break

    # Create tasks for bidirectional forwarding
    # stdin/stdout are guaranteed to be non-None because we created the subprocess with PIPE
    client_task = asyncio.create_task(forward_lines(reader, process.stdin, "Client -> KeyShot"))  # type: ignore[arg-type]
    keyshot_task = asyncio.create_task(forward_lines(process.stdout, writer, "KeyShot -> Client"))  # type: ignore[arg-type]

    try:
        _, pending = await asyncio.wait(
            [client_task, keyshot_task], return_when=asyncio.FIRST_COMPLETED
        )

        # When one task ends, cancel the other
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                # Expected since the task should be cancelled
                pass

    finally:
        writer.close()
        await writer.wait_closed()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="KeyShot Bridge - Socket server for KeyShot communication"
    )
    parser.add_argument("--scene-file", required=True, help="Path to KeyShot scene file")
    parser.add_argument(
        "--keyshot-command-handler-script", required=True, help="Path to KeyShot command handler"
    )
    parser.add_argument("--port", type=int, help="Port for socket server")
    args = parser.parse_args()

    # Validate inputs
    if not Path(args.scene_file).exists():
        raise FileNotFoundError(f"Scene file not found: {args.scene_file}")

    if not Path(args.keyshot_command_handler_script).exists():
        raise FileNotFoundError(f"Command handler not found: {args.keyshot_command_handler_script}")

    # Build KeyShot command line arguments
    cmd = [
        get_keyshot_executable(),
        # On Mac and Linux, the -headless flag is required. Omit it on Windows.
        *([] if os.name == "nt" else ["-headless"]),
        "-progress",
        "-floating_feature",
        "keyshot2",
        "--scene-file",
        args.scene_file,
        "-script",
        args.keyshot_command_handler_script,
    ]

    print(f"Starting KeyShot: {' '.join(cmd)}")
    sys.stdout.flush()

    process = None
    server = None
    try:
        # Start KeyShot process using asyncio subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        print(f"KeyShot process started with PID: {process.pid}")

        server = await start_socket_server(process, port=args.port)
        print(f"Socket server listening on port {args.port}")

        # Check if KeyShot process is still running
        if process.returncode is not None:
            error_message = f"ERROR: KeyShot process exited early with code: {process.returncode}"
            if process.stderr is not None:
                stderr_output = await process.stderr.read()
                if stderr_output:
                    error_message += f"\nKeyShot stderr: {stderr_output.decode()}"
            raise RuntimeError(error_message)

        print("KeyShot server is ready")
        sys.stdout.flush()

        await process.wait()
        print(f"KeyShot process ended with return code: {process.returncode}")
    finally:
        print("Closing KeyShot bridge...")
        if server:
            server.close()
            await server.wait_closed()
            print("Socket server closed")
        if process:
            # Try to terminate gracefully first
            process.terminate()

            # Wait a bit for graceful shutdown
            try:
                await asyncio.wait_for(process.wait(), timeout=10)
            except asyncio.TimeoutError:
                # Force kill if it doesn't terminate gracefully
                print("Force killing KeyShot process...")
                process.kill()
                await process.wait()

            print(f"KeyShot process (PID: {process.pid}) terminated")


if __name__ == "__main__":
    asyncio.run(main())
