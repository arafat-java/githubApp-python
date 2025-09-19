#!/usr/bin/env python3
"""
Setup script for PR Summarizer - helps users configure the environment.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ is required")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_requirements():
    """Install required packages."""
    print("📦 Installing requirements...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True)
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def check_git():
    """Check if git is available."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        print("✅ Git is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git is not installed or not in PATH")
        return False


def setup_azure_config():
    """Guide user through Azure OpenAI setup."""
    print("\n🔧 Azure OpenAI Configuration")
    print("=" * 40)
    
    required_vars = [
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID", 
        "AZURE_CLIENT_SECRET",
        "AZURE_ENDPOINT"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if not missing_vars:
        print("✅ All Azure environment variables are set")
        return True
    
    print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
    print("\nTo use Azure OpenAI, set these environment variables:")
    print("\n# Add to your ~/.bashrc or ~/.zshrc:")
    for var in missing_vars:
        print(f'export {var}="your-{var.lower().replace("_", "-")}"')
    
    print("\n# Or set for current session:")
    for var in missing_vars:
        print(f'export {var}="your-{var.lower().replace("_", "-")}"')
    
    return False




def run_demo():
    """Run the demo to test functionality."""
    print("\n🧪 Running Demo...")
    
    try:
        demo_path = Path(__file__).parent / "demo.py"
        result = subprocess.run([sys.executable, str(demo_path)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Demo completed successfully")
            print(result.stdout)
            return True
        else:
            print("❌ Demo failed")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        return False


def show_usage_examples():
    """Show usage examples."""
    print("\n📚 Usage Examples")
    print("=" * 40)
    
    examples = [
        ("JSON file analysis", "python3 pr_summarizer.py --json-file example_changes.json"),
        ("JSON string input", 'python3 pr_summarizer.py --json-input \'[{"filename":"app.py","status":"modified","additions":5,"deletions":2}]\''),
        ("Stdin input", "cat example_changes.json | python3 pr_summarizer.py --json-input -"),
        ("With context", "python3 pr_summarizer.py --json-file example_changes.json --context 'Bug fix'"),
        ("Save to file", "python3 pr_summarizer.py --json-file example_changes.json --output summary.json"),
        ("Example demo", "python3 example.py --example"),
    ]
    
    for description, command in examples:
        print(f"• {description}:")
        print(f"  {command}")
        print()


def main():
    """Main setup function."""
    print("🚀 PR Summarizer Setup")
    print("=" * 50)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Check Git
    if not check_git():
        print("⚠️ Git is required for some features")
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Check Azure config
    azure_ready = setup_azure_config()
    
    if not azure_ready:
        print("\n⚠️ Azure OpenAI is not configured")
        print("   Azure OpenAI credentials are required to use the PR Summarizer")
        success = False
    
    # Run demo if basic setup is successful
    if success:
        if input("\n🧪 Run demo to test functionality? (Y/n): ").strip().lower() != 'n':
            demo_success = run_demo()
            if not demo_success:
                success = False
    
    # Show results
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        show_usage_examples()
        
        print("🔗 Next Steps:")
        if azure_ready:
            print("  • You're ready to use Azure OpenAI")
        else:
            print("  • Set up Azure OpenAI credentials to get started")
        
        print("\n🚀 Start with: python3 pr_summarizer.py --json-file example_changes.json")
    else:
        print("❌ Setup encountered issues")
        print("   Please resolve the errors above and run setup again")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
