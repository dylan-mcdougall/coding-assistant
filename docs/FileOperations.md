# FileOperations Module Documentation

## Overview

The `FileOperations` module provides secure file system operations for the AI Agent application. It ensures that all file operations are restricted to allowed directories, preventing unauthorized access to sensitive areas of the file system. The module implements path validation, read/write operations, and directory listing with security boundaries.

## Class: FileOperations

The `FileOperations` class is the main component of this module, providing methods for secure file operations.

### Initialization

```python
def __init__(self, config_manager: ConfigManager)
```

**Parameters:**
- `config_manager`: An instance of `ConfigManager` containing application configuration.

**Description:**  
Initializes the `FileOperations` instance with configuration from the `ConfigManager`. It extracts the workspace configuration and security settings, and resolves the allowed paths for file operations.

### Methods

#### validate_path

```python
def validate_path(self, path: Union[str, Path]) -> Path
```

**Parameters:**
- `path`: The file or directory path to validate, either as a string or `Path` object.

**Returns:**
- A resolved `Path` object representing the validated path.

**Raises:**
- `ValueError`: If the path is not within allowed directories.

**Description:**  
Validates that a given path is within the allowed directories configured in the application. This is a key security feature that prevents directory traversal attacks and unauthorized file access.

#### safe_read_file

```python
def safe_read_file(self, path: Union[str, Path]) -> str
```

**Parameters:**
- `path`: The path to the file to read, either as a string or `Path` object.

**Returns:**
- The content of the file as a string.

**Raises:**
- `ValueError`: If the path is not within allowed directories.
- `FileNotFoundError`: If the file doesn't exist.
- Other exceptions may be raised for I/O errors.

**Description:**  
Securely reads a file from an allowed directory. The path is first validated to ensure it's within allowed boundaries, then the file is read and its content returned.

#### safe_write_file

```python
def safe_write_file(self, path: Union[str, Path], content: str, confirm: bool = None) -> None
```

**Parameters:**
- `path`: The path to write to, either as a string or `Path` object.
- `content`: The content to write to the file.
- `confirm`: Optional override for confirmation requirement. If `None`, uses the configuration setting.

**Raises:**
- `ValueError`: If the path is not within allowed directories.
- `PermissionError`: If writing is not confirmed when confirmation is required.
- Other exceptions may be raised for I/O errors.

**Description:**  
Securely writes content to a file in an allowed directory. The path is validated, and if confirmation is required (based on configuration or the `confirm` parameter), the user is prompted to confirm the write operation. The method ensures that parent directories exist before writing.

#### safe_list_files

```python
def safe_list_files(self, directory: Union[str, Path], pattern: str = "*") -> List[Path]
```

**Parameters:**
- `directory`: The directory to list files from, either as a string or `Path` object.
- `pattern`: A glob pattern to filter files (default: "*").

**Returns:**
- A list of `Path` objects representing the files that match the pattern.

**Raises:**
- `ValueError`: If the directory is not within allowed directories or is not a directory.
- Other exceptions may be raised for I/O errors.

**Description:**  
Securely lists files in an allowed directory that match a specified glob pattern. The directory path is validated to ensure it's within allowed boundaries, and then files are listed using the `glob` method.

## Security Considerations

The `FileOperations` module implements several security measures:

1. **Path Validation**: All file operations validate paths against the allowed directories configured in the application.

2. **Directory Traversal Prevention**: The module resolves paths to their absolute form and checks if they're within allowed directories, preventing directory traversal attacks.

3. **Write Confirmation**: Write operations can be configured to require explicit confirmation, preventing accidental or malicious file modifications.

4. **Explicit Directory Creation**: When writing files, the module ensures parent directories exist, avoiding errors and unexpected behavior.

5. **Comprehensive Logging**: All file operations are logged, creating an audit trail of file access and modifications.

## Usage Examples

### Reading a File

```python
# Initialize dependencies
config_manager = ConfigManager()
file_ops = FileOperations(config_manager)

# Read a file securely
try:
    content = file_ops.safe_read_file("~/projects/myapp/main.py")
    print(f"File content: {content}")
except ValueError as e:
    print(f"Security error: {e}")
except FileNotFoundError:
    print("File not found")
```

### Writing a File

```python
# Write content to a file with confirmation
try:
    file_ops.safe_write_file(
        "~/projects/myapp/output.txt",
        "This is the file content",
        confirm=True
    )
    print("File written successfully")
except ValueError as e:
    print(f"Security error: {e}")
except PermissionError:
    print("Write operation not confirmed")
```

### Listing Files

```python
# List Python files in a directory
try:
    python_files = file_ops.safe_list_files("~/projects/myapp", "*.py")
    print(f"Found {len(python_files)} Python files:")
    for file_path in python_files:
        print(f"  - {file_path.name}")
except ValueError as e:
    print(f"Security error: {e}")
```

## Integration with Commands Module

The `FileOperations` module is designed to work closely with the `Commands` module, which implements AI-powered file operations:

```python
# Initialize dependencies
config_manager = ConfigManager()
api = APIInterface(config_path)
file_ops = FileOperations(config_manager)

# Create commands instance
commands = Commands(api, file_ops)

# Use commands with secure file operations
result = commands.generate_tests("~/projects/myapp/main.py")
print(result)
```

## Configuration

The `FileOperations` module relies on configuration in the `config.json` file:

```json
"workspace": {
  "default_path": "~/ai_workspace",
  "allowed_paths": ["~/ai_workspace", "~/projects"]
},
"security": {
  "require_confirmation_for_writes": true
}
```

- `workspace.allowed_paths`: Defines directories where file operations are allowed
- `security.require_confirmation_for_writes`: Whether write operations require confirmation

## Error Handling

The module uses exceptions to handle error conditions:

- `ValueError`: Raised for security violations (path not in allowed directories)
- `FileNotFoundError`: Raised when a file doesn't exist
- `PermissionError`: Raised when write confirmation is denied
- Other standard I/O exceptions may be raised for file operations

All exceptions are logged for audit purposes.
