#!/usr/bin/env python3
"""
PR Summarizer Example - Demonstrates how to use the PR summarizer with JSON input.
"""

import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from pr_summarizer import PRSummarizerApp


def example_json_data():
    """Sample JSON data for demonstration."""
    return [
        {
            "filename": "src/auth.py",
            "status": "modified",
            "additions": 25,
            "deletions": 5,
            "diff": "Added bcrypt for password hashing and verification"
        },
        {
            "filename": "src/database.py",
            "status": "added",
            "additions": 45,
            "deletions": 0,
            "diff": "Added DatabaseManager class for user authentication"
        },
        {
            "filename": "tests/test_auth.py",
            "status": "modified",
            "additions": 15,
            "deletions": 3,
            "diff": "Updated tests to use bcrypt password hashing"
        }
    ]


def run_example():
    """Run the PR summarizer example with JSON input."""
    print("🚀 PR Summarizer Example")
    print("=" * 60)
    
    # Initialize the summarizer with Azure OpenAI
    print("Initializing PR Summarizer...")
    try:
        summarizer = PRSummarizerApp()  # Requires Azure OpenAI credentials
    except ValueError as e:
        print(f"❌ {e}")
        print("Please set up Azure OpenAI environment variables and try again.")
        return
    
    # Get example JSON data
    json_data = example_json_data()
    additional_context = """
    This PR improves the authentication system by:
    1. Replacing insecure SHA256 password hashing with bcrypt
    2. Adding proper password verification
    3. Implementing token validation and refresh functionality
    4. Adding a database layer for user management
    5. Expanding test coverage for the new functionality
    
    This addresses security vulnerabilities in the previous implementation
    and provides a more robust authentication system.
    """
    
    print("Analyzing JSON file changes...")
    print(f"Number of files: {len(json_data)}")
    print(f"Context provided: {bool(additional_context.strip())}")
    
    for item in json_data:
        print(f"  - {item['filename']}: +{item['additions']}/-{item['deletions']} ({item['status']})")
    
    try:
        # Generate summary
        print("\n🔄 Generating PR summary...")
        summary = summarizer.summarize_from_json(json_data, additional_context)
        
        print("✅ Summary generated successfully!")
        
        # Display statistics
        print(f"\n📊 Statistics:")
        print(f"  Files changed: {summary.files_changed}")
        print(f"  Lines added: {summary.total_additions}")
        print(f"  Lines deleted: {summary.total_deletions}")
        
        # Generate the JSON output as the app would
        markdown_summary = summarizer.format_summary(summary, "markdown")
        json_output = {
            "summary": markdown_summary
        }
        
        print(f"\n" + "=" * 80)
        print(f"📝 JSON OUTPUT (as returned by the app)")
        print("=" * 80)
        
        json_output_str = json.dumps(json_output, indent=2, ensure_ascii=False)
        
        # Truncate very long outputs for readability
        if len(json_output_str) > 2000:
            print(json_output_str[:2000])
            print(f"\n... (truncated, {len(json_output_str) - 2000} more characters)")
        else:
            print(json_output_str)
        
        # Save output to file
        print(f"\n💾 Saving JSON output to file...")
        filename = "example_pr_summary.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_output_str)
        
        print(f"  Saved JSON output to: {filename}")
        
        print(f"\n🎉 Example completed successfully!")
        print(f"The output format matches what the CLI app produces.")
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        print(f"Make sure you have the required dependencies installed and AI service configured.")


def interactive_demo():
    """Interactive demo mode with JSON input."""
    print("🎮 Interactive PR Summarizer Demo")
    print("=" * 60)
    
    print("This demo will show you how to use the PR summarizer with JSON input.")
    print("You can either:")
    print("1. Use the example JSON data (recommended for first time)")
    print("2. Provide your own JSON file path")
    print("3. Paste your own JSON content")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        json_data = example_json_data()
        context = "Authentication system security improvements"
        print("✅ Using example JSON data")
    elif choice == "2":
        file_path = input("Enter path to JSON file: ").strip()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            context = input("Additional context (optional): ").strip()
            print(f"✅ Loaded JSON from {file_path}")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return
    elif choice == "3":
        print("\nPaste your JSON content (press Ctrl+D when done):")
        print("Expected format: [{'filename': '...', 'status': '...', 'additions': 0, 'deletions': 0, 'diff': '...'}]")
        try:
            json_content = sys.stdin.read()
            json_data = json.loads(json_content)
            context = input("Additional context (optional): ").strip()
            print("✅ Parsed JSON content")
        except KeyboardInterrupt:
            print("\nDemo cancelled.")
            return
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format: {e}")
            return
    else:
        print("Invalid choice. Using example JSON data.")
        json_data = example_json_data()
        context = "Authentication system security improvements"
    
    if not json_data:
        print("No JSON data provided. Exiting.")
        return
    
    # Validate JSON structure
    if not isinstance(json_data, list):
        print("❌ JSON must be a list of file changes")
        return
    
    print(f"\n📊 Found {len(json_data)} file changes:")
    for item in json_data:
        filename = item.get('filename', 'unknown')
        status = item.get('status', 'unknown')
        additions = item.get('additions', 0)
        deletions = item.get('deletions', 0)
        print(f"  - {filename}: +{additions}/-{deletions} ({status})")
    
    try:
        print(f"\n🔄 Initializing summarizer with Azure OpenAI...")
        summarizer = PRSummarizerApp()
        
        print("🔍 Analyzing JSON data and generating summary...")
        summary = summarizer.summarize_from_json(json_data, context)
        
        # Generate JSON output as the CLI app would
        markdown_summary = summarizer.format_summary(summary, "markdown")
        json_output = {
            "summary": markdown_summary
        }
        
        print("\n" + "=" * 80)
        print("📋 PR SUMMARY (JSON OUTPUT)")
        print("=" * 80)
        
        json_output_str = json.dumps(json_output, indent=2, ensure_ascii=False)
        print(json_output_str)
        
        # Option to save
        save_file = input(f"\nSave to file? (y/N): ").strip().lower() == 'y'
        if save_file:
            filename = input("Filename (default: pr_summary.json): ").strip()
            if not filename:
                filename = "pr_summary.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_output_str)
            print(f"✅ Summary saved to {filename}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PR Summarizer Examples")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Run interactive demo")
    parser.add_argument("--example", "-e", action="store_true",
                       help="Run example with sample data")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_demo()
    elif args.example:
        run_example()
    else:
        # Default to example
        run_example()


if __name__ == "__main__":
    main()