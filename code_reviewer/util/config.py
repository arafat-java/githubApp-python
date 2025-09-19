#!/usr/bin/env python3
"""
Configuration utilities for Azure credentials and settings
"""

import os
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def load_env_file(env_file_path: str = ".env") -> None:
    """
    Load environment variables from a .env file.
    
    Args:
        env_file_path: Path to the .env file
    """
    env_path = Path(env_file_path)
    
    # Try different locations for .env file
    possible_paths = [
        env_path,  # Current directory
        Path(__file__).parent.parent / env_file_path,  # code_reviewer directory
        Path(__file__).parent.parent.parent / env_file_path,  # Project root
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Loading environment variables from {path}")
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value and not os.getenv(key):
                            os.environ[key] = value
            return
    
    logger.debug(f"No .env file found in any of the expected locations")


def get_secrets() -> Dict[str, str]:
    """
    Get Azure secrets from environment variables or configuration.
    
    The client secret is a secret string that the application uses to prove 
    its identity when requesting a token (also known as application password).
    
    Returns:
        Dictionary containing Azure credentials
    """
    # Try to load from .env file first
    load_env_file()
    
    secrets = {
        'azure_tenant_id': os.getenv('AZURE_TENANT_ID'),
        'azure_client_id': os.getenv('AZURE_CLIENT_ID'),
        'azure_client_secret': os.getenv('AZURE_CLIENT_SECRET'),  # Application password for token authentication
        'azure_endpoint': os.getenv('AZURE_ENDPOINT'),
        'azure_token_url': os.getenv('AZURE_TOKEN_URL'),
        'azure_scope': os.getenv('AZURE_SCOPE'),
        'azure_openai_url': os.getenv('AZURE_OPENAI_URL')
    }
    
    # Validate that all required secrets are present
    missing_secrets = [key for key, value in secrets.items() if not value]
    if missing_secrets:
        logger.warning(f"Missing environment variables: {missing_secrets}")
    
    return secrets


def validate_azure_config() -> bool:
    """
    Validate that all required Azure configuration is present.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    secrets = get_secrets()
    required_keys = ['azure_tenant_id', 'azure_client_id', 'azure_client_secret', 'azure_endpoint']
    
    for key in required_keys:
        if not secrets.get(key):
            logger.error(f"Missing required configuration: {key}")
            return False
    
    return True


def get_default_deployment_config() -> Dict[str, Any]:
    """
    Get default deployment configuration for Azure OpenAI.
    
    Returns:
        Dictionary with default deployment settings
    """
    return {
        'deployment_name': os.getenv('AZURE_DEPLOYMENT_NAME', 'gpt-4'),
        'api_version': os.getenv('AZURE_API_VERSION', '2024-02-15-preview'),
        'max_tokens': int(os.getenv('AZURE_MAX_TOKENS', '2000')),
        'temperature': float(os.getenv('AZURE_TEMPERATURE', '0.1'))
    }
