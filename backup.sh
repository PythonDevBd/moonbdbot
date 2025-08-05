#!/bin/bash
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
