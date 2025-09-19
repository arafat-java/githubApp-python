import os
import sys
from dotenv import load_dotenv

def validate_environment():
    """
    Validate that .env file exists and contains all required keys from env.example
    """
    env_file_path = '.env'
    env1_file_path = 'env.example'
    
    # Check if .env file exists
    if not os.path.exists(env_file_path):
        print(f"❌ ERROR: {env_file_path} file is missing!")
        print(f"📋 Please create {env_file_path} with the required environment variables.")
        print(f"💡 You can copy from {env1_file_path} as a template.")
        sys.exit(1)
    
    # Check if .env file is empty
    if os.path.getsize(env_file_path) == 0:
        print(f"❌ ERROR: {env_file_path} file is empty!")
        print(f"📋 Please add the required environment variables to {env_file_path}.")
        print(f"💡 You can copy from {env1_file_path} as a template.")
        sys.exit(1)
    
    # Load env.example to get required keys
    required_keys = []
    if os.path.exists(env1_file_path):
        with open(env1_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key = line.split('=')[0].strip()
                    required_keys.append(key)
    
    # Load .env file
    load_dotenv()
    
    # Check for missing required keys
    missing_keys = []
    empty_keys = []
    
    for key in required_keys:
        value = os.getenv(key)
        if value is None:
            missing_keys.append(key)
        elif value.strip() == '':
            empty_keys.append(key)
    
    # Report errors
    if missing_keys or empty_keys:
        print(f"❌ ERROR: {env_file_path} is missing or has empty values for required keys:")
        
        if missing_keys:
            print(f"   Missing keys: {', '.join(missing_keys)}")
        
        if empty_keys:
            print(f"   Empty keys: {', '.join(empty_keys)}")
        
        print(f"📋 Please ensure all required keys are present and have valid values in {env_file_path}.")
        print(f"💡 You can copy from {env1_file_path} as a template.")
        sys.exit(1)
    
    print(f"✅ Environment validation passed! All required keys are present in {env_file_path}.")

# Validate environment before loading configuration
validate_environment()

# This reads your `.env` file and adds the variables from that file to the `os.environ` object in Python.
load_dotenv()

# This assigns the values of your environment variables to local variables.
APP_ID = os.getenv('APP_ID')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
PRIVATE_KEY_PATH = os.getenv('PRIVATE_KEY_PATH')

# Code Review Configuration
USE_LOCAL_LLM = os.getenv('USE_LOCAL_LLM', 'true').lower() == 'true'

# Azure OpenAI Configuration (for code review)
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AZURE_ENDPOINT = os.getenv('AZURE_ENDPOINT')
AZURE_OPENAI_URL = os.getenv('AZURE_OPENAI_URL')

# Server configuration
PORT = 3000
HOST = 'localhost'
PATH = "/api/webhook"
LOCAL_WEBHOOK_URL = f"http://{HOST}:{PORT}{PATH}"

# Log configuration for debugging
print("Configuration loaded:")
print(f"APP_ID: {APP_ID}")
# print(f"WEBHOOK_SECRET: {WEBHOOK_SECRET}")
print(f"PRIVATE_KEY_PATH: {PRIVATE_KEY_PATH}")
