"""Tests for the LocalFS MCP server."""

import json
import tempfile
from pathlib import Path

import pytest

from localfs_mcp.server import LocalFSServer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config_file(temp_dir):
    """Create a test configuration file."""
    test_dir = temp_dir / "test_data"
    test_dir.mkdir()
    
    config_path = temp_dir / "test_config.json"
    config = {
        "allowedPaths": [str(test_dir)]
    }
    config_path.write_text(json.dumps(config))
    
    return config_path, test_dir


@pytest.fixture
def server(config_file):
    """Create a LocalFS server instance."""
    config_path, test_dir = config_file
    server = LocalFSServer(config_path=str(config_path))
    return server, test_dir


class TestPathValidation:
    """Tests for path validation and access control."""
    
    def test_allowed_path_direct(self, server):
        """Test that direct allowed path is accessible."""
        srv, test_dir = server
        assert srv.is_path_allowed(test_dir)
    
    def test_allowed_path_subdirectory(self, server):
        """Test that subdirectories of allowed paths are accessible."""
        srv, test_dir = server
        subdir = test_dir / "subdir"
        assert srv.is_path_allowed(subdir)
    
    def test_disallowed_path(self, server):
        """Test that paths outside allowed directories are denied."""
        srv, test_dir = server
        other_path = test_dir.parent / "other"
        assert not srv.is_path_allowed(other_path)
    
    def test_empty_config_denies_all(self, temp_dir):
        """Test that empty config denies all access."""
        config_path = temp_dir / "empty_config.json"
        config_path.write_text(json.dumps({"allowedPaths": []}))
        
        srv = LocalFSServer(config_path=str(config_path))
        assert not srv.is_path_allowed(temp_dir)


class TestListDirectory:
    """Tests for list_directory tool."""
    
    async def test_list_empty_directory(self, server):
        """Test listing an empty directory."""
        srv, test_dir = server
        result = await srv.list_directory(str(test_dir))
        
        assert len(result) == 1
        assert "Contents of" in result[0].text
    
    async def test_list_directory_with_files(self, server):
        """Test listing a directory with files."""
        srv, test_dir = server
        
        # Create test files
        (test_dir / "file1.txt").write_text("test")
        (test_dir / "file2.txt").write_text("test")
        (test_dir / "subdir").mkdir()
        
        result = await srv.list_directory(str(test_dir))
        
        assert len(result) == 1
        text = result[0].text
        assert "file1.txt" in text
        assert "file2.txt" in text
        assert "subdir" in text
        assert "DIR" in text  # Directory marker
        assert "FILE" in text  # File marker
    
    async def test_list_nonexistent_directory(self, server):
        """Test listing a nonexistent directory."""
        srv, test_dir = server
        result = await srv.list_directory(str(test_dir / "nonexistent"))
        
        assert len(result) == 1
        assert "does not exist" in result[0].text
    
    async def test_list_disallowed_directory(self, server):
        """Test listing a disallowed directory."""
        srv, test_dir = server
        other_path = test_dir.parent / "other"
        result = await srv.list_directory(str(other_path))
        
        assert len(result) == 1
        assert "Access denied" in result[0].text


class TestReadFile:
    """Tests for read_file tool."""
    
    async def test_read_text_file(self, server):
        """Test reading a text file."""
        srv, test_dir = server
        
        test_file = test_dir / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        result = await srv.read_file(str(test_file))
        
        assert len(result) == 1
        assert result[0].text == content
    
    async def test_read_nonexistent_file(self, server):
        """Test reading a nonexistent file."""
        srv, test_dir = server
        result = await srv.read_file(str(test_dir / "nonexistent.txt"))
        
        assert len(result) == 1
        assert "does not exist" in result[0].text
    
    async def test_read_disallowed_file(self, server):
        """Test reading a disallowed file."""
        srv, test_dir = server
        other_path = test_dir.parent / "other.txt"
        result = await srv.read_file(str(other_path))
        
        assert len(result) == 1
        assert "Access denied" in result[0].text
    
    async def test_read_directory_as_file(self, server):
        """Test trying to read a directory as a file."""
        srv, test_dir = server
        result = await srv.read_file(str(test_dir))
        
        assert len(result) == 1
        assert "not a file" in result[0].text


class TestGetFileInfo:
    """Tests for get_file_info tool."""
    
    async def test_get_file_info(self, server):
        """Test getting file information."""
        srv, test_dir = server
        
        test_file = test_dir / "test.txt"
        test_file.write_text("test content")
        
        result = await srv.get_file_info(str(test_file))
        
        assert len(result) == 1
        text = result[0].text
        assert "Path:" in text
        assert "Type: File" in text
        assert "Size:" in text
        assert "Modified:" in text
    
    async def test_get_directory_info(self, server):
        """Test getting directory information."""
        srv, test_dir = server
        result = await srv.get_file_info(str(test_dir))
        
        assert len(result) == 1
        text = result[0].text
        assert "Type: Directory" in text
    
    async def test_get_info_nonexistent(self, server):
        """Test getting info for nonexistent path."""
        srv, test_dir = server
        result = await srv.get_file_info(str(test_dir / "nonexistent"))
        
        assert len(result) == 1
        assert "does not exist" in result[0].text


class TestSearchFiles:
    """Tests for search_files tool."""
    
    async def test_search_files_non_recursive(self, server):
        """Test non-recursive file search."""
        srv, test_dir = server
        
        # Create test files
        (test_dir / "test1.txt").write_text("test")
        (test_dir / "test2.txt").write_text("test")
        (test_dir / "other.log").write_text("test")
        
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "test3.txt").write_text("test")
        
        result = await srv.search_files(str(test_dir), "*.txt", recursive=False)
        
        assert len(result) == 1
        text = result[0].text
        assert "test1.txt" in text
        assert "test2.txt" in text
        assert "test3.txt" not in text  # Should not find files in subdirectories
    
    async def test_search_files_recursive(self, server):
        """Test recursive file search."""
        srv, test_dir = server
        
        # Create test files
        (test_dir / "test1.txt").write_text("test")
        
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "test2.txt").write_text("test")
        
        result = await srv.search_files(str(test_dir), "*.txt", recursive=True)
        
        assert len(result) == 1
        text = result[0].text
        assert "test1.txt" in text
        assert "test2.txt" in text
    
    async def test_search_no_matches(self, server):
        """Test search with no matches."""
        srv, test_dir = server
        result = await srv.search_files(str(test_dir), "*.nonexistent", recursive=False)
        
        assert len(result) == 1
        assert "No files found" in result[0].text
    
    async def test_search_disallowed_directory(self, server):
        """Test searching in a disallowed directory."""
        srv, test_dir = server
        other_path = test_dir.parent / "other"
        result = await srv.search_files(str(other_path), "*.txt", recursive=False)
        
        assert len(result) == 1
        assert "Access denied" in result[0].text
