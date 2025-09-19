#!/usr/bin/env python3
"""
LLM Client utilities for Azure OpenAI integration
"""

import logging
import os
import requests
from typing import Optional, Dict, Any, List
from azure.identity import ClientSecretCredential, EnvironmentCredential

logger = logging.getLogger(__name__)


class AzureClient:
    """Azure OpenAI client for code review agents."""
    
    def __init__(self, secrets: Dict[str, str]):
        """
        Initialize Azure client with secrets.
        
        Args:
            secrets: Dictionary containing Azure credentials and endpoint
        """
        self.secrets = secrets
        self.azure_endpoint = secrets.get('azure_endpoint')
        self.azure_tenant_id = secrets.get('azure_tenant_id')
        self.azure_client_id = secrets.get('azure_client_id')
        self.azure_client_secret = secrets.get('azure_client_secret')
        self.azure_token_url = secrets.get('azure_token_url', f'https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/v2.0/token')
        self.azure_scope = secrets.get('azure_scope', 'https://cognitiveservices.azure.com/.default')
        self.azure_openai_url = secrets.get('azure_openai_url')
        
        if not all([self.azure_client_id, self.azure_client_secret]):
            raise ValueError("Missing required Azure credentials: client_id and client_secret")
        
        # Use direct token URL instead of ClientSecretCredential for more control
        self._access_token = None
        self._refresh_token()
    
    def _refresh_token(self):
        """Refresh the access token using client credentials flow."""
        try:
            # Use direct OAuth2 client credentials flow
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': self.azure_client_id,
                'client_secret': self.azure_client_secret,
                'scope': self.azure_scope
            }
            
            response = requests.post(self.azure_token_url, data=token_data, timeout=30)
            response.raise_for_status()
            
            token_response = response.json()
            self._access_token = token_response.get('access_token')
            
            if not self._access_token:
                raise ValueError("No access token received from Azure")
                
            logger.debug("Azure access token refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh Azure token: {e}")
            raise
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       deployment_name: str = "gpt-35-turbo-blue",
                       api_version: str = "2023-05-15",
                       max_tokens: int = 2000,
                       temperature: float = 0.1) -> Optional[str]:
        """
        Make a chat completion request to Azure OpenAI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            deployment_name: Azure OpenAI deployment name
            api_version: API version to use
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
            
        Returns:
            Response content or None if failed
        """
        # Use the specific OpenAI URL if provided, otherwise construct it
        if self.azure_openai_url:
            url = self.azure_openai_url
        else:
            url = f"{self.azure_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}"
        }
        
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=300)
            
            # Handle token expiration
            if response.status_code == 401:
                logger.info("Token expired, refreshing...")
                self._refresh_token()
                headers["Authorization"] = f"Bearer {self._access_token}"
                response = requests.post(url, headers=headers, json=payload, timeout=300)
            
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Azure OpenAI request failed: {e}")
            return None


class OllamaClient:
    """Local Ollama client for fallback."""
    
    def __init__(self, model_url: str = "http://localhost:11434/api/generate", 
                 model_name: str = "llama3.2"):
        self.model_url = model_url
        self.model_name = model_name
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       **kwargs) -> Optional[str]:
        """
        Make a completion request to Ollama.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Response content or None if failed
        """
        # Convert messages to single prompt for Ollama
        prompt = self._messages_to_prompt(messages)
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(self.model_url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return None
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages format to single prompt for Ollama."""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
