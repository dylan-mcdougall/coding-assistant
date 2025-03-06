"""
Commands Module for AI Agent Application.

This module provides command functions for file-based operations using AI.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

from config_manager import ConfigManager
from api_interface import APIInterface
from file_operations import FileOperations

logger = logging.getLogger(__name__)

class Commands:
    """
    Command functions for file-based operations using AI.
    """

    def __init__(self, api_interface: APIInterface, file_operations: FileOperations):
        """
        Initialize the commands.

        Args:
            api_interface: The API interface for communicating with AI.
            file_operations: The file operations module.
        """

        self.api = api_interface
        self.file_ops = file_operations

    def generate_tests(self, file_path: Union[str, Path]) -> str:
        """
        Generate tests for a file.

        Args:
            file_path: The path to the file.

        Returns:
            The generated test content.
        """

        try:
            file_content = self.file_ops.safe_read_file(file_path)
            file_name = Path(file_path).name

            # Boilerplate for now, will be replaced with scaffold at some point
            # Honestly scaffold might not even be necessary for these operations?
            self.api.add_system_message("""
            You are an expert programmer tasked with generating high-quality test code.
            Generate comprehensive tests that cover all public functions and methods,
            include both positive and negative test cases, and follow best practices.
            Return only the test code without explanations.
            """)

            prompt = f"""
            Generate unit tests for the following code in file '{file_name}':

            ```
            {file_content}
            ```
            """

            test_content = self.api.send_message(prompt)

            # Extract code from the response if explanation was included
            import re
            code_match = re.search(r'```(?:python)?\s*(.*?)```', test_content, re.DOTALL)
            if code_match:
                test_content = code_match.group(1).strip()

            file_path_obj = Path(file_path)
            test_file_path = file_path_obj.parent / f"test_{file_path_obj.name}"

            self.file_ops.safe_write_file(test_file_path, test_content)

            return f"Tests generated and saved to {test_file_path}"
        
        except Exception as e:
            logger.error(f"Error generating tests: {e}")
            return f"Error generating tests: {str(e)}"
        
    def evaluate_syntax(self, file_path: Union[str, Path]) -> str:
        """
        Evaluate a file for syntax mistakes.

        Args:
            file_path: The path to the file.

        Returns:
            The evaluation results.
        """

        try:
            file_content = self.file_ops.safe_read_file(file_path)
            file_name = Path(file_path).name

            self.api.add_system_message("""
            You are a code review expert. Analyze the provided code for:
            1. Syntax errors or mistakes
            2. Style issues
            3. Potential bugs or edge cases
            4. Suggestions for improvement
            
            Format your response as a structured, actionable report.
            """)

            prompt = f"""
            Perform a code review for the following file '{file_name}':

            ```
            {file_content}
            ```
            """

            evaluation = self.api.send_message(prompt)

            return evaluation
        
        except Exception as e:
            logger.error(f"Error evaluating syntax: {e}")
            return f"Error evaluating syntax: {str(e)}"
        
    def generate_documentation(self, directory_path: Union[str, Path],
                                file_pattern: str = "*.py") -> str:
        """
        Generate documentation for files in a directory.

        Args:
            directory_path: The path to the directory.
            file_pattern: The glob pattern to match files (default: *.py).

        Returns:
            Summary of documentation generation.
        """

        try:
            target_files = self.file_ops.safe_list_files(directory_path, file_pattern)

            if not target_files:
                return f"No file matching '{file_pattern}' found in '{directory_path}'"
            
            doc_dir = Path(directory_path) / "docs"
            doc_dir.mkdir(exist_ok=True)

            self.api.add_system_message("""
            You are a technical documentation expert. For each code file, create
            comprehensive documentation that includes:
            1. Module overview and purpose
            2. Detailed function/class documentation
            3. Usage examples
            4. Dependencies and requirements
            
            Format your documentation in Markdown.
            """)

            processed_files = []
            for file_path in target_files:
                file_content = self.file_ops.safe_read_file(file_path)
                file_name = file_path.name

                prompt = f"""
                Generate detailed documentation for the following file '{file_name}':
                
                ```
                {file_content}
                ```
                """

                doc_content = self.api.send_message(prompt)
                
                doc_file_path = doc_dir / f"{file_path.stem}_docs.md"
                self.file_ops.safe_write_file(doc_file_path, doc_content)
                processed_files.append((file_path.name, doc_file_path.name))
                
            index_content = "# Project Documentation\n\n"
            for original_name, doc_name in processed_files:
                index_content += f"- [{original_name}]({doc_name})\n"
                
            self.file_ops.safe_write_file(doc_dir / "index.md", index_content)
            
            return f"Documentation generated for {len(processed_files)} files in {doc_dir}"
            
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            return f"Error generating documentation: {str(e)}"
        
    def batch_process_directory(self, directory_path: Union[str, Path], 
                               operation: str, file_pattern: str = "*.py") -> str:
        """
        Process multiple files in a directory with a specified operation.
        
        Args:
            directory_path: The path to the directory.
            operation: The operation to perform ('tests', 'syntax', 'docs').
            file_pattern: The glob pattern to match files.
            
        Returns:
            Summary of batch processing.
        """

        try:
            files = self.file_ops.safe_list_files(directory_path, file_pattern)
            
            if not files:
                return f"No files matching '{file_pattern}' found in {directory_path}"
            
            results = []
            
            for file_path in files:
                if operation == 'tests':
                    result = self.generate_tests(file_path)
                elif operation == 'syntax':
                    result = self.evaluate_syntax(file_path)
                else:
                    result = f"Unsupported operation '{operation}' for {file_path}"
                
                results.append(f"{file_path.name}: {result}")
            
            summary = f"Processed {len(files)} files with operation '{operation}':\n\n"
            summary += "\n".join(results)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return f"Error in batch processing: {str(e)}"
