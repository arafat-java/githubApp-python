# Code Review Bot

A Python application that provides comprehensive code reviews using your local AI model (Ollama/Llama). Now featuring a **Multi-Agent Review System** for in-depth, specialized code analysis.

## Features

### 🤖 Multi-Agent Review System (NEW!)
- **6 Specialized Agents**: Security, Performance, Coding Practices, Architecture, Readability, and Testability
- **Parallel Processing**: All agents run simultaneously for faster reviews
- **Consolidated Reports**: AI-powered synthesis of all agent findings
- **Flexible Agent Selection**: Choose specific agents or run all

### 📋 Traditional Single-Agent Reviews
- **Multiple Review Types**: General, Security, Performance, and Modern code reviews
- **Streaming Output**: Real-time response streaming
- **Minimal Mode**: Concise, actionable feedback

### 🔧 General Features
- **Flexible Input**: Review code from files, direct code strings, or git diffs
- **CLI Interface**: Easy-to-use command-line interface with both modes
- **AI Integration**: Works with Azure OpenAI (recommended) or local Ollama/Llama models
- **PR Review Format**: GitHub/GitLab style review comments with line-specific feedback

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
python3 -m pip install -r requirements.txt
```

3. **Choose your AI provider:**

### Option A: Azure OpenAI (Recommended)
Set up your Azure OpenAI credentials:
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key-here"
```

### Option B: Local Ollama
Make sure your local AI model is running:
```bash
ollama serve
ollama pull llama3.2
```

## Quick Start

### 🚀 Most Common Commands

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Review a file with all agents (recommended)
python3 multi_agent_reviewer.py --file your_code.py

# Review with specific agents for faster analysis
python3 multi_agent_reviewer.py --file your_code.js --agents security performance

# Review code directly from command line
python3 multi_agent_reviewer.py --code "your code here"

# List all available agents
python3 multi_agent_reviewer.py --list-agents

# Use local Ollama instead of Azure OpenAI
python3 multi_agent_reviewer.py --file your_code.py --use-ollama
```

## Usage

### 🤖 Multi-Agent Review System

#### Comprehensive multi-agent review with Azure OpenAI (all 6 agents):
```bash
python3 multi_agent_reviewer.py --file path/to/your/code.js
```

#### Review with specific agents:
```bash
python3 multi_agent_reviewer.py --file mycode.py --agents security performance
```

#### Multi-agent review with PR-style output:
```bash
# Full review with all 6 agents (default)
python3 multi_agent_reviewer.py --file your_file.js

# Specific agents for focused review
python3 multi_agent_reviewer.py --code "your_code_here" --agents security performance

# Review git diff for PR comments
python3 multi_agent_reviewer.py --diff "$(git diff)" --agents security coding_practices
```

#### Using local Ollama instead of Azure OpenAI:
```bash
python3 multi_agent_reviewer.py --file mycode.py --use-ollama --agents security performance
```

#### List available agents:
```bash
python3 multi_agent_reviewer.py --list-agents
```

#### Run agents sequentially (slower but uses less memory):
```bash
python3 multi_agent_reviewer.py --file mycode.py --sequential
```

#### Adjust creativity level (0.0-1.0):
```bash
python3 multi_agent_reviewer.py --file mycode.py --creativity 0.3
```

#### Available agents:
- `security`: Security vulnerabilities and best practices
- `performance`: Performance bottlenecks and optimizations
- `coding_practices`: Code quality, SOLID principles, design patterns
- `architecture`: Software design and architectural concerns
- `readability`: Code clarity, documentation, naming conventions
- `testability`: Test coverage, mocking, testable design

### 📋 Traditional Single-Agent Reviews

#### Review a file:
```bash
python3 code_reviewer.py --file path/to/your/code.js --type modern
```

#### Review code directly:
```bash
python3 code_reviewer.py --code "var data = []; for(var i=0; i<items.length; i++) { if(items[i].active == true) data.push(items[i]); }" --type modern
```

#### Review a git diff:
```bash
git diff | python3 code_reviewer.py --diff -
```

#### Review types:
- `general` (default): Comprehensive code review
- `security`: Security-focused review
- `performance`: Performance optimization review  
- `modern`: Modern language features and best practices

### Python API

#### Multi-Agent API:
```python
from multi_agent_reviewer import MultiAgentCodeReviewer

