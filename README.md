# GitHub App - Python Version

This is a Python version of the GitHub App that automatically comments on pull requests and displays the diff.

## Features

- Automatically comments on new pull requests
- Displays complete PR diff when PR is opened or synchronized
- Shows file change statistics
- Handles both `pull_request.opened` and `pull_request.synchronize` events
- Webhook signature verification for security

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` with your GitHub App credentials:
   ```
   APP_ID=your_app_id_here
   WEBHOOK_SECRET=your_webhook_secret_here
   PRIVATE_KEY_PATH=path/to/your/private-key.pem
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

## File Structure

- `app.py` - Main application entry point
- `config.py` - Configuration management
- `handlers.py` - Webhook event handlers
- `server.py` - Flask server setup
- `requirements.txt` - Python dependencies
- `env.example` - Environment variables template

## How it works

1. The Flask server listens for webhook events from GitHub
2. When a PR is opened or synchronized, it fetches the complete diff
3. Displays the diff and file change statistics in the console
4. Adds a comment to the PR

## Dependencies

- `python-dotenv` - Environment variable management
- `PyGithub` - GitHub API client
- `flask` - Web framework for handling webhooks
- `requests` - HTTP library for API calls

## Security

- Webhook signature verification using HMAC-SHA256
- Environment variable configuration for sensitive data
