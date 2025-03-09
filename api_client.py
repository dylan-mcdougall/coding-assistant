"""
API Client for AI Agent Application

This module provides a base class for API clients and implementations
for specific providers
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import requests
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

class Message:
    """
    Represents a message in a conversation.
    """

    def __init__(self, role: str, content: str):
        """
        Initialize a message.

        Args:
            role: The role of the message sender (e.g. 'user', 'assistant')
            content: The content of the message.
        """

        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the message to a dictionary.

        Returns:
            A dictionary representation of the message.
        """

        return {
            "role": self.role,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Message':
        """
        Create a message from a dictionary.

        Args:
            data: A dictionary containing 'role' and 'content' keys.

        Returns:
            A message object.
        """

        return cls(data['role'], data['content'])
    
class BaseAPIClient(ABC):
    """
    Base class for API clients
    """

    def __init__(
            self, 
            api_key: str, 
            api_url: str, 
            model: str,
            max_tokens: int = 4096,
            temperature: float = 0.7,
            timeout: int = 30, 
            **kwargs
            ):
        """
        Initialize the API client.

        Args:
            api_key: The API key for authentication.
            api_url: The URL of the API endpoint.
            model: The specific model to use.
            max_tokens: The maximum number of tokens to generate.
            temperature: The temperature to use for generation.
            timeout: The request timeout in seconds.
            **kwargs: Addtional provider specific parameters.
        """

        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.kwargs = kwargs
        self.headers = kwargs.get("headers", {})
        self.conversation_history: List[Message] =[]
        self._last_request_time = 0
        self._rate_limit_remaining = None
        self._rate_limit_reset = None

    @abstractmethod
    def format_prompt(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Format prompt for the API

        Args: 
            messages: The list of messages to format.

        Returns:
            The formatted prompt.
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse the API response.

        Args:
            response: The API response.

        Returns:
            The parsed response context.
        """
        pass

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: The role of the message sender.
            content: The content of the message.
        """

        self.conversation_history.append(Message(role, content))

    def clear_conversation(self) -> None:
        """
        Clear the conversation history.
        """
        self.conversation_history = []

    def _apply_rate_limiting(self) -> None:
        """
        Apply rate limiting based on the time since the last request.

        This is a simple implementation that ensures at least 1 second between requests.
        More sophisticated implimentations can use the rate limit informationm from the
        API response headers.
        """

        if not self._last_request_time:
            return
        
        if self._rate_limit_remaining is not None and self._rate_limit_remaining <= 1:
            if self._rate_limit_reset is not None:
                wait_time = max(0, self._rate_limit_reset - time.time())
                if wait_time > 0:
                    logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds.")
                    time.sleep(wait_time)
        
        else:
            elapsed = time.time() - self._last_request_time
            if elapsed < 1:
                time.sleep(1 - elapsed)
        
    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """
        Update rate limit information from response headers.

        Args:
            headers: The response headers.
        """
        pass

    def send_message(self, content: str) -> str:
        """
        Send a message to the API and get a response.

        Args:
            content: The message content.

        Returns:
            The response from the API.

        Raises:
            Exception: If there's an error communicating with the API.
        """
        self.add_message("user", content)

        try:
            self._apply_rate_limiting()

            messages = self.conversation_history
            payload = self.format_prompt(messages)

            logger.debug(f"Sending request to {self.api_url}")
            self._last_request_time = time.time()

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            self._update_rate_limit_info(response.headers)

            if response.status_code != 200:
                error_message = f"API request failed with status code {response.status_code}: {response.text}"
                logger.error(error_message)
                raise Exception(error_message)

            response_data = response.json()
            response_content = self.parse_response(response_data)

            self.add_message("assistant", response_content)
            return response_content
        
        except Timeout:
            error_message = f"Request to {self.api_url} timed out after {self.timeout} seconds"
            logger.error(error_message)
            raise Exception(error_message)

        except RequestException as e:
            error_message = f"Error communicating with the API: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(error_message)
            raise
        
class ClaudeAPIClient(BaseAPIClient):
    """
    API client for Claude.
    """

    def __init__(self, api_key: str, api_url: str, model: str, **kwargs):
        """
        Initialize the Claude API client.

        Args:
            api_key: The API key for authentication.
            api_url: The URL of the API endpoint.
            model: The model to use.
            **kwargs: Additional parameters.
        """

        super().__init__(api_key, api_url, model, **kwargs)

        self.headers.update({
            "x-api-key": self.api_key,
            "anthropic-version": self.kwargs.get("anthropic-version", "2023-06-01"),
            "content-type": "application/json"
        })

        self.system_content = None

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        Separate handling for system messages.

        Args:
            role: The role of the message sender.
            content: The content of the message.
        """

        if role == 'system':
            self.system_content = content
        else:
            super().add_message(role, content)

    def format_prompt(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Format the prompt for the Claude API.

        Args:
            messages: The list of messages to format.

        Returns:
            The formatted prompt.
        """

        formatted_messages = [msg.to_dict() for msg in messages]

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        if self.system_content:
            payload["system"] = self.system_content
        
        return payload
    
    def parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse the Claude API response.

        Args:
            response: The API response.

        Returns:
            The response content.
        """

        try:
            return response["content"][0]["text"]
        
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Claude API response: {e}")
            logger.debug(f"Response: {response}")
            raise Exception(f"Invalid response format from Claude API: {e}")
        
    def clear_conversation(self) -> None:
        """
        Clear the conversation history and system prompt.
        """
        super().clear_conversation()
        self.system_content = None
    
    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """
        Update rate limit information from Claude API response headers.

        Args:
            headers: The respons headers.
        """

        try:
            if "x-ratelimit-remaining" in headers:
                self._rate_limit_remaining = int(headers["x-ratelimit-remaining"])
            
            if "x-ratelimit-reset" in headers:
                self._rate_limit_reset = time.time() + int(headers["x-ratelimit-reset"])

        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing rate limit headers: {e}")
    

class OpenAIAPIClient(BaseAPIClient):
    """
    API client for OpenAI.
    """

    def __init__(self, api_key: str, api_url: str, model: str, **kwargs):
        """
        Initialize the OpenAI API Client.

        Args:
            api_key: The API key for authentication.
            api_url The URL of the API endpoint.
            model: The model to use.
            **kwargs: Additional parameters.
        """

        super().__init__(api_key, api_url, model, **kwargs)

        self.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "content-type": "application/json"
        })

    def format_prompt(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Format the prompt for the OpenAI API.

        Args:
            messages: The list of messages to format.

        Returns:
            The formatted prompt.
        """

        formatted_messages = [msg.to_dict() for msg in messages]

        return {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
    
    def parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse the OpenAI API response.

        Args:
            response: The API response.

        Returns:
            The response content.
        """

        try:
            return response["choices"][0]["message"]["content"]
        
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing the OpenAI API response: {e}")
            logger.debug(f"Response: {response}")
            raise Exception(f"Invalid response format from OpenAI API: {e}")
    
    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """
        Update rate limit information from OpenAI API response headers.

        Args:
            headers: The response headers.
        """
        
        try:
            if "x-ratelimit-remaining-requests" in headers:
                self._rate_limit_remaining = int(headers["x-ratelimit-remaining-requests"])
            
            if "x-ratelimit-reset-requests" in headers:
                self._rate_limit_reset = time.time() + int(headers["x-ratelimit-reset-requests"])
        
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing rate limit headers: {e}")


class GeminiAPIClient(BaseAPIClient):
    """
    API client for Google's Gemini API.
    """

    def __init__(self, api_key: str, api_url: str, model: str, **kwargs):
        """
        Initialize the Gemini API client.

        Args:
            api_key: The API key for authentication.
            api_url: The URL of the API endpoint.
            model: The model to use.
            **kwargs: Additional parameters.
        """

        super().__init__(api_key, api_url, model, **kwargs)

        self.headers.update({
            "x-goog-api-key": self.api_key,
            "content-type": "application/json"
        })

        self.system_content = None

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        Separate handling for system messages in Gemini.

        Args:
            role: The role of the message sender.
            content: The content of the message.
        """

        if role == 'system':
            self.system_content = content
        else:
            super().add_message(role, content)

    def format_prompt(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Format the prompt for the Gemini API.

        Args:
            messages: The list of messages to format.

        Returns:
            The formatted prompt.
        """

        formatted_contents = []

        if self.system_content:
            formatted_contents.append({
                "role": "system",
                "parts": [{"text": self.system_content}]
            })

        for msg in messages:
            formatted_contents.append({
                "role": "user" if msg.role == "user" else "model",
                "parts": [{"text": msg.content}]
            })
        
        payload = {
            "contents": formatted_contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
                "topP": 0.95,
                "topK": 40
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }

        return payload
    
    def parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse the Gemini API response.

        Args:
            response: The API response.

        Returns:
            The response content.
        """
        
        try:
            return response["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Gemini API response: {e}")
            logger.debug(f"Response: {response}")
            raise Exception(f"Invalid response format from Gemini API: {e}")

    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """
        Update rate limit information from Gemini API response headers.

        Args:
            headers: The response headers.
        """

        try:
            if "quota-remaining" in headers:
                self._rate_limit_remaining = int(headers["quota-remaining"])
            if "quota-reset" in headers:
                self._rate_limit_reset = time.time() + int(headers["quota-reset"])
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing rate limit headers: {e}")
    

class LocalAPIClient(BaseAPIClient):
    """
    API client for local models with OpenAI-compatible API.
    """
    
    def __init__(self, api_url: str, model: str, **kwargs):
        """
        Initialize the Local API client.
        
        Args:
            api_url: The URL of the API endpoint.
            model: The model to use.
            **kwargs: Additional parameters.
        """

        api_key = kwargs.pop("api_key", "")
        super().__init__(api_key, api_url, model, **kwargs)
        
        self.headers.update({
            "content-type": "application/json"
        })
    
    def format_prompt(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Format the prompt for the local API (OpenAI-compatible format).
        
        Args:
            messages: The list of messages to format.
        
        Returns:
            The formatted prompt.
        """

        formatted_messages = [msg.to_dict() for msg in messages]
        
        return {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
    
    def parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse the local API response (expected to be OpenAI-compatible).
        
        Args:
            response: The API response.
        
        Returns:
            The response content.
        """

        try:
            return response["choices"][0]["message"]["content"]
        
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing local API response: {e}")
            logger.debug(f"Response: {response}")
            raise Exception(f"Invalid response format from local API: {e}")
        
class APIClientFactory:
    """
    Factory for creating API clients.
    """

    @staticmethod
    def create_client(provider: str, config: Dict[str, Any]) -> BaseAPIClient:
        """
        Create an API client for the specified provider.

        Args:
            provider: The provider name.
            config: The provider configuration.

        Returns:
            An API client instance.
        
        Raises:
            ValueError: If the provider is not supported.
        """

        
        remaining_config = config.copy()
        for key in ["api_key", "api_url", "model"]:
            remaining_config.pop(key, None)

        if provider == "claude":
            return ClaudeAPIClient(
                api_key=config["api_key"],
                api_url=config["api_url"],
                model=config["model"],
                **remaining_config
            )
        
        elif provider == "openai":
            return OpenAIAPIClient(
                api_key=config["api_key"],
                api_url=config["api_url"],
                model=config["model"],
                **remaining_config
            )
        
        elif provider == "gemini":
            return GeminiAPIClient(
                api_key=config["api_key"],
                api_url=config["api_url"],
                model=config["model"],
                **remaining_config
            )
        
        elif provider == "local":
            return LocalAPIClient(
                api_url=config["api_url"],
                model=config["model"],
                **remaining_config
            )
        
        else:
            logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