# Initialize multi-agent reviewer
reviewer = MultiAgentCodeReviewer()

# Review code with all agents
code = """
def process_user_input(user_input):
    import os
    command = "ls " + user_input  # Security issue: command injection
    os.system(command)
    return "Command executed"
"""

consolidated_review = reviewer.review_code(code)
reviewer.print_report(consolidated_review, "detailed")

# Review with specific agents
reviewer.set_enabled_agents(['security', 'coding_practices'])
review = reviewer.review_file("script.py")

# Get JSON output for integration
json_report = reviewer.generate_report(review, "json")
```

#### Traditional Single-Agent API:
```python
from code_reviewer import CodeReviewer

# Initialize reviewer
reviewer = CodeReviewer()

# Review code string
code = """
var data = [];
for(var i=0; i<items.length; i++) {
    if(items[i].active == true) {
        data.push(items[i]);
    }
}
"""

review = reviewer.review_code(code, review_type="modern")
print(review)

# Review a file
review = reviewer.review_file("script.js", review_type="security")
print(review)
```

## Configuration

You can customize the AI model settings:

```bash
python3 code_reviewer.py --file script.js --model-url http://localhost:11434/api/generate --model-name llama3.2
```

## Examples

### 🤖 Multi-Agent Examples

#### Example 1: Comprehensive Multi-Agent Review
```bash
python3 multi_agent_reviewer.py --code "
def login(username, password):
    query = 'SELECT * FROM users WHERE username = \'' + username + '\' AND password = \'' + password + '\''
    return execute_query(query)
"
```

This will run all 6 agents and provide:
- **Security Agent**: Identifies SQL injection vulnerability
- **Performance Agent**: Suggests query optimization
- **Coding Practices Agent**: Recommends parameterized queries
- **Architecture Agent**: Suggests separation of concerns
- **Readability Agent**: Improves function documentation
- **Testability Agent**: Recommends dependency injection
- **Consolidation Agent**: Synthesizes all findings with prioritized recommendations

#### Example 2: Security-Focused Review
```bash
python3 multi_agent_reviewer.py --file auth_handler.py --agents security coding_practices
```

#### Example 3: Performance Analysis
```bash
python3 multi_agent_reviewer.py --file data_processor.py --agents performance architecture
```

### 📋 Traditional Single-Agent Examples

#### Example 1: Modern JavaScript Review
```bash
python3 code_reviewer.py --code "var data = []; for(var i=0; i<items.length; i++) { if(items[i].active == true) data.push(items[i]); }" --type modern
```

Expected output includes suggestions like:
- Use `const`/`let` instead of `var`
- Use array methods like `filter()`
- Use strict equality (`===`)
- Modern ES6+ syntax

#### Example 2: Security Review
```bash
python3 code_reviewer.py --file user_input_handler.js --type security
```

#### Example 3: Performance Review
```bash
python3 code_reviewer.py --file data_processing.py --type performance
```

### 🧪 Running Examples
Try the comprehensive example script:
```bash
python3 example_multi_agent.py
```

This script demonstrates various use cases and agent combinations.

## Requirements

- Python 3.7+
- Local AI model running (e.g., Ollama with Llama 3.2)
- Internet connection for initial setup

## Troubleshooting

1. **Connection Error**: Make sure your local AI model is running on the correct port
2. **Model Not Found**: Ensure the model name matches your local setup
3. **Timeout**: Large code files may take longer to process

## License

MIT License - feel free to use and modify as needed!
