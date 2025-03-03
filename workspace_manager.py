import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Union
import tempfile
import logging
from dataclasses import dataclass
from enum import Enum

class FileOperationType(Enum):
    """
    Types of file operations that can be performed.
    """
    READ = "read"
    WRITE = "write"
    APPEND = "append"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_DIR = "create_dir"
    LIST_DIR = "list_dir"

@dataclass
class FileOperation:
    """
    Represents a file operation with rollback capability.
    """
    operation_type: FileOperationType
    path: Path
    content: Optional[bytes] = None
    new_path: Optional[Path] = None
    backup_path: Optional[Path] = None

class WorkspaceSecurityError(Exception):
    """
    Exception raised for workspace security violations.
    """
    pass

class WorkspaceManager:
    """
    Manages a secure workspace with strict file access controls.

    This class provides safe file operations within a designated root directory,
    preventing access to any files outside of the directory.
    """

    def __init__(
            self,
            root_path: str,
            allowed_paths: Optional[List[str]] = None,
            require_confirmation_for_writes: bool = True,
            logger: Optional[logging.Logger] = None
        ):
        """
        Initialize the workspace manager.

        Args:
            root_path: The root path of the workspace.
            allowed_paths: Additional allowed paths outside the root.
            require_confirmation_for_writes: Whether to require confirmation for write operations.
            logger: Logger instance to use.
        """

        self.root_path = self._normalize_path(root_path)
        self.allowed_paths = [self.root_path]

        if allowed_paths:
            for path in allowed_paths:
                normalized_path = self._normalize_path(path)
                if normalized_path not in self.allowed_paths:
                    self.allowed_paths.append(normalized_path)
        
        self.require_confirmation_for_writes = require_confirmation_for_writes
        self.logger = logger or logging.getLogger(__name__)
        self.transaction_operations: List[FileOperation] = []

        self._ensure_workspace_exists()
    
    def _normalize_path(self, path: str) -> Path:
        """
        Normalize a path to an absolute path with user directory expansion.

        Args:
            path: The path to normalize

        Returns:
            The normalized path as a Path object.
        """

        expanded_path = os.path.expanduser(path)
        return Path(os.path.abspath(expanded_path))
    
    def _ensure_workspace_exists(self) -> None:
        """
        Ensure the workspace root directory exists.
        """

        for path in self.allowed_paths:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created workspace directory: {path}")

    def _is_path_allowed(self, path: Union[str, Path]) -> bool:
            """
            Check if a given path is within the allowed workspace boundaries.
            
            Args:
                path: The path to check.
                
            Returns:
                True if the path is within the allowed boundaries, False otherwise.
            """
            normalized_path = self._normalize_path(str(path))
            
            for allowed_path in self.allowed_paths:
                try:
                    normalized_path.relative_to(allowed_path)
                    return True
                
                except ValueError:
                    continue
            
            return False
    
    def _validate_path(self, path: Union[str, Path]) -> Path:
        """
        Validate a path is within the allowed workspace boundaries.

        Args:
            path: The path to validate.

        Returns:
            The normalized path if valid.

        Raises:
            WorkspaceSecurityError: If the path is outside the allowed boundaries.
        """

        normalized_path = self._normalize_path(str(path))

        real_path = normalized_path.resolve()
        if not self._is_path_allowed(real_path):
            self.logger.warning(f"Attempted access to path that resolves outside workspace: {normalized_path} -> {real_path}")
            raise WorkspaceSecurityError(f"Path resolves to location outside the allowed workspace: {path}")
        
        if not self._is_path_allowed(normalized_path):
            self.logger.warning(f"Attempted access to unauthorized path: {normalized_path}")
            raise WorkspaceSecurityError(f"Path is outside the allowed workspace: {path}")
        
        return normalized_path
    
    def _get_relative_path(self, path: Union[str, Path]) -> str:
        """"
        Get the path relative to the workspace root.

        Args:
            path: The path to convert.

        Returns:
            The path relative to the workspace root.
        """

        normalized_path = self._normalize_path(str(path))

        for allowed_path in self.allowed_paths:
            try:
                relative_path = normalized_path.relative_to(allowed_path)
                return str(relative_path)

            except ValueError:
                continue

        raise WorkspaceSecurityError(f"Path is outside the allowed workspace: {path}")
    
    def _backup_file(self, path: Path) -> Optional[Path]:
        """
        Create a backup of a file for potential rollback.

        Args:
            path: The path of the file to backup.

        Returns:
            The path of the backup file, or None if the file doesn't exist.
        """

        if not path.exists():
            return None

        backup_dir = tempfile.mkdtemp(prefix="ai_agent_backup_")
        backup_path = Path(backup_dir) / path.name

        if path.is_file():
            shutil.copy2(path, backup_path)
        else:
            shutil.copytree(path, backup_path)
        
        return backup_path
    
    def _rollback_operation(self, operation: FileOperation) -> None:
        """
        Rollback a file operation.

        Args:
            operation: The operation to rollback.
        """

        if operation.backup_path is None:
            if operation.operation_type == FileOperationType.CREATE_DIR:
                path = operation.path
                if path.exists() and path.is_dir():
                    shutil.rmtree(path)
            
            elif operation.operation_type == FileOperation.WRITE:
                path = operation.path
                if path.exists() and path.is_file():
                    path.unlink()
            
            return
        
        if operation.backup_path.exists():
            if operation.path.exists():
                if operation.path.is_file():
                    operation.path.unlink()
                else:
                    shutil.rmtree(operation.path)

            if operation.backup_path.is_file():
                shutil.copy2(operation.backup_path, operation.path)
            else:
                shutil.copytree(operation.backup_path, operation.path)
        
