# GitHub App - Python Version

This is a Python version of the GitHub App that automatically comments on pull requests, displays the diff, and provides AI-powered code reviews.

## Features

- **Automated PR Comments**: Automatically comments on new pull requests
- **Diff Display**: Shows complete PR diff when PR is opened or synchronized
- **File Change Statistics**: Displays detailed file change information
- **AI Code Review**: Multi-agent AI system for comprehensive code analysis
- **Event Handling**: Handles both `pull_request.opened` and `pull_request.synchronize` events
- **Security**: Webhook signature verification using HMAC-SHA256
- **Flexible LLM Backend**: Supports both Azure OpenAI and local Ollama

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
   
   # Code Review Configuration (optional)
   USE_LOCAL_LLM=true  # Use local Ollama (default)
   # OR configure Azure OpenAI credentials if USE_LOCAL_LLM=false
   ```

3. **Set up Code Review (Optional):**
   
   For AI-powered code reviews, you need either:
   - **Local Ollama** (recommended): See [CODE_REVIEW_SETUP.md](CODE_REVIEW_SETUP.md)
   - **Azure OpenAI**: Configure credentials in `.env`

4. **Run the application:**
   ```bash
   python app.py
   ```

## File Structure

- `app.py` - Main application entry point
- `config.py` - Configuration management
- `handlers.py` - Webhook event handlers
- `server.py` - Flask server setup
- `code_review_integration.py` - AI code review integration
- `code_reviewer/` - Multi-agent code review system
  - `multi_agent_reviewer.py` - Main orchestrator
  - `specialized_agents.py` - Individual review agents
  - `consolidation_agent.py` - Review consolidation
  - `pr_review_formatter.py` - PR comment formatting
- `requirements.txt` - Python dependencies
- `env.example` - Environment variables template
- `CODE_REVIEW_SETUP.md` - Code review setup guide

## How it works

1. The Flask server listens for webhook events from GitHub
2. When a PR is opened or synchronized, it fetches the complete diff
3. Displays the diff and file change statistics in the console
4. Adds a comment to the PR
5. **NEW**: Performs AI-powered code review using multi-agent system
6. **NEW**: Posts structured review comments with specific feedback and recommendations

## Dependencies

- `python-dotenv` - Environment variable management
- `PyGithub` - GitHub API client
- `flask` - Web framework for handling webhooks
- `requests` - HTTP library for API calls
- `openai` - OpenAI API client for code review
- `azure-identity` - Azure authentication
- `azure-core` - Azure core functionality
- `click` - Command line interface
- `colorama` - Colored terminal output

## Security

- Webhook signature verification using HMAC-SHA256
- Environment variable configuration for sensitive data
