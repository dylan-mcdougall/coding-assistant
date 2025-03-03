# AI Agent Application Documentation

## Project Overview

The AI Agent Application is a secure CLI-based tool designed for personal developer use that interacts with various AI model providers through their APIs. The application follows a modular architecture with a strong focus on security, allowing for interactions with different AI providers while maintaining strict workspace boundaries and comprehensive audit logging.

This documentation covers the key components that have been implemented so far.

## Core Components

### 1. Configuration Management (`config_manager.py`)

The `ConfigManager` class provides the foundation for loading, validating, and accessing application configuration settings.

#### Key Functions:

- **Loading Configuration**: Loads settings from a JSON config file (default: `~/.ai_agent/config.json`)
- **Configuration Validation**: Ensures all required fields are present and valid
- **Provider Configuration Access**: Retrieves configuration for specific AI providers
- **Workspace & Security Settings**: Manages secure workspace paths and security parameters
- **Configuration Updates**: Allows updating and saving configuration changes

#### Usage Examples:

```python
# Create a config manager with default path
config_manager = ConfigManager()

# Or with a custom path
config_manager = ConfigManager("~/custom/config.json")

# Get configuration for a specific provider
claude_config = config_manager.get_provider_config("claude")

# Get the default provider name
default_provider = config_manager.get_default_provider()

# Get security configuration
security_config = config_manager.get_security_config()

# Update a provider's settings
config_manager.update_provider("claude", {"api_key": "new_key", "temperature": 0.8})

# Save configuration changes
config_manager.save_config()
```

#### Configuration Structure:

The configuration file has the following structure:
- `default_provider`: The default AI provider to use
- `providers`: Settings for each AI provider (API keys, URLs, models, etc.)
- `workspace`: Directories allowed for AI agent operations
- `security`: Audit logging paths and security restrictions
- `logging`: Logging configuration (level, format, output paths)

### 2. API Client (`api_client.py`)

This module provides a flexible architecture for communicating with different AI model APIs through a common interface.

#### Key Components:

- **Message Class**: Represents a message in a conversation (role, content)
- **BaseAPIClient**: Abstract base class with common functionality
- **Provider-Specific Clients**:
  - `ClaudeAPIClient`: Client for Anthropic's Claude API
  - `OpenAIAPIClient`: Client for OpenAI's API
  - `LocalAPIClient`: Client for local models with OpenAI-compatible API
- **APIClientFactory**: Factory for creating the appropriate client type

#### Features:

- **Conversation History Management**: Storing and managing conversation context
- **Rate Limiting**: Basic rate limit handling with provider-specific enhancements
- **Error Handling**: Robust error handling for API requests
- **Provider-Specific Formatting**: Adapting requests and responses to each provider's API

#### Usage Examples:

```python
# Create a client through the factory
provider_config = config_manager.get_provider_config("claude")
client = APIClientFactory.create_client("claude", provider_config)

# Send a message
response = client.send_message("Hello, how can you help me with code analysis?")

# Add a system message
client.add_message("system", "You are a helpful assistant focused on Python development.")

# Clear conversation
client.clear_conversation()
```

#### Provider-Specific Implementations:

Each provider client handles:
- Formatting messages according to the provider's API specifications
- Parsing provider-specific response formats
- Managing provider-specific rate limiting based on response headers

### 3. API Interface (`api_interface.py`)

The `APIInterface` class serves as the main interaction point for the application, providing a unified interface to the various AI providers.

#### Key Functions:

- **Provider Management**: Creating and switching between AI providers
- **Message Handling**: Sending messages and retrieving responses
- **Conversation Management**: Clearing history, adding system messages
- **Audit Logging**: Comprehensive logging of all API interactions
- **Conversation History**: Tracking and retrieving conversation history

#### Features:

- **Automatic Audit Logging**: All API requests and responses are logged
- **Conversation History Tracking**: All messages are stored for future reference
- **Provider Switching**: Dynamic switching between different AI providers
- **Error Handling**: Robust error handling and reporting

#### Usage Examples:

```python
# Create an API interface with default configuration
api = APIInterface()

# Or with custom configuration and provider
api = APIInterface(config_path="~/custom/config.json", provider="openai")

# Send a message
response = api.send_message("Generate a Python function to parse CSV files.")

# Switch provider
api.switch_provider("claude")

# Add a system message
api.add_system_message("Focus on secure coding practices.")

# Get conversation history
history = api.get_conversation_history()

# Clear conversation
api.clear_conversation()
```

#### Audit Logging:

The API Interface creates two types of log files:
- `audit.jsonl`: Logs all API requests, responses, and system events with timestamps
- `history.jsonl`: Records the complete conversation history

### 4. Application Entry Point (`app.py`)

This module serves as the main entry point for the application, providing a command-line interface and application setup.

#### Key Functions:

- **Configuration Setup**: Creates default configuration if needed
- **Logging Setup**: Configures logging based on settings
- **Command-Line Interface**: Processes command-line arguments
- **Interactive Mode**: Provides a simple interactive CLI for testing

#### Command-Line Arguments:

- `--config`, `-c`: Specify a custom configuration file path
- `--provider`, `-p`: Override the default AI provider
- `--debug`: Enable debug-level logging
- `--init`: Initialize the default configuration file

#### Usage Examples:

```bash
# Create default configuration
python app.py --init

# Start with default settings
python app.py

# Use custom configuration and provider
python app.py --config ~/custom/config.json --provider openai

# Enable debug logging
python app.py --debug
```

#### Initialization Process:

1. Parse command-line arguments
2. Load configuration
3. Set up logging
4. Create API interface
5. Enter interactive mode (if applicable)

## Security Considerations

The application has implemented several security features:

1. **Audit Logging**: All API interactions are logged for review
2. **Configuration Validation**: Validation prevents misconfiguration
3. **Error Handling**: Robust error handling for API communication
4. **Path Expansion**: User paths are properly expanded to prevent issues

Additional security features planned but not yet implemented:
- Secure workspace with strict boundaries
- Sandbox isolation for code execution
- Transaction-based file operations with rollback capability

## Next Steps for Development

Based on the current implementation, here are the suggested next steps:

1. **Implement Secure Workspace Manager**: Currently marked as PLANNED in the project overview
2. **Complete Code Execution Environment**: For safely testing generated code
3. **Enhance CLI Interface**: More sophisticated commands and workflows
4. **Implement Unit Tests**: For all implemented components
5. **Add Voice Processing**: As an optional interaction method

## File Structure

```
ai-agent/
├── app.py              # Application entry point (IMPLEMENTED)
├── api_client.py       # API client implementation (IMPLEMENTED)
├── api_interface.py    # API Interface (IMPLEMENTED)
├── config_manager.py   # Configuration manager (IMPLEMENTED)
├── workspace.py        # Secure workspace handling (PLANNED)
├── voice_handler.py    # Voice processing (PLANNED - optional)
├── code_executor.py    # Code generation & testing (PLANNED)
├── security.py         # Security utilities (PLANNED)
└── config/
    └── config.json     # Configuration settings (IMPLEMENTED)
```
