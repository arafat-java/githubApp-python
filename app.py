from github import Github, Auth
from config import APP_ID, PRIVATE_KEY_PATH
from server import create_app, start_server

def main():
    """
    Main application entry point
    """
    # Read the private key content
    with open(PRIVATE_KEY_PATH, 'r') as f:
        private_key_content = f.read()
    
    # Create GitHub App authentication using the new PyGithub Auth system
    auth = Auth.AppAuth(
        app_id=int(APP_ID),
        private_key=private_key_content
    )
    
    # Create GitHub instance with app authentication
    github_app = Github(auth=auth)
    
    # Create and start the server
    app = create_app(github_app)
    start_server(app)

if __name__ == "__main__":
    main()
