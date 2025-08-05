#!/usr/bin/env python3
"""
Production Setup Script for Pionex Trading Bot
This script helps configure the bot for production use.
"""

import os
import yaml
import shutil
from pathlib import Path

def create_env_file():
    """Create .env file from template"""
    env_template = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ALLOWED_USERS=123456789,987654321

# Pionex API Configuration
PIONEX_API_KEY=your_pionex_api_key_here
PIONEX_SECRET_KEY=your_pionex_secret_key_here

# Database Configuration
DATABASE_URL=sqlite:///trading_bot.db

# Logging Configuration
LOG_LEVEL=INFO

# Production Settings
DEBUG=false
ENVIRONMENT=production
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✅ Created .env file")
        print("⚠️  Please edit .env file with your real credentials")
    else:
        print("✅ .env file already exists")

def create_logs_directory():
    """Create logs directory"""
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    print("✅ Created logs directory")

def update_config_yaml():
    """Update config.yaml with production settings"""
    config_path = Path('config.yaml')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update production settings
        config['logging']['level'] = 'INFO'
        config['watchdog']['enabled'] = True
        config['notifications']['telegram']['enabled'] = True
        
        with open(config_path, 'w') as f:
            yaml.safe_dump(config, f, sort_keys=False)
        
        print("✅ Updated config.yaml with production settings")
    else:
        print("❌ config.yaml not found")

def create_docker_file():
    """Create Dockerfile for production deployment"""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Expose port (if needed for web interface)
EXPOSE 8080

# Run the bot
CMD ["python", "run.py"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    print("✅ Created Dockerfile")

def create_systemd_service():
    """Create systemd service file"""
    service_content = """[Unit]
Description=Pionex Trading Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/pionex-trading-bot
Environment=PATH=/opt/pionex-trading-bot/venv/bin
ExecStart=/opt/pionex-trading-bot/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open('pionex-trading-bot.service', 'w') as f:
        f.write(service_content)
    print("✅ Created systemd service file")

def create_backup_script():
    """Create backup script"""
    backup_script = """#!/bin/bash
# Backup script for Pionex Trading Bot

BACKUP_DIR="/backup/pionex-bot"
DATE=$(date +%Y%m%d_%H%M%S)
BOT_DIR="/opt/pionex-trading-bot"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp $BOT_DIR/trading_bot.db $BACKUP_DIR/trading_bot_$DATE.db

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz $BOT_DIR/logs/

# Backup config
cp $BOT_DIR/config.yaml $BACKUP_DIR/config_$DATE.yaml

echo "Backup completed: $BACKUP_DIR"
"""
    
    with open('backup.sh', 'w') as f:
        f.write(backup_script)
    os.chmod('backup.sh', 0o755)
    print("✅ Created backup script")

def main():
    """Main setup function"""
    print("🚀 Pionex Trading Bot - Production Setup")
    print("=" * 50)
    
    # Create necessary files and directories
    create_env_file()
    create_logs_directory()
    update_config_yaml()
    create_docker_file()
    create_systemd_service()
    create_backup_script()
    
    print("\n" + "=" * 50)
    print("✅ Production setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your real credentials")
    print("2. Test the bot: python run.py")
    print("3. For Docker deployment: docker build -t pionex-bot .")
    print("4. For systemd service: sudo cp pionex-trading-bot.service /etc/systemd/system/")
    print("5. Start service: sudo systemctl enable pionex-trading-bot && sudo systemctl start pionex-trading-bot")
    print("\n🔧 Configuration files:")
    print("- .env: Environment variables")
    print("- config.yaml: Bot configuration")
    print("- Dockerfile: Docker deployment")
    print("- pionex-trading-bot.service: Systemd service")
    print("- backup.sh: Backup script")

if __name__ == "__main__":
    main() 