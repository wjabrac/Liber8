"""Standard file-system boundary tools."""
import os

def list_directory(path: str = ".") -> list:
    return os.listdir(path)

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} bytes to {path}"
write_file.is_write = True

def register_standard_tools(registry):
    registry.register("list_directory", is_write=False, is_network=False, func=list_directory)
    registry.register("read_file", is_write=False, is_network=False, func=read_file)
    registry.register("write_file", is_write=True, is_network=False, func=write_file)
