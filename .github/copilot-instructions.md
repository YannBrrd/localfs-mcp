# GitHub Copilot Instructions for LocalFS MCP

## Project Overview

This is a Model Context Protocol (MCP) server for read-only local filesystem access. The server provides safe, controlled access to local filesystems through the MCP protocol, designed for use with AI assistants like Claude in VS Code.

**Key Principles:**
- All operations are read-only (no write, delete, or modify operations)
- Access is strictly controlled via configuration
- Security is paramount - path traversal attempts must be blocked

## Technology Stack

- **Language:** Python 3.10+
- **Framework:** MCP (Model Context Protocol) SDK
- **Testing:** pytest with pytest-asyncio
- **Package Manager:** pip with pyproject.toml

## Project Structure

```
localfs-mcp/
├── src/localfs_mcp/       # Source code
│   ├── __init__.py
│   └── server.py          # Main server implementation
├── tests/                 # Test files
│   ├── __init__.py
│   └── test_server.py     # Server tests
├── config.json            # Runtime configuration
├── config.example.json    # Configuration template
└── pyproject.toml         # Package configuration
```

## Code Style and Conventions

### Python Style
- Use Python 3.10+ type hints for all function parameters and return values
- Follow PEP 8 style guidelines
- Use double quotes for strings
- Use docstrings for all classes and public methods (Google style)
- Prefer `pathlib.Path` over string paths for filesystem operations

### Type Annotations
- Always include type hints: `def function_name(param: Type) -> ReturnType:`
- Use `list[Type]` instead of `List[Type]` (Python 3.10+ syntax)
- Use `Path` from `pathlib` for file system paths

### Error Handling
- Use try-except blocks for file I/O operations
- Return descriptive error messages to users
- Log errors to stderr using `print(..., file=sys.stderr)`
- Never expose system internals in error messages

### Async/Await
- All MCP handler functions must be async
- Use `async def` and `await` appropriately
- Return MCP `types.TextContent` objects with proper formatting

## Security Guidelines

**Critical Security Requirements:**
1. **Read-Only Operations:** Never implement write, delete, or modify operations
2. **Path Validation:** Always validate paths using `is_path_allowed()` before any operation
3. **Path Resolution:** Use `Path.resolve()` to prevent path traversal attacks
4. **Access Control:** Respect the `allowedPaths` configuration strictly
5. **Binary Files:** Return errors when attempting to read binary files as text

### Path Validation Pattern
```python
path = Path(user_input).resolve()
if not self.is_path_allowed(path):
    raise ValueError(f"Access denied: {path}")
```

## Testing Practices

### Test Organization
- Tests are organized by feature in test classes (e.g., `TestPathValidation`, `TestListDirectory`)
- Use pytest fixtures for setup and teardown
- All tests use temporary directories to avoid side effects

### Running Tests
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_server.py
```

### Test Fixtures
- `temp_dir`: Provides a temporary directory for testing
- `config_file`: Creates a test configuration file
- `server`: Creates a configured LocalFSServer instance

### Writing New Tests
- Use `pytest.mark.asyncio` for async tests (or rely on `asyncio_mode = "auto"` in config)
- Create temporary files/directories within test fixtures
- Test both success and error cases
- Verify error messages are user-friendly

## Development Workflow

### Setup
```bash
# Clone the repository
git clone https://github.com/YannBrrd/localfs-mcp.git
cd localfs-mcp

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Adding New Tools
When adding new MCP tools:
1. Add the tool definition in `list_tools()` with proper JSON schema
2. Implement the handler function with `@self.server.call_tool()`
3. Validate all paths using `is_path_allowed()`
4. Return `types.TextContent` or `types.ImageContent` as appropriate
5. Write comprehensive tests for the new tool

### Configuration
- Configuration is loaded from `config.json`
- Configuration schema: `{"allowedPaths": ["path1", "path2"]}`
- Windows paths use backslashes: `"C:\\Users\\..."`
- Unix paths use forward slashes: `"/home/..."`

## Common Patterns

### Returning Results
```python
return [
    types.TextContent(
        type="text",
        text="Result description"
    )
]
```

### Error Handling
```python
try:
    # Operation
    result = perform_operation()
    return [types.TextContent(type="text", text=str(result))]
except Exception as e:
    return [types.TextContent(
        type="text",
        text=f"Error: {str(e)}"
    )]
```

### File Operations
```python
path = Path(input_path).resolve()
if not self.is_path_allowed(path):
    return [types.TextContent(
        type="text",
        text=f"Access denied: {path} is not in allowed paths"
    )]

if not path.exists():
    return [types.TextContent(
        type="text",
        text=f"Path does not exist: {path}"
    )]
```

## Dependencies

### Core Dependencies
- `mcp>=0.9.0`: Model Context Protocol SDK

### Development Dependencies
- `pytest>=8.0.0`: Testing framework
- `pytest-asyncio>=0.23.0`: Async test support

## Building and Distribution

```bash
# Build the package
pip install build
python -m build

# Install locally
pip install -e .

# Run the server
localfs-mcp --config /path/to/config.json
```

## Additional Notes

- The server uses stdio for communication with MCP clients
- All file operations should handle both Windows and Unix paths
- When listing directories, distinguish between files and directories with type indicators
- File patterns support glob syntax (e.g., `*.txt`, `README*`)
- Recursive operations should have reasonable depth limits to prevent performance issues
