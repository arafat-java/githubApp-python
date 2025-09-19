import requests
from github import Github, Auth, GithubIntegration
import json
from datetime import datetime
from code_review_integration import get_code_review_integration
from pr_summarizer_integration import get_pr_summarizer_integration

# This defines the message that your app will post to pull requests.
# MESSAGE_FOR_NEW_PRS = "Thanks for opening a new PR! Please follow our contributing guidelines to make your PR easier to review."

def create_bot_review_comment():
    """
    Create a comment indicating the PR has been reviewed by the Innovation days bot
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"🤖 **Innovation days bot** has reviewed this PR at `{timestamp}`"

def create_ignore_message():
    """
    Create a message when PR review is ignored
    """
    return "You demanded I shut up? Alright.\nBut don't cry when that for loop turns into Skynet. 🤖"

def should_skip_review(pr_description):
    """
    Check if PR description contains the ignore flag
    
    Args:
        pr_description: The PR description text
        
    Returns:
        bool: True if review should be skipped, False otherwise
    """
    if not pr_description:
        return False
    
    # Check for the exact ignore flag string
    return "@adsk_pr_review_bot_ignore" in pr_description

def get_installation_github(github_app, repo_owner, repo_name):
    """
    Get a GitHub instance authenticated with installation access token for the repository
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
        
        # Create a new GitHub instance with the installation access token
        installation_github = Github(access_token.token)
        
        return installation_github, access_token.token
    except Exception as error:
        print(f"Error getting installation GitHub instance: {error}")
        return None, None

