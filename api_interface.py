"""
API Interface for AI Agent Application.

This module provides the main interface for interacting with the AI APIS.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
import os
from pathlib import Path

from config_manager import ConfigManager
from api_client import Message, BaseAPIClient, APIClientFactory

logger = logging.getLogger(__name__)

class APIInterface:
    """
    Main interface for interacting with AI APIs.
    """

    def __init__(self, config_path: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize the API interface.

        Args:
            config_path: Path to the configuration file. If None, uses the default path.
            provider: The provider to use. If None, uses the default provider from the config.
        """

        self.config_manager = ConfigManager(config_path)
        self.provider = provider or self.config_manager.get_default_provider()
        self.client = self._create_client()
        self._setup_audit_logging()
    
    def _create_client(self) -> BaseAPIClient:
        """
        Create an API client based on the current provider.

        Returns:
            An API client instance.
        """

        try:
            provider_config = self.config_manager.get_provider_config(self.provider)
            return APIClientFactory.create_client(self.provider, provider_config)
        
        except Exception as e:
            logger.error(f"Error creating the API client: {e}")
            raise

    def _setup_audit_logging(self) -> None:
        """
        Set up audit loggging.
        """

        security_config = self.config_manager.get_security_config()
        self.audit_log_path = Path(os.path.expanduser(
            security_config.get("audit_log_path", "~/.ai_agent/audit.jsonl")
        ))
        self.history_path = Path(os.path.expanduser(
            security_config.get("history_path", "~/.ai_agent/history.jsonl")
        ))

        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def _log_audit(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: The type of event.
            data: The event data.
        """

        import time
        
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "provider": self.provider,
            **data
        }
        
        try:
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(event) + "\n")
        
        except Exception as e:
            logger.error(f"Error writing to audit log: {e}")

    def _log_history(self, role: str, content: str) -> None:
        """
        Log a message to the conversation history file.
        
        Args:
            role: The role of the message sender.
            content: The content of the message.
        """

        import time
        
        entry = {
            "timestamp": time.time(),
            "provider": self.provider,
            "role": role,
            "content": content
        }
        
        try:
            with open(self.history_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        
        except Exception as e:
            logger.error(f"Error writing to history log: {e}")

    def send_message(self, content: str) -> str:
        """
        Send a message to the API and get a response.
        
        Args:
            content: The message content.
        
        Returns:
            The response from the API.
        """

        logger.info(f"Sending message to {self.provider} API")
        
        try:
            # Log the request
            self._log_audit("api_request", {"content": content})
            self._log_history("user", content)
            
            # Send the message
            response = self.client.send_message(content)
            
            # Log the response
            self._log_audit("api_response", {"content": response})
            self._log_history("assistant", response)
            
            return response
        
        except Exception as e:
            error_message = f"Error sending message: {str(e)}"
            logger.error(error_message)
            
            # Log the error
            self._log_audit("api_error", {"error": error_message})
            
            raise

    def clear_conversation(self) -> None:
        """Clear the conversation history."""

        self.client.clear_conversation()
        logger.info("Conversation history cleared")
        self._log_audit("conversation_cleared", {})

    def switch_provider(self, provider: str) -> None:
        """
        Switch to a different provider.
        
        Args:
            provider: The provider to switch to.
        
        Raises:
            ValueError: If the provider doesn't exist.
        """

        if provider not in self.config_manager.get_available_providers():
            raise ValueError(f"Provider '{provider}' not found in configuration")
        
        self.provider = provider
        self.client = self._create_client()
        logger.info(f"Switched to provider: {provider}")
        self._log_audit("provider_switched", {"new_provider": provider})

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history.
        
        Returns:
            The conversation history as a list of dictionaries.
        """
        
        return [msg.to_dict() for msg in self.client.conversation_history]
    
    def add_system_message(self, content: str) -> None:
        """
        Add a system message to the conversation history.
        
        Args:
            content: The message content.
        """

        self.client.add_message("system", content)
        self._log_history("system", content)
        logger.info("Added system message to conversation")
        self._log_audit("system_message_added", {"content": content})
