import requests
from github import Github, Auth, GithubIntegration
import json

# This defines the message that your app will post to pull requests.
MESSAGE_FOR_NEW_PRS = "Thanks for opening a new PR! Please follow our contributing guidelines to make your PR easier to review."

def get_installation_access_token(github_app, repo_owner, repo_name):
    """
    Get an installation access token for the GitHub App to access the repository
    """
    try:
        # Extract app_id and private_key from the github_app object
        app_auth = github_app._Github__requester._Requester__auth
        app_id = app_auth.app_id
        private_key = app_auth.private_key
        
        # Create GithubIntegration instance
        integration = GithubIntegration(app_id, private_key)
        
        # Get the installation for this repository
        installation = integration.get_installation(repo_owner, repo_name)
        
        # Get the access token for this installation
        access_token = integration.get_access_token(installation.id)
        
        return access_token.token
    except Exception as error:
        print(f"Error getting installation access token: {error}")
        return None

def handle_pull_request_opened(payload, github_app):
    """
    This adds an event handler that your code will call later. When this event handler is called, 
    it will log the event to the console. Then, it will use GitHub's REST API to add a comment 
    to the pull request that triggered the event.
    """
    pr_number = payload['pull_request']['number']
    repo_owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    pr_title = payload['pull_request']['title']
    
    print(f"Received a pull request event for #{pr_number}")
    print(f"Repository: {repo_owner}/{repo_name}")
    print(f"PR Title: {pr_title}")

    try:
        # Get installation access token
        access_token = get_installation_access_token(github_app, repo_owner, repo_name)
        if not access_token:
            print(f"Failed to get installation access token for {repo_owner}/{repo_name}")
            return
        
        # Get the repository and pull request
        repo = github_app.get_repo(f"{repo_owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Get the PR diff
        print(f"\n=== Fetching PR Diff ===")
        diff_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "Authorization": f"token {access_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        diff_response = requests.get(diff_url, headers=headers)
        diff_response.raise_for_status()
        
        print(f"\n=== PR DIFF ===")
        print(diff_response.text)
        print(f"=== END PR DIFF ===\n")

        # Also get the files changed for additional context
        files_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
        files_response = requests.get(files_url, headers=headers)
        files_response.raise_for_status()
        files_data = files_response.json()

        print(f"\n=== Files Changed ===")
        for index, file in enumerate(files_data, 1):
            print(f"{index}. {file['filename']}")
            print(f"   Status: {file['status']}")
            print(f"   Additions: +{file['additions']}")
            print(f"   Deletions: -{file['deletions']}")
            print(f"   Changes: {file['changes']}")
            if file.get('patch'):
                patch_preview = file['patch'][:200]
                if len(file['patch']) > 200:
                    patch_preview += '...'
                print(f"   Patch preview: {patch_preview}")
            print('')
        print(f"=== END Files Changed ===\n")

        # Add comment to the PR
        pr.create_issue_comment(MESSAGE_FOR_NEW_PRS)
        print(f"Successfully added comment to PR #{pr_number}")
        
    except Exception as error:
        print(f"Error processing PR #{pr_number}: {error}")

def handle_pull_request_synchronized(payload, github_app):
    """
    Handler for when PR is synchronized (new commits pushed)
    """
    pr_number = payload['pull_request']['number']
    repo_owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    pr_title = payload['pull_request']['title']
    
    print(f"Received a pull request synchronized event for #{pr_number}")
    print(f"Repository: {repo_owner}/{repo_name}")
    print(f"PR Title: {pr_title}")

    try:
        # Get installation access token
        access_token = get_installation_access_token(github_app, repo_owner, repo_name)
        if not access_token:
            print(f"Failed to get installation access token for {repo_owner}/{repo_name}")
            return
        
        # Get the repository and pull request
        repo = github_app.get_repo(f"{repo_owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Get the PR diff
        print(f"\n=== Fetching PR Diff (Synchronized) ===")
        diff_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "Authorization": f"token {access_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        diff_response = requests.get(diff_url, headers=headers)
        diff_response.raise_for_status()
        
        print(f"\n=== PR DIFF (Synchronized) ===")
        print(diff_response.text)
        print(f"=== END PR DIFF (Synchronized) ===\n")

        # Also get the files changed for additional context
        files_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
        files_response = requests.get(files_url, headers=headers)
        files_response.raise_for_status()
        files_data = files_response.json()

        print(f"\n=== Files Changed (Synchronized) ===")
        for index, file in enumerate(files_data, 1):
            print(f"{index}. {file['filename']}")
            print(f"   Status: {file['status']}")
            print(f"   Additions: +{file['additions']}")
            print(f"   Deletions: -{file['deletions']}")
            print(f"   Changes: {file['changes']}")
            if file.get('patch'):
                patch_preview = file['patch'][:200]
                if len(file['patch']) > 200:
                    patch_preview += '...'
                print(f"   Patch preview: {patch_preview}")
            print('')
        print(f"=== END Files Changed (Synchronized) ===\n")

        print(f"Successfully processed synchronized PR #{pr_number}")
        
    except Exception as error:
        print(f"Error processing synchronized PR #{pr_number}: {error}")

def handle_webhook_error(error):
    """
    This logs any errors that occur.
    """
    if hasattr(error, 'name') and error.name == "AggregateError":
        print(f"Error processing request: {error.event}")
    else:
        print(f"Webhook error: {error}")

def log_webhook_event(event_name, payload):
    """
    General webhook event logger for debugging
    """
    print(f"=== Webhook Event Received ===")
    print(f"Event: {event_name}")
    print(f"Action: {payload.get('action', 'N/A')}")
    print(f"Repository: {payload.get('repository', {}).get('full_name', 'N/A')}")
    print(f"===============================")
