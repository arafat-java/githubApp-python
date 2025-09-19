# PR Summarizer

A powerful AI-driven CLI tool that analyzes JSON file changes and generates comprehensive Pull Request summaries in markdown format. Built with Azure OpenAI for intelligent code change analysis.

## 🚀 Features

### 🤖 AI-Powered Analysis
- **JSON Input Processing**: Takes a JSON list of file changes as input
- **Multi-Language Support**: Detects programming languages and provides context-aware analysis
- **Comprehensive Summaries**: Generates titles, descriptions, and detailed change overviews
- **Markdown Output**: Returns a JSON object with markdown-formatted summary

### 📊 Detailed Insights
- **Key Changes Extraction**: Identifies the most important modifications
- **Impact Analysis**: Analyzes potential impacts on the system and users
- **Security Assessment**: Identifies potential security implications
- **Testing Recommendations**: Suggests specific testing strategies
- **Breaking Changes Detection**: Flags potential breaking changes

### 🛠️ CLI Interface
- **JSON File Input**: Read file changes from JSON file
- **JSON String Input**: Accept JSON string directly or from stdin
- **Structured Output**: Returns JSON with markdown summary field
- **Context Support**: Add additional context about the PR

### 🔧 Configuration
- **Azure OpenAI Integration**: Enterprise-grade AI with Azure OpenAI
- **Customizable Creativity**: Adjustable AI creativity levels

## 📦 Installation

1. **Navigate to the PR summarizer directory**:
```bash
cd pr_summarizer
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up Azure OpenAI credentials**:
```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"  
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_ENDPOINT="https://your-resource.openai.azure.com"
```

## 🚀 Quick Start

### Basic Usage

```bash
# From JSON file
python3 pr_summarizer.py --json-file changes.json

# From JSON string
python3 pr_summarizer.py --json-input '[{"filename":"app.py","status":"modified","additions":5,"deletions":2}]'

# From stdin
echo '[{"filename":"app.py","status":"modified","additions":5,"deletions":2}]' | python3 pr_summarizer.py --json-input -

# With context
python3 pr_summarizer.py --json-file changes.json --context "Bug fix for authentication"

# Save to file
python3 pr_summarizer.py --json-file changes.json --output summary.json
```

## 📖 Input Format

The tool expects a JSON array of file change objects. Each object should contain:

```json
[
  {
    "filename": "src/auth.py",           // Required: file path
    "status": "modified",                // Required: added, modified, deleted, renamed
    "additions": 25,                     // Required: number of lines added
    "deletions": 5,                      // Required: number of lines deleted
    "diff": "diff content here...",      // Optional: actual diff content
    "old_filename": "old_auth.py"        // Optional: for renamed files
  }
]
```

### Flexible Field Names
The tool supports alternative field names for compatibility:
- `filename` or `file`
- `additions` or `added`
- `deletions` or `deleted`
- `diff` or `patch`
- `old_filename` or `previous_filename`

## 📊 Output Format

The tool returns a JSON object with a single field:

```json
{
  "summary": "# Implement user authentication with bcrypt\n\n## Description\nThis PR improves the authentication system...\n\n## Key Changes\n- Replace SHA256 password hashing with bcrypt\n- Add password verification functionality\n..."
}
```

The `summary` field contains a complete markdown-formatted PR summary including:
- **Title**: Concise PR title
- **Description**: Detailed explanation of changes
- **Statistics**: Files changed, lines added/deleted
- **Key Changes**: Most important modifications
- **Impact Analysis**: Potential system impacts
- **Security Considerations**: Security implications
- **Testing Recommendations**: Suggested testing approaches
- **Breaking Changes**: Potential compatibility issues

## 🎯 Usage Examples

### Example 1: Basic File Analysis
```bash
# Create a JSON file with your changes
cat > changes.json << 'EOF'
[
  {
    "filename": "src/app.py",
    "status": "modified", 
    "additions": 5,
    "deletions": 2,
    "diff": "@@ -1,3 +1,6 @@\n from flask import Flask\n+import os\n+import logging\n \n def create_app():\n     app = Flask(__name__)\n+    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')\n     return app"
  }
]
EOF

# Generate summary
python3 pr_summarizer.py --json-file changes.json
```

### Example 2: Multiple Files with Context
```bash
python3 pr_summarizer.py --json-file changes.json --context "Security improvements for user authentication system"
```

### Example 3: Pipeline Usage
```bash
# From a script or CI/CD pipeline
echo '[{"filename":"config.py","status":"modified","additions":10,"deletions":3}]' | \
  python3 pr_summarizer.py --json-input - --output pr_summary.json
```

### Example 4: Using the Python API
```python
import json
from pr_summarizer import PRSummarizerApp

# Initialize the summarizer
summarizer = PRSummarizerApp()

# JSON data
changes = [
    {
        "filename": "src/auth.py",
        "status": "modified",
        "additions": 15,
        "deletions": 3,
        "diff": "actual diff content here..."
    }
]

# Generate summary
summary = summarizer.summarize_from_json(changes, "Security improvements")

