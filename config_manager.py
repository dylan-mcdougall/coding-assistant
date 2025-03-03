"""
Configuration Manager for AI Agent Application.

This module contains the functionality for loading, validating, and accessing
configuration settings from the config.json file.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                    ConfigManager    
#║ 
#║                                      Contents:
#║
#║                                load_config
#║                                validate_config
#║                                get_provider_config
#║                                get_default_provider
#║                                get_workspace_config
#║                                get_security_config
#║                                get_logging_config
#║                                save_config 
#║                                update_provider
#║                                set_default_provider
#║                                get_available_providers
#║                             
#╚══════════════════════════════════════════════════════════════════════════════════════╝

class ConfigManager:
    """
    Manges the configuration settings for the AI Agent Application.
    """

    DEFAULT_CONFIG_PATH = "~/.ai_agent/config.json"
    REQUIRED_PROVIDER_FIELDS = ["api_url", "model"]

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialization of the configuration manager.

        Args:
            config_path: Path to the configuration file. If None, uses the default path.
        """

        self.config_path = Path(os.path.expanduser(config_path or self.DEFAULT_CONFIG_PATH))
        self.config: Dict[str, Any] = {}
        self.load_config()


#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                    load_config                                  
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def load_config(self) -> None:
        """
        Load configuration from the config file.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            json.JSONDecodeError: If the configuration file contains invalid JSON
        """

        try:
            if not self.config_path.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)

            self._validate_config()
            logger.info(f"Configuration loaded successfully from {self.config_path}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuratio file: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise


#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                   validate_config                                 
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def _validate_config(self) -> None:
        """
        Validate the loaded configuration.

        Raises:
            ValueError: If the configuration is invalid.
        """

        if 'providers' not in self.config:
            raise ValueError("Missing 'providers' section in configuration")
        
        if not self.config['providers']:
            raise ValueError("No providers defined in configuration")
        
        if 'default_provider' not in self.config:
            logger.warning("No default provider specified, using the first available one.")
            self.config['default_provider'] = next(iter(self.config['providers'].keys()))
        elif self.config['default_provider'] not in self.config['providers']:
            logger.warning(f"Default provider '{self.config['default_provider']}' not found in providers, using the first available one.")
            self.config['default_provider'] = next(iter(self.config['providers'].keys()))

        for provider, settings in self.config['providers'].items():
            for field in self.REQUIRED_PROVIDER_FIELDS:
                if field not in settings:
                    raise ValueError(f"Provider '{provider}' is missing required field '{field}'")
                
                
#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                 get_provider_config                                
#╚══════════════════════════════════════════════════════════════════════════════════════╝

        
    def get_provider_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific provider.

        Args:
            provider: The provider to get configuration for.
                If None, uses the default provider.
        
        Returns:
            ValueError: If the provider doesn't exist
        """

        provider = provider or self.config.get('default_provider')
        if provider not in self.config['providers']:
            raise ValueError(f"Provider '{provider}' not found in configuration")
        
        return self.config['providers'][provider]
    

#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                get_default_provider                               
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def get_default_provider(self) -> str:
        """
        Get the default provider name.

        Returns:
            The name of the default provider.
        """

        return self.config.get('default_provider')
    

#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                get_workspace_config                              
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def get_workspace_config(self) -> Dict[str, Any]:
        """
        Get the workspace configuration.

        Returns:
            The workspace configuration.
        """

        return self.config.get('workspace', {})
    

#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                get_security_config                               
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def get_security_config(self) -> Dict[str, Any]:
        """
        Get the security configuration.

        Returns:
            The security configuration.
        """

        return self.config.get('security', {})
    

#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                 get_logging_config                               
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get the logging configuration.

        Returns:
            The logging configuration.
        """

        return self.config.get('logging', {})
    

#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                    save_config                              
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def save_config(self) -> None:
        """
        Save the current configuration to the config file.

        Raises:
            IOError: If there's an error writing the configuration.
        """

        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved successfully to {self.config_path}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    

#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                   update_provider                               
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def update_provider(self, provider: str, settings: Dict[str, Any]) -> None:
        """
        Update a provider's settings.

        Args:
            provider: The provider to update.
            settings: The new settings.
        """

        if 'providers' not in self.config:
            self.config['providers'] = {}
        
        self.config['providers'][provider] = settings
        logger.info(f"Updated settings for provider '{provider}'")
    

#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                                set_default_provider                               
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def set_default_provider(self, provider: str) -> None:
        """
        Set the default provider.

        Args:
            provider: The provider to be set as default.

        Raises:
            ValueError: If the provider doesn't exist.
        """

        if provider not in self.config['providers']:
            raise ValueError(f"Cannot set default provider: '{provider}' not found in configuration")
        
        self.config['default_provider'] = provider
        logger.info(f"Set default provider to '{provider}'")
    

#╔══════════════════════════════════════════════════════════════════════════════════════╗
#║                                    (づ ◕‿◕ )づ        
#║                             
#║                               get_available_providers                               
#╚══════════════════════════════════════════════════════════════════════════════════════╝


    def get_available_providers(self) -> list:
        """"
        Get a list of available providers.

        Returns:
            List of provider names.
        """

        return list(self.config.get('providers', {}).keys())
