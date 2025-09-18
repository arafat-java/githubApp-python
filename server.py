from flask import Flask, request, jsonify
import json
import hmac
import hashlib
from config import PORT, HOST, PATH, LOCAL_WEBHOOK_URL, WEBHOOK_SECRET

def create_app(github_app):
    """
    This creates a Flask server that listens for incoming HTTP requests (including webhook payloads from GitHub) 
    on the specified port. When the server receives a request, it executes the webhook handlers.
    """
    app = Flask(__name__)
    
    def verify_webhook_signature(payload, signature):
        """
        Verify the webhook signature to ensure the request is from GitHub
        """
        if not WEBHOOK_SECRET:
            return True  # Skip verification if no secret is set
        
        expected_signature = 'sha256=' + hmac.new(
            WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def logging_middleware():
        """
        Add logging middleware to track all incoming requests
        """
        print(f"[{request.method}] {request.url} - Server invoked!")
        
        # Log headers for POST requests
        if request.method == 'POST':
            print('POST Request Headers:')
            print(json.dumps(dict(request.headers), indent=2))
            
            # Log the GitHub event type if it's a webhook
            github_event = request.headers.get('X-GitHub-Event')
            if github_event:
                print(f"GitHub Event Type: {github_event}")
    
    @app.route(PATH, methods=['POST'])
    def webhook_handler():
        """
        Handle incoming webhook events from GitHub
        """
        try:
            # Apply logging middleware
            logging_middleware()
            
            # Get the payload and signature
            payload = request.get_data()
            signature = request.headers.get('X-Hub-Signature-256', '')
            
            # Verify the webhook signature
            if not verify_webhook_signature(payload, signature):
                print("Invalid webhook signature")
                return jsonify({'error': 'Invalid signature'}), 401
            
            # Parse the JSON payload
            try:
                payload_json = json.loads(payload.decode('utf-8'))
            except json.JSONDecodeError:
                print("Invalid JSON payload")
                return jsonify({'error': 'Invalid JSON'}), 400
            
            # Get the event type and action
            event_type = request.headers.get('X-GitHub-Event')
            action = payload_json.get('action')
            
            # Log the webhook event
            from handlers import log_webhook_event
            log_webhook_event(event_type, payload_json)
            
            # Handle different event types
            if event_type == 'pull_request':
                if action == 'opened':
                    from handlers import handle_pull_request_opened
                    handle_pull_request_opened(payload_json, github_app)
                elif action == 'synchronize':
                    from handlers import handle_pull_request_synchronized
                    handle_pull_request_synchronized(payload_json, github_app)
            
            return jsonify({'status': 'success'}), 200
            
        except Exception as error:
            from handlers import handle_webhook_error
            handle_webhook_error(error)
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint
        """
        return jsonify({'status': 'healthy'}), 200
    
    return app

def start_server(app):
    """
    Start the Flask server
    """
    print(f"Server is listening for events at: {LOCAL_WEBHOOK_URL}")
    print('Press Ctrl + C to quit.')
    app.run(host=HOST, port=PORT, debug=True)
