# Getting Started with PR Summarizer

Welcome to PR Summarizer! This guide will help you get up and running quickly with the Azure OpenAI-powered CLI tool.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
cd pr_summarizer
pip install -r requirements.txt
```

### 2. Set Up Azure OpenAI Credentials
```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_ENDPOINT="https://your-resource.openai.azure.com"
```

### 3. Test the Installation
```bash
python3 demo.py
```

## 🎯 Quick Start Examples

### Basic Usage with JSON File
```bash
# Use the example file
python3 pr_summarizer.py --json-file example_changes.json
```

### JSON String Input
```bash
# Direct JSON input
python3 pr_summarizer.py --json-input '[{"filename":"src/app.py","status":"modified","additions":5,"deletions":2}]'
```

### From Stdin
```bash
# Pipe JSON data
cat example_changes.json | python3 pr_summarizer.py --json-input -
```

### With Context and Output File
```bash
# Add context and save to file
python3 pr_summarizer.py --json-file example_changes.json --context "Bug fix for authentication" --output summary.json
```

## 📝 Input Format

Your JSON input should be an array of file change objects:

```json
[
  {
    "filename": "src/auth.py",
    "status": "modified",
    "additions": 25,
    "deletions": 5,
    "diff": "@@ -1,5 +1,6 @@\n import hashlib\n import jwt\n+import bcrypt"
  },
  {
    "filename": "src/database.py", 
    "status": "added",
    "additions": 45,
    "deletions": 0,
    "diff": "@@ -0,0 +1,45 @@\n+import sqlite3"
  }
]
```

### Required Fields
- `filename`: File path
- `status`: `added`, `modified`, `deleted`, or `renamed`
- `additions`: Number of lines added
- `deletions`: Number of lines deleted

### Optional Fields
- `diff`: Actual diff content for better analysis
- `old_filename`: For renamed files

## 📊 Output Format

The tool returns a JSON object with a markdown summary:

```json
{
  "summary": "# Implement user authentication with bcrypt\n\n## Description\nThis PR improves the authentication system...\n\n## Key Changes\n- Replace SHA256 password hashing with bcrypt\n- Add password verification functionality\n..."
}
```

## 🛠️ Troubleshooting

### "Azure OpenAI credentials not found"
Make sure all environment variables are set:
```bash
echo $AZURE_TENANT_ID
echo $AZURE_CLIENT_ID
echo $AZURE_CLIENT_SECRET
echo $AZURE_ENDPOINT
```

### "Invalid JSON format"
- Validate your JSON using an online JSON validator
- Ensure it's an array, not an object
- Check that all required fields are present

### "No valid file changes found"
- Verify each object has `filename`, `status`, `additions`, and `deletions`
- Ensure filenames are not empty
- Check that status values are valid

## 🎮 Try the Examples

### Run the Demo
```bash
python3 demo.py
```

### Interactive Example
```bash
python3 example.py --interactive
```

### Sample Data Example  
```bash
python3 example.py --example
```

## 🚀 You're Ready!

Start with the example file:
```bash
python3 pr_summarizer.py --json-file example_changes.json
```

Then try with your own data:
```bash
python3 pr_summarizer.py --json-input '[{"filename":"your-file.py","status":"modified","additions":10,"deletions":3}]'
```

For more advanced usage, check out the full README.md!

Happy summarizing! 🎉