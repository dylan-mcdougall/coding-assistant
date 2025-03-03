# Workspace Manager Documentation

## Overview

The Workspace Manager provides a secure interface for file operations within a designated workspace directory. It serves as a security boundary between the AI Agent application and the file system, ensuring that all operations are confined to authorized locations.

This document provides a comprehensive reference for the `WorkspaceManager` class implemented in `workspace_manager.py`.

### Purpose and Role in the AI Agent Application

The Workspace Manager is a critical security component designed to:

1. **Establish Secure Boundaries**: Create a controlled environment where the AI Agent can read and write files without risking access to sensitive system files.

2. **Enable Safe File Operations**: Allow the AI Agent to perform necessary file operations (read, write, create, delete) but only within explicitly defined boundaries.

3. **Prevent Security Vulnerabilities**: Protect against common security issues like path traversal attacks, directory manipulation, and unauthorized access.

4. **Provide Rollback Capability**: Support atomic operations with the ability to revert changes if errors occur, maintaining file system integrity.

## Table of Contents

- [Key Concepts](#key-concepts)
- [Security Features](#security-features)
- [Transaction System](#transaction-system)
- [API Reference](#api-reference)
  - [Constructor](#constructor)
  - [File Reading Operations](#file-reading-operations)
  - [File Writing Operations](#file-writing-operations)
  - [File Management Operations](#file-management-operations)
  - [Directory Operations](#directory-operations)
  - [Utility Methods](#utility-methods)
  - [Transaction Methods](#transaction-methods)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Common Operation Examples](#common-operation-examples)

## Key Concepts

### Workspace Root

The workspace root is the base directory that the Workspace Manager is allowed to access. All operations must be performed within this directory or explicitly allowed additional paths.

### Allowed Paths

Additional directories that the Workspace Manager is permitted to access. These paths supplement the workspace root, providing flexibility while maintaining security boundaries.

### File Operations

Operations that read, write, or manipulate files and directories within the workspace. All operations are subject to security validation to prevent access outside the workspace.

### Transactions

A sequence of file operations that can be committed or rolled back as a unit. This provides atomicity and the ability to revert changes if an error occurs.

## Security Features

The Workspace Manager implements multiple layers of security to prevent unauthorized access to the file system:

### Path Validation

All file paths are validated to ensure they are within the allowed workspace boundaries:

1. **Path Normalization**: Converts relative paths to absolute paths and expands user directories (`~`).
2. **Boundary Checking**: Verifies that paths are within the workspace root or allowed paths.
3. **Symlink Resolution**: Resolves symbolic links to their actual paths and verifies they remain within allowed boundaries.
4. **Path Traversal Prevention**: Detects and blocks attempts to use `../` or similar constructs to access parent directories outside the workspace.

### Content Validation

File content can be optionally validated for potentially dangerous patterns:

```python
dangerous_patterns = [
    "import os;", "import subprocess", "exec(", "eval(", 
    "os.system(", "subprocess.run(", "subprocess.Popen("
]
```

### Write Confirmation

By default, all operations that modify the file system require explicit confirmation. This can be disabled for automated processes or testing.

### Transaction-Based Operations

All file modifications are performed within a transaction, allowing for atomic operations and rollback capability if errors occur.

## Transaction System

The transaction system provides the following capabilities:

1. **Begin Transaction**: Start tracking file operations for potential rollback.
2. **Commit Transaction**: Finalize changes and clean up backup files.
3. **Rollback Transaction**: Restore files to their state before the transaction began.

For each write operation, the system:
1. Creates a backup of the original file (if it exists)
2. Records the operation in a transaction log
3. Performs the requested operation

If a rollback is requested, the system restores files from backups in reverse order.

## API Reference

### Constructor

```python
def __init__(
    self, 
    root_path: str,
    allowed_paths: Optional[List[str]] = None,
    require_confirmation_for_writes: bool = True,
    logger: Optional[logging.Logger] = None
) -> None
```

Creates a new `WorkspaceManager` instance.

**Parameters:**
- `root_path`: The root directory for the workspace.
- `allowed_paths`: Additional directories that the workspace manager is allowed to access.
- `require_confirmation_for_writes`: Whether to require user confirmation for write operations.
- `logger`: A logger instance for recording operations.

**Example:**
```python
workspace = WorkspaceManager(
    root_path="~/ai_workspace",
    allowed_paths=["~/projects/shared"],
    require_confirmation_for_writes=True
)
```

### File Reading Operations

#### `read_file`

```python
def read_file(self, path: Union[str, Path], binary: bool = False) -> Union[str, bytes]
```

Reads the content of a file from the workspace.

**Parameters:**
- `path`: The path to the file relative to the workspace root.
- `binary`: Whether to read the file in binary mode.

**Returns:**
- The file content as a string (if `binary=False`) or bytes (if `binary=True`).

**Raises:**
- `WorkspaceSecurityError`: If the path is outside the allowed boundaries.
- `FileNotFoundError`: If the file does not exist.
- `IsADirectoryError`: If the path is a directory.

**Example:**
```python
# Read a text file
content = workspace.read_file("documents/notes.txt")

# Read a binary file
image_data = workspace.read_file("images/photo.jpg", binary=True)
```

#### `file_exists`

```python
def file_exists(self, path: Union[str, Path]) -> bool
```

Checks if a file or directory exists in the workspace.

**Parameters:**
- `path`: The path to check.

**Returns:**
- `True` if the file or directory exists, `False` otherwise.

**Example:**
```python
if workspace.file_exists("config.json"):
    # File exists, process it
    config = workspace.read_file("config.json")
```

#### `get_file_info`

```python
def get_file_info(self, path: Union[str, Path]) -> Dict[str, Any]
```

Gets detailed information about a file or directory.

**Parameters:**
- `path`: The path to the file or directory.

**Returns:**
- A dictionary containing file metadata:
  - `name`: File name
  - `path`: Relative path
  - `full_path`: Absolute path
  - `type`: File type (e.g., "file", "directory", "python", "image")
  - `size`: File size in bytes (None for directories)
  - `created`: Creation timestamp
  - `modified`: Last modified timestamp
  - `is_hidden`: Whether the file is hidden
  - `extension`: File extension (None for directories)
  - `is_binary`: Whether the file contains binary content (None for directories)

**Raises:**
- `WorkspaceSecurityError`: If the path is outside the allowed boundaries.
- `FileNotFoundError`: If the file does not exist.

**Example:**
```python
file_info = workspace.get_file_info("documents/report.pdf")
print(f"Size: {file_info['size']} bytes")
print(f"Modified: {datetime.fromtimestamp(file_info['modified'])}")
```

### File Writing Operations

#### `write_file`

```python
def write_file(
    self, 
    path: Union[str, Path], 
    content: Union[str, bytes], 
    append: bool = False,
    confirm: bool = True,
    validate_content: bool = True
) -> bool
```

Writes content to a file in the workspace.

**Parameters:**
- `path`: The path to the file.
- `content`: The content to write (string or bytes).
- `append`: Whether to append to the file instead of overwriting.
- `confirm`: Whether to ask for confirmation before writing.
- `validate_content`: Whether to validate the content for security.

**Returns:**
- `True` if the file was written, `False` if the operation was cancelled.

**Raises:**
- `WorkspaceSecurityError`: If the path is outside the allowed boundaries.

**Example:**
```python
# Write text to a file
workspace.write_file("output/result.txt", "Analysis complete")

# Append to a log file without confirmation
workspace.write_file("logs/app.log", "New log entry\n", 
                     append=True, confirm=False)

# Write binary data
workspace.write_file("images/generated.png", image_data, 
                     validate_content=False)
```

### File Management Operations

#### `delete_file`

```python
def delete_file(
    self, 
    path: Union[str, Path], 
    confirm: bool = True
) -> bool
```

Deletes a file or directory from the workspace.

**Parameters:**
- `path`: The path to the file or directory.
- `confirm`: Whether to ask for confirmation before deleting.

**Returns:**
- `True` if the file was deleted, `False` if the operation was cancelled.

**Raises:**
- `WorkspaceSecurityError`: If the path is outside the allowed boundaries.
- `FileNotFoundError`: If the file does not exist.

**Example:**
```python
# Delete a file with confirmation
workspace.delete_file("temp/old_data.txt")

# Delete a directory without confirmation
workspace.delete_file("output/cache", confirm=False)
```

#### `rename_file`

```python
def rename_file(
    self, 
    old_path: Union[str, Path], 
    new_path: Union[str, Path], 
    confirm: bool = True
) -> bool
```

Renames a file or directory in the workspace.

**Parameters:**
- `old_path`: The current path of the file or directory.
- `new_path`: The new path for the file or directory.
- `confirm`: Whether to ask for confirmation before renaming.

**Returns:**
- `True` if the file was renamed, `False` if the operation was cancelled.

**Raises:**
- `WorkspaceSecurityError`: If either path is outside the allowed boundaries.
- `FileNotFoundError`: If the source file does not exist.
- `FileExistsError`: If the destination file already exists.

**Example:**
```python
# Rename a file
workspace.rename_file("draft.txt", "final.txt")

# Move a file to a subdirectory
workspace.rename_file("report.pdf", "archive/2023/report.pdf")
```

### Directory Operations

#### `create_directory`

```python
def create_directory(
    self, 
    path: Union[str, Path], 
    confirm: bool = True
) -> bool
```

Creates a directory in the workspace.

**Parameters:**
- `path`: The path to the directory.
- `confirm`: Whether to ask for confirmation before creating.

**Returns:**
- `True` if the directory was created, `False` if the operation was cancelled.

**Raises:**
- `WorkspaceSecurityError`: If the path is outside the allowed boundaries.
- `FileExistsError`: If a file (not directory) with the same name already exists.

**Example:**
```python
# Create a directory
workspace.create_directory("output/reports")

# Create nested directories
workspace.create_directory("data/processed/2023/Q4")
```

#### `list_directory`

```python
def list_directory(
    self, 
    path: Union[str, Path] = "",
    pattern: Optional[str] = None,
    include_hidden: bool = False
) -> List[Dict[str, Any]]
```

Lists the contents of a directory in the workspace.

**Parameters:**
- `path`: The path to the directory (empty string for workspace root).
- `pattern`: Optional glob pattern for filtering files.
- `include_hidden`: Whether to include hidden files.

**Returns:**
- A list of dictionaries containing file information.

**Raises:**
- `WorkspaceSecurityError`: If the path is outside the allowed boundaries.
- `NotADirectoryError`: If the path is not a directory.
- `FileNotFoundError`: If the directory does not exist.

**Example:**
```python
# List all files in the workspace root
all_files = workspace.list_directory()

# List Python files in a specific directory
python_files = workspace.list_directory("src", pattern="*.py")

# List all files including hidden ones
all_files = workspace.list_directory(include_hidden=True)
```

### Utility Methods

#### `is_within_workspace`

```python
def is_within_workspace(self, path: Union[str, Path]) -> bool
```

Checks if a path is within the allowed workspace boundaries.

**Parameters:**
- `path`: The path to check.

**Returns:**
- `True` if the path is within the allowed boundaries, `False` otherwise.

**Example:**
```python
if workspace.is_within_workspace("/home/user/documents/file.txt"):
    print("Path is within the workspace")
else:
    print("Path is outside the workspace")
```

#### `get_workspace_root`

```python
def get_workspace_root(self) -> str
```

Gets the root path of the workspace.

**Returns:**
- The root path of the workspace.

**Example:**
```python
root = workspace.get_workspace_root()
print(f"Workspace root: {root}")
```

#### `get_allowed_paths`

```python
def get_allowed_paths(self) -> List[str]
```

Gets the list of allowed paths.

**Returns:**
- The list of allowed paths.

**Example:**
```python
paths = workspace.get_allowed_paths()
print("Allowed paths:")
for path in paths:
    print(f"- {path}")
```

### Transaction Methods

#### `begin_transaction`

```python
def begin_transaction(self) -> None
```

Begins a new transaction for rollback capability.

**Example:**
```python
# Begin a transaction
workspace.begin_transaction()

try:
    # Perform multiple operations
    workspace.write_file("config.json", json_content)
    workspace.write_file("readme.md", readme_content)
    
    # Commit the transaction if everything succeeds
    workspace.commit_transaction()
except Exception as e:
    # Rollback on error
    workspace.rollback_transaction()
    print(f"Error: {e}")
```

#### `commit_transaction`

```python
def commit_transaction(self) -> None
```

Commits the current transaction and cleans up backups.

#### `rollback_transaction`

```python
def rollback_transaction(self) -> None
```

Rolls back all operations in the current transaction.

## Error Handling

The Workspace Manager uses custom exceptions to handle errors:

### `WorkspaceSecurityError`

Raised when an operation attempts to access a path outside the allowed workspace boundaries or when a security violation is detected.

Example handling:

```python
try:
    content = workspace.read_file(user_input_path)
    print(content)
except WorkspaceSecurityError as e:
    print(f"Security violation: {e}")
    # Log the attempt
    logger.warning(f"Security violation: {e}")
except FileNotFoundError:
    print(f"File not found: {user_input_path}")
```

## Best Practices

### Security

1. **Validate User Input**: Always validate user-provided paths before passing them to Workspace Manager methods.
2. **Use Transactions**: Wrap multiple related operations in transactions to ensure atomicity.
3. **Handle Security Errors**: Properly catch and handle `WorkspaceSecurityError` exceptions.
4. **Limit Write Operations**: Require confirmation for write operations in production environments.

### Usage

1. **Relative Paths**: Use relative paths where possible to make code more portable.
2. **Content Validation**: Enable content validation for user-generated content.
3. **Proper Path Handling**: Use `Path` objects from the `pathlib` module for better path manipulation.
4. **Error Recovery**: Implement proper rollback procedures for error conditions.

## Common Operation Examples

### Reading and Writing Files

```python
# Reading a file
config_content = workspace.read_file("config/settings.json")

# Parsing JSON content
import json
config = json.loads(config_content)

# Modifying and writing back
config["debug"] = True
workspace.write_file("config/settings.json", json.dumps(config, indent=2))
```

### File Operations with Transactions

```python
# Begin a transaction
workspace.begin_transaction()

try:
    # Read a file
    content = workspace.read_file("document.txt")
    
    # Modify the content
    modified_content = content.replace("old text", "new text")
    
    # Write back the modified content
    workspace.write_file("document.txt", modified_content)
    
    # Create a backup copy
    workspace.write_file("backups/document.txt.bak", content)
    
    # Commit the transaction
    workspace.commit_transaction()
    print("Document updated successfully")
except Exception as e:
    # Rollback on error
    workspace.rollback_transaction()
    print(f"Error updating document: {e}")
```

### Directory Management

```python
# List files in a directory
files = workspace.list_directory("data")

# Filter and process specific file types
python_files = [f for f in files if f["name"].endswith(".py")]
for file in python_files:
    print(f"Processing {file['name']}")
    content = workspace.read_file(f"data/{file['name']}")
    # Process Python file...

# Create a new directory for outputs
workspace.create_directory("output/processed")
```

### Checking File Existence and Type

```python
# Check if a file exists before reading
if workspace.file_exists("data/input.csv"):
    # Get file information
    file_info = workspace.get_file_info("data/input.csv")
    
    # Check file type and size
    if file_info["type"] == "csv" and file_info["size"] > 0:
        content = workspace.read_file("data/input.csv")
        # Process CSV data...
    else:
        print("File is empty or not a CSV file")
else:
    print("Input file does not exist")
```

### Handling User Input Paths

```python
def process_user_file(workspace, user_path):
    """Process a file specified by the user."""
    try:
        # Check if the path is within the workspace
        if not workspace.is_within_workspace(user_path):
            print("Error: The specified path is outside the allowed workspace")
            return False
        
        # Check if the file exists
        if not workspace.file_exists(user_path):
            print(f"Error: File '{user_path}' does not exist")
            return False
        
        # Read and process the file
        content = workspace.read_file(user_path)
        # Process content...
        
        return True
    except WorkspaceSecurityError as e:
        print(f"Security violation: {e}")
        return False
    except Exception as e:
        print(f"Error processing file: {e}")
        return False
```

---

## Internal Implementation Details

For developers maintaining the Workspace Manager, here are some key implementation details:

### Path Validation Process

1. `_normalize_path`: Converts a path to an absolute path with user directory expansion.
2. `_is_path_allowed`: Checks if a path is within any of the allowed paths.
3. `_validate_path`: Validates a path against security constraints, resolving symlinks.

### Transaction Management

1. File operations create `FileOperation` objects with the operation type, path, and content.
2. Backups are stored in temporary directories using `tempfile.mkdtemp()`.
3. Rollbacks process operations in reverse order, restoring from backups.
4. Cleanup removes all backup files and directories after commit or rollback.

### Content Validation

The content validation system checks for dangerous patterns that might indicate code injection attempts. This is a basic protection mechanism and should be enhanced for specific use cases.
