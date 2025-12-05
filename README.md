# LocalFS MCP Server

A Model Context Protocol (MCP) server for read-only local filesystem access. This server allows safe, controlled access to your local filesystem through the MCP protocol, making it ideal for use with AI assistants like Claude in VS Code.

## Features

- **Read-only access**: All operations are read-only, ensuring your files are safe
- **Configurable access control**: Limit access to specific folders and their subfolders
- **Windows support**: Designed with Windows paths in mind (also works on Linux/Mac)
- **Multiple operations**:
  - List directory contents
  - Read text files
  - Get file/directory information
  - Search for files by pattern

## Installation

### Using pip

```bash
pip install -e .
```

### For development

```bash
pip install -e ".[dev]"
```

## Configuration

Create a `config.json` file in the same directory as the server to specify which directories can be accessed:

```json
{
  "allowedPaths": [
    "C:\\Users\\YourUsername\\Documents",
    "C:\\Projects"
  ]
}
```

On Linux/Mac, use Unix-style paths:

```json
{
  "allowedPaths": [
    "/home/username/documents",
    "/home/username/projects"
  ]
}
```

**Important**: Only paths listed in `allowedPaths` and their subdirectories will be accessible. If no paths are configured, all access will be denied.

## Usage

### Running the server

```bash
localfs-mcp
```

Or with a custom config file:

```bash
localfs-mcp --config /path/to/config.json
```

### Using with VS Code and Claude

1. Install the MCP extension in VS Code
2. Configure the MCP settings to use this server:

```json
{
  "mcpServers": {
    "localfs": {
      "command": "localfs-mcp",
      "args": ["--config", "C:\\path\\to\\config.json"]
    }
  }
}
```

3. Restart VS Code or reload the MCP extension

## Available Tools

The server provides the following tools:

### list_directory
List the contents of a directory.
- **Input**: `path` (string) - Directory path to list
- **Output**: List of files and directories with type indicators

### read_file
Read the contents of a text file.
- **Input**: `path` (string) - File path to read
- **Output**: File contents as text

### get_file_info
Get information about a file or directory.
- **Input**: `path` (string) - Path to get information about
- **Output**: File type, size, modification time, and absolute path

### search_files
Search for files matching a pattern.
- **Input**: 
  - `directory` (string) - Directory to search in
  - `pattern` (string) - File name pattern (e.g., "*.txt", "README*")
  - `recursive` (boolean, optional) - Whether to search subdirectories
- **Output**: List of matching file paths

## Development

### Running tests

```bash
pytest
```

### Project structure

```
localfs-mcp/
├── src/
│   └── localfs_mcp/
│       ├── __init__.py
│       └── server.py
├── tests/
│   ├── __init__.py
│   └── test_server.py
├── config.json
├── config.example.json
├── pyproject.toml
└── README.md
```

## Security

- All operations are **read-only** - no write, delete, or modify operations are supported
- Access is restricted to configured paths only
- Path traversal attempts are blocked by resolving all paths to absolute paths
- Binary files return an error when attempting to read as text

## License

MIT License - see LICENSE file for details
