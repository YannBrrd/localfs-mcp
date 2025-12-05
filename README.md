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

This MCP server integrates seamlessly with VS Code when using Claude or other AI assistants that support the Model Context Protocol.

#### Prerequisites

- Visual Studio Code (latest version recommended)
- Claude for VS Code extension (install from VS Code Marketplace)
- Python 3.10 or higher
- This package installed via pip (see [Installation](#installation) section above)

#### Step-by-Step Installation

1. **Install the LocalFS MCP Server**
   
   First, install this package using pip:
   ```bash
   pip install -e .
   ```

2. **Create a Configuration File**
   
   Create a `config.json` file to specify which directories you want to grant read access to. You can place this file anywhere, but a common location is in your home directory or project folder.

   **Windows example:**
   ```json
   {
     "allowedPaths": [
       "C:\\Users\\YourUsername\\Documents",
       "C:\\Users\\YourUsername\\Projects"
     ]
   }
   ```

   **Linux/Mac example:**
   ```json
   {
     "allowedPaths": [
       "/home/username/Documents",
       "/home/username/Projects"
     ]
   }
   ```

3. **Configure VS Code MCP Settings**

   Open your VS Code settings and configure the MCP server. You can do this in two ways:

   **Option A: Using VS Code Settings UI**
   - Open VS Code Settings (`Ctrl+,`/`Cmd+,`)
   - Search for "MCP"
   - Add your LocalFS server configuration

   **Option B: Editing settings.json directly**
   - Open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
   - Type "Preferences: Open User Settings (JSON)"
   - Add the MCP server configuration

   **Quick Start:** You can also copy the example configuration from `.vscode/mcp-settings.example.json` in this repository as a starting point. Note that the example file uses `${workspaceFolder}/config.json`, where `${workspaceFolder}` is a VS Code variable that automatically resolves to the root of your workspace. This makes the configuration portable for shared projects. The examples below show absolute paths instead.

   **Windows configuration:**
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

   **Linux/Mac configuration:**
   ```json
   {
     "mcpServers": {
       "localfs": {
         "command": "localfs-mcp",
         "args": ["--config", "/path/to/config.json"]
       }
     }
   }
   ```

   **Note:** If you installed the package in a virtual environment, you may need to provide the full path to the `localfs-mcp` command:
   ```json
   {
     "mcpServers": {
       "localfs": {
         "command": "/path/to/venv/bin/localfs-mcp",
         "args": ["--config", "/path/to/config.json"]
       }
     }
   }
   ```

4. **Restart VS Code**
   
   After configuring, restart VS Code or reload the MCP extension for the changes to take effect.

5. **Verify Installation**
   
   Open Claude in VS Code and try asking it to list files in one of your allowed directories. For example:
   ```
   Can you list the files in my Documents folder?
   ```

   If configured correctly, Claude should be able to access and list the files in your configured directories.

#### Troubleshooting

**Server not starting:**
- Verify that `localfs-mcp` is in your PATH by running `localfs-mcp --help` in a terminal
- If using a virtual environment, provide the full path to the executable
- Check that Python 3.10+ is installed: `python --version`

**Access denied errors:**
- Ensure the paths in your `config.json` are correct and exist
- Check that the paths use the correct format for your OS (backslashes on Windows, forward slashes on Linux/Mac)
- Verify that your user account has read permissions for the specified directories

**Configuration not loading:**
- Verify the config file path in your VS Code settings is absolute and correct
- Ensure the `config.json` file is valid JSON (no trailing commas, proper quotes)
- Check the VS Code Output panel for MCP-related error messages

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
