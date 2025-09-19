#!/usr/bin/env python3
"""
Azure OpenAI Setup Guide and Test Script
"""

import os
import logging
from llm_manager import get_llm_instance, SandboxInstances
from util.config import validate_azure_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_environment_variables():
    """Guide for setting up Azure OpenAI environment variables."""
    
    print("🔧 Azure OpenAI Setup Guide")
    print("=" * 60)
    
    print("\n📋 Required Environment Variables:")
    print("Set these environment variables with your Azure credentials:")
    print()
    
    required_vars = [
        ("AZURE_TENANT_ID", "Your Azure AD tenant ID"),
        ("AZURE_CLIENT_ID", "Your Azure AD application (client) ID"),
        ("AZURE_CLIENT_SECRET", "Client secret (application password) for token authentication"),
        ("AZURE_ENDPOINT", "Your Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com)")
    ]
    
    for var_name, description in required_vars:
        current_value = os.getenv(var_name)
        status = "✅ SET" if current_value else "❌ NOT SET"
        print(f"  {var_name}: {description}")
        print(f"    Status: {status}")
        if current_value:
            # Show partial value for security
            masked_value = current_value[:8] + "..." if len(current_value) > 8 else "***"
            print(f"    Value: {masked_value}")
        print()
    
    print("📝 How to set environment variables:")
    print()
    print("# For bash/zsh (.bashrc, .zshrc):")
    print("export AZURE_TENANT_ID='your-tenant-id'")
    print("export AZURE_CLIENT_ID='your-client-id'")
    print("export AZURE_CLIENT_SECRET='your-client-secret'")
    print("export AZURE_ENDPOINT='https://your-resource.openai.azure.com'")
    print()
    
    print("# For current session:")
    print("export AZURE_TENANT_ID='your-tenant-id' && \\")
    print("export AZURE_CLIENT_ID='your-client-id' && \\")
    print("export AZURE_CLIENT_SECRET='your-client-secret' && \\")
    print("export AZURE_ENDPOINT='https://your-resource.openai.azure.com'")
    print()
    
    print("💡 Optional deployment configuration:")
    print("export AZURE_DEPLOYMENT_NAME='gpt-4'  # Your deployment name")
    print("export AZURE_API_VERSION='2024-02-15-preview'  # API version")
    print()
    
    print("🔍 Where to find these values in Azure:")
    print("1. AZURE_TENANT_ID: Azure AD > Properties > Tenant ID")
    print("2. AZURE_CLIENT_ID: App registrations > Your app > Application ID")
    print("3. AZURE_CLIENT_SECRET: App registrations > Your app > Certificates & secrets")
    print("   └─ This is the 'Value' of your client secret (application password)")
    print("4. AZURE_ENDPOINT: Azure OpenAI > Keys and Endpoint > Endpoint")
    print()


def test_azure_connection():
    """Test Azure OpenAI connection."""
    
    print("\n🧪 Testing Azure OpenAI Connection")
    print("=" * 60)
    
    # Validate configuration
    if not validate_azure_config():
        print("❌ Configuration validation failed!")
        print("Please set all required environment variables.")
        return False
    
    try:
        # Get Azure LLM instance
        logger.info("Creating Azure OpenAI client...")
        llm_client = get_llm_instance(is_local=False, creativity_level=0.1)
        
        print("✅ Azure OpenAI client created successfully!")
        
        # Test with a simple request
        test_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond briefly."
            },
            {
                "role": "user",
                "content": "Say hello and confirm you're working."
            }
        ]
        
        print("🔄 Testing chat completion...")
        response = llm_client.chat_completion(
            messages=test_messages,
            deployment_name=os.getenv('AZURE_DEPLOYMENT_NAME', 'gpt-4'),
            temperature=0.1,
            max_tokens=100
        )
        
        if response:
            print("✅ Chat completion successful!")
            print(f"Response: {response}")
            return True
        else:
            print("❌ Chat completion failed - no response received")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        logger.error(f"Azure connection test error: {e}", exc_info=True)
        return False


def test_multi_agent_system():
    """Test the multi-agent system with Azure OpenAI."""
    
    print("\n🤖 Testing Multi-Agent System")
    print("=" * 60)
    
    try:
        # Import here to avoid circular imports
        from multi_agent_reviewer import MultiAgentCodeReviewer
        
        # Initialize multi-agent reviewer
        reviewer = MultiAgentCodeReviewer(
            is_local=False,  # Use Azure OpenAI
            enabled_agents=['security']  # Test with one agent first
        )
        
        print("✅ Multi-agent reviewer initialized!")
        
        # Test code with security issue
        test_code = """
def login(username, password):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return execute_query(query)
        """
        
        print("🔄 Running security agent test...")
        result = reviewer.review_code(test_code)
        
        if result:
            print("✅ Multi-agent review completed successfully!")
            print(f"Overall score: {result.overall_score}/10")
            print(f"Findings: {len(result.critical_issues)} critical issues found")
            
            # Show summary
            reviewer.print_report(result, "summary")
            return True
        else:
            print("❌ Multi-agent review failed")
            return False
            
    except Exception as e:
        print(f"❌ Multi-agent test failed: {e}")
        logger.error(f"Multi-agent test error: {e}", exc_info=True)
        return False


def show_usage_examples():
    """Show usage examples for the Azure-enabled system."""
    
    print("\n📚 Usage Examples")
    print("=" * 60)
    
    print("1. Basic multi-agent review:")
    print("   python multi_agent_reviewer.py --file mycode.py")
    print()
    
    print("2. Specific agents:")
    print("   python multi_agent_reviewer.py --code 'your code' --agents security performance")
    print()
    
    print("3. Python API:")
    print("""
from multi_agent_reviewer import MultiAgentCodeReviewer

# Create reviewer (uses Azure OpenAI by default)
reviewer = MultiAgentCodeReviewer()

# Review code
result = reviewer.review_code(code)
reviewer.print_report(result, "detailed")
    """)
    
    print("4. Cache management:")
    print("""
from llm_manager import SandboxInstances

# Check cached instances
print(SandboxInstances.get_cache_info())

# Clear cache if needed
SandboxInstances.clear_cache()
    """)


def main():
    """Main setup and test function."""
    
    print("🚀 Azure OpenAI Multi-Agent Code Review Setup")
    print("=" * 80)
    
    # Show setup guide
    setup_environment_variables()
    
    # Test connection if credentials are available
    config_valid = validate_azure_config()
    
    if config_valid:
        print("\n" + "=" * 80)
        connection_success = test_azure_connection()
        
        if connection_success:
            # Test multi-agent system
            print("\n" + "=" * 80)
            multi_agent_success = test_multi_agent_system()
            
            if multi_agent_success:
                show_usage_examples()
                print("\n🎉 Setup complete! Your Azure OpenAI multi-agent system is ready.")
            else:
                print("\n⚠️ Multi-agent system needs debugging.")
        else:
            print("\n⚠️ Fix Azure connection before testing multi-agent system.")
    else:
        print("\n💡 Set up your environment variables and run this script again!")
        show_usage_examples()


if __name__ == "__main__":
    main()
