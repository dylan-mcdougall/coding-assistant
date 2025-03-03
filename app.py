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
    
    # Create directory if it doesn't exist
    default_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the default configuration
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
        
        logger.info("AI Agent Application initialized successfully")
        
        # TODO: Add interactive CLI or other interfaces
        print("AI Agent Application is ready.")
        print(f"Using provider: {api.provider}")
        
        # Simple interactive mode for testing
        print("\nEnter messages (Ctrl+C or 'exit' to quit):")
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                response = api.send_message(user_input)
                print(f"\n{response}\n")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"Error: {e}")
    
    except Exception as e:
        # If we can't even load the configuration, use basic logging
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
