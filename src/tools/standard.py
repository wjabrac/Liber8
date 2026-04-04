"""Standard file-system boundary tools."""

import os
from src.execution.gateway import execute_command


def list_directory(path: str = ".") -> list:
    return os.listdir(path)


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} bytes to {path}"


def open_interpreter(
    command: str,
    approval_token: str | None = None,
    timeout: float = 10.0,
    sandbox_root: str | None = None,
    working_directory: str | None = None,
) -> dict:
    return execute_command(
        command,
        approval_token=approval_token,
        timeout=timeout,
        sandbox_root=sandbox_root,
        working_directory=working_directory,
    )


write_file.is_write = True
write_file.requires_isolation = True
open_interpreter.is_write = True
open_interpreter.requires_isolation = True


def register_standard_tools(registry):
    registry.register("list_directory", is_write=False, is_network=False, func=list_directory)
    registry.register("read_file", is_write=False, is_network=False, func=read_file)
    registry.register("write_file", is_write=True, is_network=False, func=write_file, requires_isolation=True)
    registry.register("open_interpreter", is_write=True, is_network=False, func=open_interpreter, requires_isolation=True)
