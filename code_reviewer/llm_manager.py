#!/usr/bin/env python3
"""
LLM Instance Manager for Multi-Agent Code Review System
"""

import logging
import os
from typing import Optional, Union
from .util.llm import AzureClient, OllamaClient
from .util import config

logger = logging.getLogger(__name__)


def get_llm_instance(is_local: bool = False, creativity_level: float = 0.5) -> Union[AzureClient, OllamaClient]:
    """
    Get an LLM instance (Azure or local Ollama).
    
    Args:
        is_local: If True, use local Ollama; if False, use Azure OpenAI
        creativity_level: Temperature/creativity level (0.0-1.0)
        
    Returns:
        LLM client instance
    """
    if is_local:
        logger.info("Creating local Ollama client")
        return OllamaClient()
    else:
        logger.info("Creating Azure OpenAI client")
        
        # Get secrets from environment or config
        secrets = {
            'azure_tenant_id': os.getenv('AZURE_TENANT_ID'),
            'azure_client_id': os.getenv('AZURE_CLIENT_ID'),
            'azure_client_secret': os.getenv('AZURE_CLIENT_SECRET'),
            'azure_endpoint': os.getenv('AZURE_ENDPOINT')
        }
        
        # Fallback to config if environment variables not found
        if not all(secrets.values()):
            logger.info("Environment variables not found, trying config...")
            secrets = config.get_secrets()
        
        if not all(secrets.values()):
            raise ValueError("Missing Azure credentials. Please set environment variables or configure secrets.")
        
        return AzureClient(secrets)


class SandboxInstances:
    """Singleton manager for LLM instances to avoid recreating clients."""
    
    llm_map = {}
    
    @staticmethod
    def get_instance(name: str, is_local: bool = False, creativity_level: float = 0.5) -> Union[AzureClient, OllamaClient]:
        """
        Get a cached LLM instance by name.
        
        Args:
            name: Instance name/identifier
            is_local: Whether to use local Ollama
            creativity_level: Temperature for responses
            
        Returns:
            Cached or new LLM instance
        """
        cache_key = f"{name}_{is_local}_{creativity_level}"
        
        if SandboxInstances.llm_map.get(cache_key) is None:
            logger.info(f"Creating new LLM instance: {cache_key}")
            SandboxInstances.llm_map[cache_key] = get_llm_instance(is_local, creativity_level)
        else:
            logger.debug(f"Using cached LLM instance: {cache_key}")
            
        return SandboxInstances.llm_map[cache_key]
    
    @staticmethod
    def clear_cache():
        """Clear all cached instances."""
        SandboxInstances.llm_map.clear()
        logger.info("LLM instance cache cleared")
    
    @staticmethod
    def get_cache_info():
        """Get information about cached instances."""
        return {
            'cached_instances': list(SandboxInstances.llm_map.keys()),
            'count': len(SandboxInstances.llm_map)
        }
