#!/usr/bin/env python3
"""
Setup script to create .env file for Azure OpenAI configuration
"""

import os
import shutil
from pathlib import Path


def create_env_file():
    """Create a .env file from the template."""
    
    print("🔧 Azure OpenAI Environment Setup")
    print("=" * 50)
    
    # Paths
    template_file = Path("env_template.txt")
    env_file = Path(".env")
    
    if not template_file.exists():
        print("❌ Template file 'env_template.txt' not found!")
        print("Make sure you're running this script from the code_reviewer directory.")
        return False
    
    # Check if .env already exists
    if env_file.exists():
        response = input("📋 .env file already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("✅ Keeping existing .env file")
            return True
    
    # Copy template to .env
    try:
        shutil.copy2(template_file, env_file)
        print("✅ Created .env file from template")
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False
    
    print("\n📝 Next steps:")
    print("1. Edit the .env file with your Azure credentials:")
    print(f"   nano {env_file}")
    print("   # or")
    print(f"   code {env_file}")
    print()
    print("2. Fill in these required values:")
    print("   - AZURE_TENANT_ID")
    print("   - AZURE_CLIENT_ID") 
    print("   - AZURE_CLIENT_SECRET")
    print("   - AZURE_ENDPOINT")
    print()
    print("3. Test your configuration:")
    print("   python azure_setup.py")
    print()
    
    return True


def check_env_file():
    """Check if .env file exists and show status."""
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ No .env file found")
        return False
    
    print("✅ .env file exists")
    
    # Try to load and validate
    try:
        from util.config import get_secrets, validate_azure_config
        
        print("\n📋 Current configuration:")
        secrets = get_secrets()
        
        for key, value in secrets.items():
            if value:
                # Mask sensitive values
                if 'secret' in key.lower():
                    masked = value[:8] + "..." if len(value) > 8 else "***"
                    print(f"  {key}: {masked} ✅")
                else:
                    print(f"  {key}: {value} ✅")
            else:
                print(f"  {key}: NOT SET ❌")
        
        if validate_azure_config():
            print("\n🎉 Configuration looks good!")
            print("Run 'python azure_setup.py' to test the connection.")
        else:
            print("\n⚠️ Configuration incomplete. Please fill in missing values.")
            
    except Exception as e:
        print(f"\n❌ Error checking configuration: {e}")
        return False
    
    return True


def main():
    """Main setup function."""
    
    print("🚀 Azure OpenAI Multi-Agent Code Review - Environment Setup")
    print("=" * 70)
    
    # Check current directory
    if not Path("env_template.txt").exists():
        print("❌ Please run this script from the code_reviewer directory")
        print("cd to the directory containing 'env_template.txt'")
        return
    
    # Show menu
    print("\nChoose an option:")
    print("1. Create new .env file from template")
    print("2. Check existing .env file")
    print("3. Show template content")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        create_env_file()
    elif choice == "2":
        check_env_file()
    elif choice == "3":
        template_file = Path("env_template.txt")
        if template_file.exists():
            print("\n📋 Template content:")
            print("-" * 50)
            with open(template_file, 'r') as f:
                print(f.read())
        else:
            print("❌ Template file not found")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
