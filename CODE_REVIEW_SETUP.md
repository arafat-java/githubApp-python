# Code Review Setup Guide

This guide will help you set up the automated code review functionality for your GitHub App.

## Prerequisites

The code review system requires either:
1. **Azure OpenAI** (cloud-based, requires API credentials)
2. **Local Ollama** (privacy-focused, runs locally)

## Option 1: Local Ollama Setup (Recommended)

### Install Ollama

1. **Download and Install Ollama**:
   - Visit: https://ollama.ai/
   - Download for your operating system
   - Follow the installation instructions

2. **Pull a Model**:
   ```bash
   # Pull the recommended model
   ollama pull llama3.2
   
   # Or try a smaller model if you have limited resources
   ollama pull llama3.2:3b
   ```

3. **Verify Installation**:
   ```bash
   # Check if Ollama is running
   ollama list
   
   # Test the API
   curl http://localhost:11434/api/generate -d '{
     "model": "llama3.2",
     "prompt": "Hello, how are you?",
     "stream": false
   }'
   ```

### Configure Environment

1. **Set up your `.env` file**:
   ```bash
   # Copy the example file
   cp env.example .env
   
   # Edit the file and ensure USE_LOCAL_LLM=true
   USE_LOCAL_LLM=true
   ```

2. **Test the Integration**:
   ```bash
   python3 -c "from code_review_integration import get_code_review_integration; integration = get_code_review_integration(); print(f'Available: {integration.is_available()}')"
   ```

## Option 2: Azure OpenAI Setup

### Get Azure OpenAI Credentials

1. **Create an Azure OpenAI Resource**:
   - Go to Azure Portal
   - Create a new "Azure OpenAI" resource
   - Deploy a model (e.g., GPT-4, GPT-3.5-turbo)

2. **Get Required Information**:
   - Tenant ID
   - Client ID
   - Client Secret
   - Endpoint URL
   - Deployment Name

### Configure Environment

1. **Set up your `.env` file**:
   ```bash
   # Copy the example file
   cp env.example .env
   
   # Edit the file with your Azure credentials
   USE_LOCAL_LLM=false
   AZURE_TENANT_ID=your_tenant_id
   AZURE_CLIENT_ID=your_client_id
   AZURE_CLIENT_SECRET=your_client_secret
   AZURE_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2023-05-15
   ```

## Testing the Setup

### Test Code Review Integration

```bash
# Test if the integration is available
python3 -c "
from code_review_integration import get_code_review_integration
integration = get_code_review_integration()
print(f'Code review available: {integration.is_available()}')
"
```

### Test with Sample Code

```bash
# Test with a simple diff
python3 -c "
from code_review_integration import get_code_review_integration
import json

integration = get_code_review_integration()
if integration.is_available():
    test_diff = '''
diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print('Hello World')
+    print('Hello, World!')
     return True
'''
    pr_info = {'number': 999, 'title': 'Test PR'}
    review = integration.review_pr_diff(test_diff, pr_info)
    if review:
        print('✅ Code review working!')
        print(review[:200] + '...' if len(review) > 200 else review)
    else:
        print('❌ Code review failed')
else:
    print('❌ Code review not available')
"
```

## Troubleshooting

### Ollama Issues

**Error: "404 Client Error: Not Found"**
- Ensure Ollama is running: `ollama serve`
- Check if the model is installed: `ollama list`
- Pull the model: `ollama pull llama3.2`

**Error: "Connection refused"**
- Start Ollama service: `ollama serve`
- Check if port 11434 is available: `lsof -i :11434`

**Error: "Model not found"**
- List available models: `ollama list`
- Pull the required model: `ollama pull llama3.2`

### Azure OpenAI Issues

**Error: "Missing Azure credentials"**
- Check all required environment variables are set
- Verify the credentials are correct
- Ensure the Azure resource is active

**Error: "401 Unauthorized"**
- Verify the client secret is correct
- Check if the client ID has proper permissions
- Ensure the deployment exists and is accessible

### General Issues

**Error: "Multi-agent code reviewer not available"**
- Check if all dependencies are installed: `pip install -r requirements.txt`
- Verify the code_reviewer package is properly set up
- Check the application logs for specific error messages

**Error: "Import errors"**
- Ensure you're in the correct directory
- Check if all Python files are present
- Verify the code_reviewer/__init__.py file exists

## Performance Tips

### For Local Ollama

1. **Use a smaller model** for faster responses:
   ```bash
   ollama pull llama3.2:3b  # 3B parameter model
   ```

2. **Adjust creativity level** in the code:
   ```python
   # Lower creativity = faster, more focused responses
   integration = CodeReviewIntegration(creativity_level=0.1)
   ```

3. **Limit enabled agents** for faster reviews:
   ```python
   # Use fewer agents for quicker reviews
   enabled_agents=['security', 'coding_practices']
   ```

### For Azure OpenAI

1. **Use appropriate model size** based on your needs
2. **Set reasonable token limits** to control costs
3. **Use parallel processing** (enabled by default)

## Next Steps

Once the setup is complete:

1. **Start your GitHub App**: `python app.py`
2. **Create a test PR** in your repository
3. **Verify the automated review** appears in the PR comments
4. **Customize the review settings** as needed

The code review system will now automatically analyze all new and synchronized pull requests, providing comprehensive AI-powered feedback directly in your GitHub PRs!