def _process_pull_request(payload, github_app, is_new_pr=False):
    """
    Common method to process pull request events (opened or synchronized).
    
    Args:
        payload: GitHub webhook payload
        github_app: GitHub app instance
        is_new_pr: Boolean flag indicating if this is a new PR (True) or synchronized PR (False)
    """
    pr_number = payload['pull_request']['number']
    repo_owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    pr_title = payload['pull_request']['title']
    pr_description = payload['pull_request'].get('body', '')
    
    event_type = "opened" if is_new_pr else "synchronized"
    print(f"Received a pull request {event_type} event for #{pr_number}")
    print(f"Repository: {repo_owner}/{repo_name}")
    print(f"PR Title: {pr_title}")
    
    # Check if PR review should be skipped
    if should_skip_review(pr_description):
        print(f"PR #{pr_number} contains @adsk_pr_review_bot_ignore - skipping review and summarization")
        try:
            # Get installation-authenticated GitHub instance
            installation_github, access_token = get_installation_github(github_app, repo_owner, repo_name)
            if installation_github and access_token:
                # Get the repository and pull request using installation auth
                repo = installation_github.get_repo(f"{repo_owner}/{repo_name}")
                pr = repo.get_pull(pr_number)
                
                # Add the ignore message
                ignore_comment = create_ignore_message()
                pr.create_issue_comment(ignore_comment)
                print(f"Successfully added ignore message to {event_type} PR #{pr_number}")
            else:
                print(f"Failed to get installation GitHub instance for ignore message in {repo_owner}/{repo_name}")
        except Exception as error:
            print(f"Error adding ignore message to {event_type} PR #{pr_number}: {error}")
        return

    try:
        # Get installation-authenticated GitHub instance
        installation_github, access_token = get_installation_github(github_app, repo_owner, repo_name)
        if not installation_github or not access_token:
            print(f"Failed to get installation GitHub instance for {repo_owner}/{repo_name}")
            return
        
        # Get the repository and pull request using installation auth
        repo = installation_github.get_repo(f"{repo_owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Get the PR diff
        print(f"\n=== Fetching PR Diff ({'New' if is_new_pr else 'Synchronized'}) ===")
        diff_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "Authorization": f"token {access_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        diff_response = requests.get(diff_url, headers=headers)
        diff_response.raise_for_status()
        
        print(f"\n=== PR DIFF ({'New' if is_new_pr else 'Synchronized'}) ===")
        print(diff_response.text)
        print(f"=== END PR DIFF ({'New' if is_new_pr else 'Synchronized'}) ===\n")

        # Also get the files changed for additional context
        files_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
        files_response = requests.get(files_url, headers=headers)
        files_response.raise_for_status()
        files_data = files_response.json()

        print(f"\n=== Files Changed ({'New' if is_new_pr else 'Synchronized'}) ===")
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
                # Only show patch preview for new PRs to reduce noise
                if is_new_pr:
                    print(f"   Patch preview: {patch_preview}")
            print('')
        print(f"=== END Files Changed ({'New' if is_new_pr else 'Synchronized'}) ===\n")

        # # Add welcome message only for new PRs
        # if is_new_pr:
        #     pr.create_issue_comment(MESSAGE_FOR_NEW_PRS)
        #     print(f"Successfully added welcome comment to PR #{pr_number}")
        
        # Add bot review comment
        bot_comment = create_bot_review_comment()
        pr.create_issue_comment(bot_comment)
        print(f"Successfully added bot review comment to {event_type} PR #{pr_number}")
        
        # Perform automated PR summarization
        try:
            pr_summarizer_integration = get_pr_summarizer_integration()
            if pr_summarizer_integration:
                print(f"Starting automated PR summarization for {event_type} PR #{pr_number}")
                
                # Get PR info for the summarization
                pr_info = {
                    'number': pr_number,
                    'title': pr_title,
                    'repo_owner': repo_owner,
                    'repo_name': repo_name
                }
                
                # Generate PR summary using the files data (will use fallback if AI not available)
                summary_comment = pr_summarizer_integration.summarize_pr_files(files_data, pr_info)
                
                if summary_comment:
               
                    # Add the detailed summary (or fallback summary)
                    pr.create_issue_comment(summary_comment)
                    print(f"Successfully added automated PR summary to {event_type} PR #{pr_number}")
                else:
                    print(f"PR summarization failed for {event_type} PR #{pr_number}")
            else:
                print(f"PR summarizer integration not available for {event_type} PR #{pr_number}")
        except Exception as summary_error:
            print(f"Error during PR summarization for {event_type} PR #{pr_number}: {summary_error}")
        
        # Perform automated code review
        try:
            code_review_integration = get_code_review_integration()
            if code_review_integration and code_review_integration.is_available():
                print(f"Starting automated code review for {event_type} PR #{pr_number}")
                
                # Get PR info for the review
                pr_info = {
                    'number': pr_number,
                    'title': pr_title,
                    'repo_owner': repo_owner,
                    'repo_name': repo_name
                }
                
                # Perform code review using the diff
                review_comment = code_review_integration.review_pr_diff(diff_response.text, pr_info)
                
                if review_comment:
                
                    # Add the detailed review
                    pr.create_issue_comment(review_comment)
                    print(f"Successfully added automated code review to {event_type} PR #{pr_number}")
                else:
                    print(f"Code review failed for {event_type} PR #{pr_number}")
            else:
                print(f"Code review functionality not available for {event_type} PR #{pr_number}")
        except Exception as review_error:
            print(f"Error during code review for {event_type} PR #{pr_number}: {review_error}")
        
        if not is_new_pr:
            print(f"Successfully processed {event_type} PR #{pr_number}")
        
    except Exception as error:
        print(f"Error processing {event_type} PR #{pr_number}: {error}")

def handle_pull_request_opened(payload, github_app):
    """
    This adds an event handler that your code will call later. When this event handler is called, 
    it will log the event to the console. Then, it will use GitHub's REST API to add a comment 
    to the pull request that triggered the event.
    """
    _process_pull_request(payload, github_app, is_new_pr=True)

def handle_pull_request_synchronized(payload, github_app):
    """
    Handler for when PR is synchronized (new commits pushed)
    """
    _process_pull_request(payload, github_app, is_new_pr=False)

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
