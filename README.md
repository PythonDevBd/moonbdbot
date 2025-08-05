# Pionex Trading Bot

A comprehensive Telegram trading bot for Pionex exchange with advanced automated trading capabilities, multi-timeframe RSI analysis, volume filters, MACD confirmation, and dynamic risk management.

## 🚀 Advanced Features

### 📊 RSI Multi-Timeframe Analysis
- **Timeframes**: 5 minutes and 1 hour
- **Long Entry**: RSI(5m) < 30 AND RSI(1h) < 50
- **Short Entry**: RSI(5m) > 70 AND RSI(1h) > 50
- **Function**: Avoids false signals and entries against the trend

### 📈 Volume Filter (EMA)
- **Calculation**: EMA(volume, 20)
- **Valid Entry**: current_volume > 1.5 × EMA(volume)
- **Function**: Allows entry only when there is significant movement

### 🛡️ Dynamic Risk Management
- **Dynamic Stop Loss**: -1.5% (configurable)
- **Dynamic Take Profit**: +2.5% (configurable)
- **Trailing Stop**: Enabled after initial TP is reached
- **Dynamic Mobile SL**: Adjusts upward as price continues favorably

### 📊 MACD Confirmation
- **MACD Crossover**: Used to confirm trend direction
- **Supporting Filter**: Only used as additional confirmation
- **Parameters**: Fast(12), Slow(26), Signal(9)

### 🕯️ Candlestick OHLC Analysis
- **Pattern Recognition**: Engulfing, pin bar (hammer/shooting star)
- **Visual Confirmation**: Provides additional context for entries
- **Pattern Types**: Bullish/Bearish engulfing, hammer, shooting star

### 🎯 Advanced Trading Strategies

#### 1. RSI Multi-Timeframe Strategy
```python
# Long entry conditions
if rsi_5m < 30 and rsi_1h < 50:
    # Strong buy signal
# Short entry conditions  
if rsi_5m > 70 and rsi_1h > 50:
    # Strong sell signal
```

#### 2. Volume Filter Strategy
```python
# Volume filter condition
volume_filter = current_volume > (volume_ema * 1.5)
if rsi < 30 and volume_filter:
    # Valid buy signal
```

#### 3. Advanced Strategy
```python
# Combines all indicators
bullish_conditions = (
    rsi < 30 and  # RSI oversold
    macd_crossover in ['bullish', 'neutral'] and  # MACD not bearish
    volume_filter and  # High volume
    candlestick_signal in ['bullish', 'neutral']  # Candlestick confirmation
)
```

## Features

### 🔐 Authentication & Security
- User authentication via Telegram
- API key management for Pionex
- Secure HMAC signature generation
- User authorization system

### 💰 Account Management
- Real-time balance monitoring
- Position tracking and management
- Portfolio performance analytics
- Trading history with detailed logs

### 🤖 Automated Trading
- Multiple advanced trading strategies
- Configurable risk management
- Automatic trade execution with stop loss/take profit
- Strategy parameter customization

### 📊 Technical Analysis
- RSI (Relative Strength Index) calculation
- Multi-timeframe RSI analysis
- MACD trend confirmation
- Volume analysis with EMA
- Candlestick pattern recognition
- Real-time market data analysis

### 📈 Portfolio Management
- Real-time portfolio tracking
- PnL calculation and monitoring
- Position sizing and risk management
- Portfolio performance history

### 🎯 Trading Strategies
- **RSI Strategy**: Basic RSI with oversold/overbought signals
- **RSI Multi-Timeframe**: 5m and 1h timeframe analysis
- **Volume Filter**: RSI with volume confirmation
- **Advanced Strategy**: Combines RSI, MACD, Volume, and Candlestick
- **Grid Trading**: Automated grid-based trading
- **DCA (Dollar Cost Averaging)**: Regular investment strategy
- **Manual Trading**: Full manual control

### 📱 Telegram Interface
- Inline keyboard navigation
- Real-time notifications
- Interactive trading interface
- Advanced technical analysis display
- Status monitoring and alerts

## Installation

### Prerequisites
- Python 3.8 or higher
- Pionex API credentials
- Telegram Bot Token

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PionexTradeBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp env_example.txt .env
   ```
   
   Edit `.env` file with your credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   PIONEX_API_KEY=your_pionex_api_key
   PIONEX_SECRET_KEY=your_pionex_secret_key
   ALLOWED_USERS=your_telegram_user_id
   ```

4. **Test advanced features**
   ```bash
   python test_advanced_features.py
   ```

5. **Run the bot**
   ```bash
   python run.py
   ```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Yes |
| `PIONEX_API_KEY` | Pionex API key | Yes |
| `PIONEX_SECRET_KEY` | Pionex secret key | Yes |
| `ALLOWED_USERS` | Comma-separated list of authorized user IDs | No |
| `DATABASE_URL` | Database connection string | No |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) | No |

### Advanced Trading Configuration

The bot supports extensive advanced configuration:

- **Default Leverage**: 10x (configurable)
- **Risk Percentage**: 10% per trade (configurable)
- **Max Positions**: 5 concurrent positions (configurable)
- **RSI Period**: 14 (configurable)
- **RSI Overbought**: 70 (configurable)
- **RSI Oversold**: 30 (configurable)
- **Stop Loss**: -1.5% (configurable)
- **Take Profit**: +2.5% (configurable)
- **Trailing Stop**: 1% (configurable)
- **Volume EMA Period**: 20 (configurable)
- **Volume Multiplier**: 1.5x (configurable)
- **MACD Parameters**: Fast(12), Slow(26), Signal(9)

## Usage

### Starting the Bot

1. Start the bot with `/start` command
2. Navigate through the main menu
3. Configure your trading settings
4. Set up automated strategies

### Main Menu Options

- **💰 Balance**: View account balance and assets
- **📊 Positions**: Monitor current positions
- **📈 Portfolio**: Portfolio overview and performance
- **📋 Trading History**: View recent trades
- **⚙️ Settings**: Configure bot settings
- **📊 Technical Analysis**: Advanced analysis tools
- **🤖 Auto Trading**: Automated trading controls
- **📝 Manual Trade**: Manual trading interface
- **🎯 Strategies**: Strategy management
- **📊 Status**: Bot status and health

### Advanced Technical Analysis

- **📈 RSI Analysis**: Basic RSI signals
- **📊 Multi-Timeframe RSI**: 5m and 1h analysis
- **📈 Volume Filter Analysis**: Volume confirmation
- **📊 Advanced Analysis**: Combined indicators
- **📈 MACD Analysis**: Trend confirmation
- **🕯️ Candlestick Patterns**: Pattern recognition

### Setting Up Advanced Automated Trading

1. Go to **Settings** → **Auto Trading**
2. Enable auto trading
3. Go to **Strategies** and select an advanced strategy:
   - **RSI Multi-Timeframe**: For trend confirmation
   - **Volume Filter**: For volume-based entries
   - **Advanced Strategy**: For comprehensive analysis
4. Choose trading pairs
5. Configure strategy parameters
6. Monitor performance in **Portfolio**

### Advanced Trading Strategies

#### RSI Multi-Timeframe Strategy
- Analyzes RSI on both 5-minute and 1-hour timeframes
- Long entry: RSI(5m) < 30 AND RSI(1h) < 50
- Short entry: RSI(5m) > 70 AND RSI(1h) > 50
- Avoids false signals and entries against the trend

#### Volume Filter Strategy
- Uses EMA(volume, 20) for volume analysis
- Valid entry if: current_volume > 1.5 × EMA(volume)
- Allows entry only when there is significant movement
- Reduces false signals during low-volume periods

#### Advanced Strategy
- Combines RSI, MACD, Volume, and Candlestick patterns
- Dynamic Stop Loss: -1.5%
- Dynamic Take Profit: +2.5%
- Trailing Stop enabled after initial TP
- Comprehensive signal confirmation

## API Integration

The bot integrates with Pionex API for:

- Account information and balance
- Position management
- Order placement and cancellation with stop loss/take profit
- Market data retrieval for multiple timeframes
- Real-time price feeds

## Database

The bot uses SQLite database to store:

- User information and settings
- Trading history with strategy details
- Active strategies with parameters
- Portfolio snapshots
- Performance metrics

## Security Features

- HMAC signature authentication
- User authorization system
- Secure API key management
- Error handling and logging
- Rate limiting protection

## Risk Management

- Configurable position sizing
- Maximum position limits
- Risk percentage controls
- Dynamic stop-loss and take-profit orders
- Trailing stop functionality
- Portfolio diversification

## Monitoring and Logging

- Real-time bot status monitoring
- Detailed trading logs with strategy information
- Error tracking and reporting
- Performance analytics
- Portfolio snapshots

## Testing

### Basic Tests
```bash
python test_bot.py
```

### Advanced Features Tests
```bash
python test_advanced_features.py
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Verify API credentials
   - Check network connectivity
   - Ensure API permissions

2. **Telegram Bot Issues**
   - Verify bot token
   - Check user authorization
   - Ensure bot is running

3. **Trading Errors**
   - Check account balance
   - Verify position limits
   - Review risk settings

4. **Advanced Features Issues**
   - Check market data availability
   - Verify strategy parameters
   - Review technical analysis settings

### Logs

Check the log file for detailed error information:
```bash
tail -f trading_bot.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This bot is for educational and demonstration purposes. Trading cryptocurrencies involves significant risk. Always:

- Test thoroughly with small amounts
- Understand the risks involved
- Never invest more than you can afford to lose
- Monitor the bot regularly
- Keep your API keys secure

## Support

For support and questions:
- Check the documentation
- Review the logs
- Open an issue on GitHub

---

**⚠️ Warning**: This is a trading bot that can execute real trades. Use at your own risk and always test thoroughly before using with real funds.

**🚀 Advanced Features**: The bot now includes sophisticated technical analysis, multi-timeframe analysis, volume filters, and dynamic risk management for professional trading. 