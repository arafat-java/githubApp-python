import os
from dotenv import load_dotenv

# This reads your `.env` file and adds the variables from that file to the `os.environ` object in Python.
load_dotenv()

# This assigns the values of your environment variables to local variables.
APP_ID = os.getenv('APP_ID')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
PRIVATE_KEY_PATH = os.getenv('PRIVATE_KEY_PATH')

# Server configuration
PORT = 3000
HOST = 'localhost'
PATH = "/api/webhook"
LOCAL_WEBHOOK_URL = f"http://{HOST}:{PORT}{PATH}"

# Log configuration for debugging
print("Configuration loaded:")
print(f"APP_ID: {APP_ID}")
print(f"WEBHOOK_SECRET: {WEBHOOK_SECRET}")
print(f"PRIVATE_KEY_PATH: {PRIVATE_KEY_PATH}")
