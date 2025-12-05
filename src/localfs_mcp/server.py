"""MCP server for read-only local filesystem access."""

import asyncio
from datetime import datetime
import json
import sys
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server


class LocalFSServer:
    """MCP server for read-only local filesystem access."""

    def __init__(self, config_path: str = "config.json"):
        """Initialize the server with configuration."""
        self.server = Server("localfs-mcp")
        self.allowed_paths: list[Path] = []
        self.load_config(config_path)
        self.setup_handlers()

    def load_config(self, config_path: str) -> None:
        """Load configuration from JSON file."""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                # Try relative to script directory
                script_dir = Path(__file__).parent.parent.parent
                config_file = script_dir / config_path
            
            if not config_file.exists():
                print(f"Warning: Config file not found at {config_path}, using empty allowed paths", file=sys.stderr)
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load allowed paths and normalize them
            raw_paths = config.get("allowedPaths", [])
            for path_str in raw_paths:
                # Convert to Path and resolve to absolute path
                path = Path(path_str).resolve()
                self.allowed_paths.append(path)
            
            print(f"Loaded {len(self.allowed_paths)} allowed paths from config", file=sys.stderr)
            for path in self.allowed_paths:
                print(f"  - {path}", file=sys.stderr)
        
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr)

    def is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories."""
        if not self.allowed_paths:
            # If no allowed paths configured, deny all access
            return False
        
        # Resolve to absolute path
        try:
            resolved_path = path.resolve()
        except (OSError, RuntimeError):
            return False
        
        # Check if path is under any allowed path
        for allowed_path in self.allowed_paths:
            try:
                # Check if resolved_path is relative to allowed_path
                resolved_path.relative_to(allowed_path)
                return True
            except ValueError:
                # Not relative to this allowed path, try next
                continue
        
        return False

    def setup_handlers(self) -> None:
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List available filesystem tools."""
            return [
                types.Tool(
                    name="list_directory",
                    description="List contents of a directory. Returns files and subdirectories.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path to list"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="read_file",
                    description="Read contents of a text file. Returns the file content as a string.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to read"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="get_file_info",
                    description="Get information about a file or directory (size, modification time, type).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to get information about"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="search_files",
                    description="Search for files in a directory by name pattern.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directory to search in"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "File name pattern to search for (e.g., '*.txt', 'README*')"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Whether to search recursively in subdirectories",
                                "default": False
                            }
                        },
                        "required": ["directory", "pattern"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "list_directory":
                    return await self.list_directory(arguments["path"])
                elif name == "read_file":
                    return await self.read_file(arguments["path"])
                elif name == "get_file_info":
                    return await self.get_file_info(arguments["path"])
                elif name == "search_files":
                    return await self.search_files(
                        arguments["directory"],
                        arguments["pattern"],
                        arguments.get("recursive", False)
                    )
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async def list_directory(self, path_str: str) -> list[types.TextContent]:
        """List contents of a directory."""
        path = Path(path_str)
        
        if not self.is_path_allowed(path):
            return [types.TextContent(
                type="text",
                text=f"Error: Access denied. Path '{path}' is not in allowed directories."
            )]
        
        if not path.exists():
            return [types.TextContent(type="text", text=f"Error: Path does not exist: {path}")]
        
        if not path.is_dir():
            return [types.TextContent(type="text", text=f"Error: Path is not a directory: {path}")]
        
        try:
            entries = []
            for entry in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                entry_type = "DIR" if entry.is_dir() else "FILE"
                size = ""
                if entry.is_file():
                    try:
                        size = f" ({entry.stat().st_size} bytes)"
                    except (OSError, PermissionError):
                        size = ""
                entries.append(f"{entry_type:5} {entry.name}{size}")
            
            result = f"Contents of {path}:\n" + "\n".join(entries)
            return [types.TextContent(type="text", text=result)]
        
        except PermissionError:
            return [types.TextContent(type="text", text=f"Error: Permission denied: {path}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error listing directory: {str(e)}")]

    async def read_file(self, path_str: str) -> list[types.TextContent]:
        """Read contents of a file."""
        path = Path(path_str)
        
        if not self.is_path_allowed(path):
            return [types.TextContent(
                type="text",
                text=f"Error: Access denied. Path '{path}' is not in allowed directories."
            )]
        
        if not path.exists():
            return [types.TextContent(type="text", text=f"Error: File does not exist: {path}")]
        
        if not path.is_file():
            return [types.TextContent(type="text", text=f"Error: Path is not a file: {path}")]
        
        try:
            # Try to read as text
            content = path.read_text(encoding='utf-8')
            return [types.TextContent(type="text", text=content)]
        except UnicodeDecodeError:
            return [types.TextContent(
                type="text",
                text=f"Error: File is not a text file or has incompatible encoding: {path}"
            )]
        except PermissionError:
            return [types.TextContent(type="text", text=f"Error: Permission denied: {path}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error reading file: {str(e)}")]

    async def get_file_info(self, path_str: str) -> list[types.TextContent]:
        """Get information about a file or directory."""
        path = Path(path_str)
        
        if not self.is_path_allowed(path):
            return [types.TextContent(
                type="text",
                text=f"Error: Access denied. Path '{path}' is not in allowed directories."
            )]
        
        if not path.exists():
            return [types.TextContent(type="text", text=f"Error: Path does not exist: {path}")]
        
        try:
            stat_info = path.stat()
            modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            info_lines = [
                f"Path: {path}",
                f"Type: {'Directory' if path.is_dir() else 'File'}",
                f"Size: {stat_info.st_size} bytes",
                f"Modified: {modified_time}",
                f"Absolute path: {path.resolve()}"
            ]
            
            return [types.TextContent(type="text", text="\n".join(info_lines))]
        
        except PermissionError:
            return [types.TextContent(type="text", text=f"Error: Permission denied: {path}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting file info: {str(e)}")]

    async def search_files(self, directory_str: str, pattern: str, recursive: bool = False) -> list[types.TextContent]:
        """Search for files matching a pattern."""
        directory = Path(directory_str)
        
        if not self.is_path_allowed(directory):
            return [types.TextContent(
                type="text",
                text=f"Error: Access denied. Path '{directory}' is not in allowed directories."
            )]
        
        if not directory.exists():
            return [types.TextContent(type="text", text=f"Error: Directory does not exist: {directory}")]
        
        if not directory.is_dir():
            return [types.TextContent(type="text", text=f"Error: Path is not a directory: {directory}")]
        
        try:
            matches = []
            
            if recursive:
                # Use rglob for recursive search
                for match in directory.rglob(pattern):
                    if self.is_path_allowed(match):
                        matches.append(str(match))
            else:
                # Use glob for non-recursive search
                for match in directory.glob(pattern):
                    if self.is_path_allowed(match):
                        matches.append(str(match))
            
            if not matches:
                return [types.TextContent(type="text", text=f"No files found matching '{pattern}' in {directory}")]
            
            result = f"Found {len(matches)} file(s) matching '{pattern}':\n" + "\n".join(sorted(matches))
            return [types.TextContent(type="text", text=result)]
        
        except PermissionError:
            return [types.TextContent(type="text", text=f"Error: Permission denied: {directory}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error searching files: {str(e)}")]

    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point for the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LocalFS MCP Server")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    args = parser.parse_args()
    
    server = LocalFSServer(config_path=args.config)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
