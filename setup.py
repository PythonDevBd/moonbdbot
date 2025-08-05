#!/usr/bin/env python3
"""
Setup script for Pionex Trading Bot
Helps users install and configure the bot
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ env_example.txt not found")
        return False
    
    try:
        # Copy env_example.txt to .env
        with open(env_example, 'r') as src:
            content = src.read()
        
        with open(env_file, 'w') as dst:
            dst.write(content)
        
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your credentials")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_env_variables():
    """Check if required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'PIONEX_API_KEY',
        'PIONEX_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("📝 Please set these in your .env file")
        return False
    
    print("✅ All required environment variables are set")
    return True

def run_tests():
    """Run bot tests"""
    print("🧪 Running bot tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_bot.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def print_setup_instructions():
    """Print setup instructions"""
    print("\n" + "=" * 50)
    print("🚀 Pionex Trading Bot Setup Complete!")
    print("=" * 50)
    
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your credentials:")
    print("   - TELEGRAM_BOT_TOKEN: Get from @BotFather")
    print("   - PIONEX_API_KEY: Your Pionex API key")
    print("   - PIONEX_SECRET_KEY: Your Pionex secret key")
    print("   - ALLOWED_USERS: Your Telegram user ID")
    
    print("\n2. Test the bot:")
    print("   python test_bot.py")
    
    print("\n3. Run the bot:")
    print("   python run.py")
    
    print("\n4. Start the bot in Telegram:")
    print("   Send /start to your bot")
    
    print("\n⚠️ Important:")
    print("- Test with small amounts first")
    print("- Monitor the bot regularly")
    print("- Keep your API keys secure")
    print("- Never invest more than you can afford to lose")

def main():
    """Main setup function"""
    print("🚀 Setting up Pionex Trading Bot...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("❌ Setup failed at .env file creation")
        sys.exit(1)
    
    # Check environment variables
    if not check_env_variables():
        print("⚠️ Environment variables not set - please configure .env file")
    
    # Run tests (optional)
    print("\n🧪 Would you like to run tests? (y/n): ", end="")
    try:
        response = input().lower().strip()
        if response in ['y', 'yes']:
            run_tests()
    except KeyboardInterrupt:
        print("\n⏹️ Setup interrupted")
        sys.exit(1)
    
    # Print instructions
    print_setup_instructions()

if __name__ == "__main__":
    main() 