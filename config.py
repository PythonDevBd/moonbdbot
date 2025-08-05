import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_USERS = os.getenv('ALLOWED_USERS', '').split(',')

# Pionex API Configuration
PIONEX_API_KEY = os.getenv('PIONEX_API_KEY')
PIONEX_SECRET_KEY = os.getenv('PIONEX_SECRET_KEY')
PIONEX_BASE_URL = "https://api.pionex.com"

# Trading Configuration
DEFAULT_LEVERAGE = 10
DEFAULT_MARGIN_TYPE = "isolated"
MAX_POSITION_SIZE = 0.1  # 10% of balance
STOP_LOSS_PERCENTAGE = 1.5  # -1.5%
TAKE_PROFIT_PERCENTAGE = 2.5  # +2.5%
TRAILING_STOP_PERCENTAGE = 1.0  # 1% trailing stop

# RSI Configuration
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Multi-Timeframe RSI Configuration
RSI_5M_OVERSOLD = 30
RSI_5M_OVERBOUGHT = 70
RSI_1H_NEUTRAL = 50

# Volume Filter Configuration
VOLUME_EMA_PERIOD = 20
VOLUME_MULTIPLIER = 1.5  # Volume must be 1.5x EMA

# MACD Configuration
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Database Configuration (for storing user data)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'trading_bot.log'

# Trading Pairs
SUPPORTED_PAIRS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
    'DOTUSDT', 'LINKUSDT', 'MATICUSDT', 'AVAXUSDT', 'UNIUSDT'
]

# Strategy Types
STRATEGY_TYPES = {
    'RSI_STRATEGY': 'RSI Strategy',
    'RSI_MULTI_TF': 'RSI Multi-Timeframe',
    'VOLUME_FILTER': 'Volume Filter Strategy',
    'ADVANCED_STRATEGY': 'Advanced Strategy',
    'GRID_TRADING': 'Grid Trading',
    'DCA': 'Dollar Cost Averaging',
    'MANUAL': 'Manual Trading'
}

# Strategy Descriptions
STRATEGY_DESCRIPTIONS = {
    'RSI_STRATEGY': 'Basic RSI strategy with oversold/overbought signals',
    'RSI_MULTI_TF': 'RSI analysis on 5-minute and 1-hour timeframes for trend confirmation',
    'VOLUME_FILTER': 'RSI strategy with volume filter using EMA(20)',
    'ADVANCED_STRATEGY': 'Combines RSI, MACD, Volume, and Candlestick patterns',
    'GRID_TRADING': 'Automated grid-based trading strategy',
    'DCA': 'Dollar Cost Averaging for regular investments',
    'MANUAL': 'Full manual control without automated decisions'
} 