# Get markdown output
markdown_summary = summarizer.format_summary(summary, "markdown")

# Create final JSON output
output = {"summary": markdown_summary}
print(json.dumps(output, indent=2))
```

## 🧪 Testing and Examples

### Run Demo
```bash
python3 demo.py
```

### Interactive Example
```bash
python3 example.py --interactive
```

### Run with Sample Data
```bash
python3 example.py --example
```

### Test with Example File
```bash
python3 pr_summarizer.py --json-file example_changes.json
```

## 🔧 Command Line Options

```
usage: pr_summarizer.py [-h] [--json-file JSON_FILE] [--json-input JSON_INPUT]
                        [--context CONTEXT] [--output OUTPUT] [--creativity CREATIVITY]

PR Summarizer - Analyze JSON file changes and generate PR summaries using Azure OpenAI

options:
  -h, --help            show this help message and exit
  --json-file JSON_FILE, -f JSON_FILE
                        Path to JSON file containing file changes
  --json-input JSON_INPUT, -j JSON_INPUT
                        JSON string of file changes (use '-' for stdin)
  --context CONTEXT, -c CONTEXT
                        Additional context about the PR
  --output OUTPUT, -o OUTPUT
                        Output file path (default: stdout)
  --creativity CREATIVITY
                        Creativity level for AI responses (0.0-1.0)
```

## 🔍 Advanced Features

### Language Detection
The tool automatically detects programming languages from file extensions and provides language-specific insights.

### Security Analysis
- **Vulnerability Detection**: Identifies potential security issues
- **Best Practices**: Suggests security improvements
- **Risk Assessment**: Evaluates security impact of changes

### Performance Insights
- **Performance Impact**: Analyzes potential performance implications
- **Optimization Suggestions**: Recommends performance improvements
- **Resource Usage**: Estimates resource impact of changes

## 🚨 Troubleshooting

### Common Issues

#### "Azure credentials not found"
```bash
# Make sure all required environment variables are set
echo $AZURE_TENANT_ID
echo $AZURE_CLIENT_ID
echo $AZURE_CLIENT_SECRET
echo $AZURE_ENDPOINT
```

#### "Invalid JSON format"
- Ensure your JSON is valid (use a JSON validator)
- Check that the input is a JSON array, not an object
- Verify all required fields are present

#### "No valid file changes found"
- Ensure each object has at least `filename`, `status`, `additions`, and `deletions`
- Check that filenames are not empty
- Verify status values are valid (added, modified, deleted, renamed)

### Performance Tips

1. **Use appropriate creativity levels**: Lower values (0.1-0.3) for production use
2. **Include diff content**: Provides more context for better summaries
3. **Add meaningful context**: Helps the AI understand the purpose of changes

## 🤝 Integration Examples

### GitHub Actions
```yaml
name: Auto PR Summary
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  summarize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Generate file changes JSON
        run: |
          # Convert git diff to JSON format (custom script needed)
          ./generate_changes_json.sh > changes.json
      - name: Generate PR Summary
        run: |
          python3 pr_summarizer/pr_summarizer.py --json-file changes.json > summary.json
```

### CI/CD Pipeline
```bash
#!/bin/bash
# generate_pr_summary.sh

# Create JSON from git changes (example)
echo '[{"filename":"'$1'","status":"modified","additions":'$2',"deletions":'$3'}]' | \
  python3 pr_summarizer.py --json-input - --context "$4" --output pr_summary.json

# Use the summary
cat pr_summary.json
```

### Custom Integration
```python
import subprocess
import json
from pr_summarizer import PRSummarizerApp

def analyze_pr_changes(changes_json, context=""):
    """Analyze PR changes from JSON data."""
    summarizer = PRSummarizerApp()
    summary = summarizer.summarize_from_json(changes_json, context)
    markdown_summary = summarizer.format_summary(summary, "markdown")
    return {"summary": markdown_summary}

# Usage
changes = [{"filename": "app.py", "status": "modified", "additions": 5, "deletions": 2}]
result = analyze_pr_changes(changes, "Bug fix")
print(result["summary"])
```

## 📈 Roadmap

### Planned Features
- [ ] **GitHub API Integration**: Direct GitHub PR analysis
- [ ] **GitLab Support**: Native GitLab merge request analysis  
- [ ] **Batch Processing**: Analyze multiple PR sets at once
- [ ] **Custom Templates**: User-defined summary templates
- [ ] **Enhanced Diff Parsing**: Better diff content analysis

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Issues**: Found a bug? Report it in the issues section
2. **Feature Requests**: Suggest new features or improvements  
3. **Code Contributions**: Submit pull requests with improvements
4. **Documentation**: Help improve documentation and examples
5. **Testing**: Test with different JSON formats and provide feedback

## 📄 License

MIT License - feel free to use and modify as needed!

## 🙏 Acknowledgments

- **Azure OpenAI**: For providing powerful AI capabilities
- **Git**: For the diff format and version control integration

---

**Happy Summarizing! 🚀**

For more examples and advanced usage, check out the `example.py` file and test with the provided `example_changes.json`.