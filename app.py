"""
Main entry point for the Ai Agent Application.

This module provides the main command-line interface for the application.
"""

import argparse
import logging
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config_manager import ConfigManager
from api_interface import APIInterface
from file_operations import FileOperations
from commands import Commands

def setup_logging(config: Dict[str, Any]) -> None:
    """
    Set up logging based on configuration.

    Args:
        config: The logging configuration.
    """

    log_level = getattr(logging, config.get("level", "INFO"))
    log_format = config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handlers = [logging.StreamHandler()]

    if config.get("log_to_file", False):
        log_file = config.get("log_file", "~/.ai_agent/app.log")
        log_file_path = Path(os.path.expanduser(log_file))
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file_path))

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )

def create_default_config() -> None:
    """
    Create a default configuration file if it doesn't exist.
    """

    default_config_path = Path(os.path.expanduser(ConfigManager.DEFAULT_CONFIG_PATH))

    if default_config_path.exists():
        return

    default_config = {
        "default_provider": "claude",
        "providers": {
            "claude": {
                "api_key": "",
                "api_url": "https://api.anthropic.com/v1/messages",
                "model": "claude-3-opus-20240229",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 30,
                "headers": {
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
            },
            "openai": {
                "api_key": "",
                "api_url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4-turbo",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 30,
                "headers": {
                    "content-type": "application/json"
                }
            },
            "local": {
                "api_key": "",
                "api_url": "http://localhost:8000/v1/chat/completions",
                "model": "local-model",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 30,
                "headers": {
                    "content-type": "application/json"
                }
            }
        },
        "workspace": {
            "default_path": "~/ai_workspace",
            "allowed_paths": ["~/ai_workspace", "~/projects"]
        },
        "security": {
            "audit_log_path": "~/.ai_agent/audit.jsonl",
            "history_path": "~/.ai_agent/history.jsonl",
            "require_confirmation_for_writes": True,
            "max_execution_time": 10,
            "allow_network_access": False
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "log_to_file": True,
            "log_file": "~/.ai_agent/app.log"
        }
    }
    
    default_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(default_config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"Created default configuration at {default_config_path}")

def main() -> None:
    """
    Main entry point for the application.
    """

    parser = argparse.ArgumentParser(description="AI Agent Application")
    
    parser.add_argument(
        "--config", "-c",
        help="Path to the configuration file"
    )
    
    parser.add_argument(
        "--provider", "-p",
        help="The AI provider to use"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize the default configuration file"
    )

    file_ops_group = parser.add_argument_group("File Operations")
    
    file_ops_group.add_argument(
        "--generate-tests",
        metavar="FILE",
        help="Generate tests for a file"
    )
    
    file_ops_group.add_argument(
        "--evaluate-syntax",
        metavar="FILE",
        help="Evaluate a file for syntax mistakes"
    )
    
    file_ops_group.add_argument(
        "--generate-docs",
        metavar="DIRECTORY",
        help="Generate documentation for files in a directory"
    )
    
    file_ops_group.add_argument(
        "--batch-process",
        metavar="DIRECTORY",
        help="Process all files in a directory"
    )
    
    file_ops_group.add_argument(
        "--operation",
        choices=["tests", "syntax", "docs"],
        help="Operation to perform when batch processing"
    )
    
    file_ops_group.add_argument(
        "--pattern",
        default="*.py",
        help="File pattern for batch operations (default: *.py)"
    )
    
    args = parser.parse_args()
    
    # Initialize default configuration if requested
    if args.init:
        create_default_config()
        return
    
    try:
        # Load configuration
        config_manager = ConfigManager(args.config)
        
        # Set up logging
        logging_config = config_manager.get_logging_config()
        if args.debug:
            logging_config["level"] = "DEBUG"
        
        setup_logging(logging_config)
        logger = logging.getLogger(__name__)
        
        # Create API interface
        api = APIInterface(args.config, args.provider)
        file_ops = FileOperations(config_manager)
        commands = Commands(api, file_ops)
        
        logger.info("AI Agent Application initialized successfully")

        if args.generate_tests:
            result = commands.generate_tests(args.generate_tests)
            print(result)
            return
            
        if args.evaluate_syntax:
            result = commands.evaluate_syntax(args.evaluate_syntax)
            print(result)
            return
            
        if args.generate_docs:
            result = commands.generate_documentation(args.generate_docs, args.pattern)
            print(result)
            return
            
        if args.batch_process:
            if not args.operation:
                parser.error("--operation is required with --batch-process")
            result = commands.batch_process_directory(args.batch_process, args.operation, args.pattern)
            print(result)
            return
        
        # TODO: Add interactive CLI or other interfaces
        print("AI Agent Application is ready.")
        print(f"Using provider: {api.provider}")
        print("\nAvailable commands:")
        print("1. generate-tests <file> - Generate tests for a file")
        print("2. evaluate-syntax <file> - Evaluate a file for syntax mistakes")
        print("3. generate-docs <directory> - Generate documentation for files in a directory")
        print("4. batch-process <directory> <operation> [pattern] - Process multiple files")
        print("5. exit - Exit the application")
        
        print("\nEnter messages (Ctrl+C or 'exit' to quit):")
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                parts = user_input.split()
                if not parts:
                    continue
                
                command = parts[0].lower()
                
                if command == "generate-tests" and len(parts) >= 2:
                    result = commands.generate_tests(parts[1])
                    print(result)
                    
                elif command == "evaluate-syntax" and len(parts) >= 2:
                    result = commands.evaluate_syntax(parts[1])
                    print(result)
                    
                elif command == "generate-docs" and len(parts) >= 2:
                    pattern = parts[2] if len(parts) >= 3 else "*.py"
                    result = commands.generate_documentation(parts[1], pattern)
                    print(result)
                    
                elif command == "batch-process" and len(parts) >= 3:
                    directory = parts[1]
                    operation = parts[2]
                    pattern = parts[3] if len(parts) >= 4 else "*.py"
                    
                    if operation not in ["tests", "syntax", "docs"]:
                        print(f"Invalid operation: {operation}")
                        continue
                    
                    result = commands.batch_process_directory(directory, operation, pattern)
                    print(result)
                    
                else:
                    print("Invalid command or missing arguments.")
                    print("Usage:")
                    print("  generate-tests <file>")
                    print("  evaluate-syntax <file>")
                    print("  generate-docs <directory> [pattern]")
                    print("  batch-process <directory> <operation> [pattern]")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"Error: {e}")
    
    except Exception as e:
        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        
        logger = logging.getLogger(__name__)
        logger.error(f"Initialization error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
