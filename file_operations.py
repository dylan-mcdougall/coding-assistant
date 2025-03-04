"""
File Operations Module for AI Agent Application.

This module provides secure file operations within allowed workspace directories.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class FileOperations:
    """
    Provides secure file operations within allowed workspace directories.
    """

    def __init__(self, config_manger: ConfigManager):
        """
        Initialize the file operations.

        Args:
            config_manager: The configuration manager.
        """
        self.config_manager = config_manger
        self.workspace_config = config_manger.get_workspace_config()
        self.security_config = config_manger.get_security_config()
        self.allowed_paths = [
            Path(os.path.expanduser(path))
            for path in self.workspace_config.get("allowed_paths", [])
        ]

    def validate_path(self, path: Union[str, Path]) -> Path:
        """
        Validate a path is within allowed directories.

        Args:
            path: The path to validate.

        Returns:
            The resolved Path object.

        Raises:
            ValueError: If the path is not within allowed directories.
        """
        
        resolved_path = Path(os.path.expanduser(path)).resolve()

        if not any(
            str(resolved_path).startswith(str(allowed.resolve()))
            for allowed in self.allowed_paths
        ):
            logger.error(f"Path {resolved_path} is not within allowed directories.")
            raise ValueError(f"Path {resolved_path} is not within allowed directories.")
        
        return resolved_path

    def safe_read_file(self, path: Union[str, Path]) -> str:
        """
        Safely read a file from an allowed directory.

        Args:
            path: The path to the file.

        Returns:
            The file content.

        Raises:
            ValueError: If the path is not within allowd directories.
            FileNotFoundError: If the file doens't exist.
        """

        resolved_path = self.validate_path(path)

        try:
            logger.info(f"Reading file: {resolved_path}")
            with open(resolved_path, 'r') as f:
                content = f.read()
            return content
        
        except FileNotFoundError:
            logger.error(f"File not found: {resolved_path}")
            raise

        except Exception as e:
            logger.error(f"Error reading file: {resolved_path}")
            raise
        

    def safe_write_file(self, path: Union[str, Path], content: str, confirm: bool = None) -> None:
        """
        Safely write a file to an allowed directory.

        Args:
            path: The path to the file.
            content: The content to write.
            confirm: Whether to require confirmation (defaults to config setting).

        Raises:
            ValueError: If the path is not within allowed directories.
            PermissionError: If the writing is not confirmed.
        """

        resolved_path = self.validate_path(path)

        require_confirmation = self.security_config.get("require_confirmation_for_writes", True)
        if confirm is not None:
            require_confirmation = confirm

        if require_confirmation:
            confirmation = input(f"Do you want to write to {resolved_path}? (y/n): ")
            if confirmation.lower() not in ['y', 'ye', 'yes']:
                logger.info(f"Write operation cancelled for {resolved_path}")
                raise PermissionError(f"Write operation not confirmed for {resolved_path}")
            
        try:
            logger.info(f"Writing file: {resolved_path}")
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            with open(resolved_path, 'w') as f:
                f.write(content)

        except Exception as e:
            logger.error(f"Error writing file {resolved_path}: {e}")
            raise


    def safe_list_files(self, directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """
        Safely list files in an allowed directory.

        Args:
            directory: The directory to list files from.
            pattern: The glob pattern to match files.

        Returns:
            A list of file paths.

        Raises:
            ValueError: If the directory is not within allowed directories.
        """

        resolved_dir = self.validate_path(directory)

        if not resolved_dir.is_dir():
            logger.error(f"Not a directory: {resolved_dir}")
            raise ValueError(f"Not a directory: {resolved_dir}")
        
        try:
            logger.info(f"Listing files in directory: {resolved_dir}")
            return list(resolved_dir.glob(pattern))
        
        except Exception as e:
            logger.error(f"Error listing files in {resolved_dir}: {e}")
            raise
