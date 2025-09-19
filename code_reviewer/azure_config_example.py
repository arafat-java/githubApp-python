#!/usr/bin/env python3
"""
Azure OpenAI Configuration Example for Multi-Agent Code Review System
"""

import os
from multi_agent_reviewer import MultiAgentCodeReviewer


def setup_azure_credentials():
    """Example of how to set up Azure OpenAI credentials."""
    
    print("🔧 Azure OpenAI Configuration Setup")
    print("=" * 50)
    
    # Method 1: Environment Variables (Recommended)
    print("\n📋 Method 1: Set Environment Variables")
    print("Add these to your shell profile (.bashrc, .zshrc, etc.):")
    print()
    print("export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'")
    print("export AZURE_OPENAI_API_KEY='your-api-key-here'")
    print()
    
    # Method 2: Direct Parameters
    print("📋 Method 2: Direct Parameters")
    print("Pass credentials directly to the reviewer:")
    print()
    print("reviewer = MultiAgentCodeReviewer(")
    print("    azure_endpoint='https://your-resource.openai.azure.com',")
    print("    api_key='your-api-key-here',")
    print("    deployment_name='gpt-4'  # Your deployment name")
    print(")")
    print()
    
    # Method 3: CLI Arguments
    print("📋 Method 3: CLI Arguments")
    print("Use command line arguments:")
    print()
    print("python3 multi_agent_reviewer.py \\")
    print("  --azure-endpoint 'https://your-resource.openai.azure.com' \\")
    print("  --api-key 'your-api-key' \\")
    print("  --deployment-name 'gpt-4' \\")
    print("  --code 'your code here'")
    print()


def test_azure_connection():
    """Test Azure OpenAI connection with environment variables."""
    
    print("🧪 Testing Azure OpenAI Connection")
    print("=" * 50)
    
    # Check if environment variables are set
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not endpoint or not api_key:
        print("❌ Missing environment variables!")
        print("Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
        return False
    
    try:
        # Initialize reviewer with Azure OpenAI
        reviewer = MultiAgentCodeReviewer(
            azure_endpoint=endpoint,
            api_key=api_key,
            deployment_name="gpt-4",  # Update with your deployment name
            use_azure=True,
            enabled_agents=['security']  # Test with just one agent
        )
        
        print("✅ Multi-agent reviewer initialized successfully!")
        
        # Test with simple code
        test_code = """
def test_function():
    return "Hello, World!"
        """
        
        print("🔄 Testing security agent with simple code...")
        result = reviewer.review_code(test_code)
        
        if result:
            print("✅ Azure OpenAI connection successful!")
            print(f"Overall score: {result.overall_score}/10")
            return True
        else:
            print("❌ Review failed - check your configuration")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def example_usage():
    """Show example usage with Azure OpenAI."""
    
    print("\n🚀 Example Usage with Azure OpenAI")
    print("=" * 50)
    
    example_code = """
# Example: Code with security issues for demonstration
def login(username, password):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return execute_query(query)
    """
    
    print("Example code with security vulnerabilities:")
    print(example_code)
    
    print("\nTo review this code with Azure OpenAI:")
    print()
    print("1. Set environment variables:")
    print("   export AZURE_OPENAI_ENDPOINT='your-endpoint'")
    print("   export AZURE_OPENAI_API_KEY='your-key'")
    print()
    print("2. Run the review:")
    print("   python3 multi_agent_reviewer.py --code \"$(cat example_code.py)\" --agents security performance")
    print()
    print("3. Or use Python API:")
    print("""
reviewer = MultiAgentCodeReviewer(use_azure=True)
result = reviewer.review_code(code)
reviewer.print_report(result, "detailed")
    """)


def main():
    """Main function to demonstrate Azure OpenAI setup."""
    
    setup_azure_credentials()
    
    # Test connection if environment variables are available
    if os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"):
        print("\n" + "=" * 50)
        if test_azure_connection():
            example_usage()
    else:
        print("\n💡 Set up your environment variables and run this script again to test the connection!")
        example_usage()


if __name__ == "__main__":
    main()
