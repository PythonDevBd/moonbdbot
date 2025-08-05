import asyncio
import logging
import threading
import time
import json
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config_loader import get_config, reload_config
from pionex_api import PionexAPI
from trading_strategies import TradingStrategies
from database import Database

class AutoTrader:
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.api = PionexAPI()
        self.strategies = TradingStrategies(self.api)
        self.db = Database()
        self.config = get_config()
        
        # Single-pair operation
        self.current_pair = self.config.get('trading_pair', 'BTCUSDT')
        self.is_running = False
        self.auto_trading_enabled = False
        
        # Setup dedicated logging per instance
        self.setup_logging()
        
        # Threading
        self.trading_thread = None
        self.stop_event = threading.Event()
        
        # Restart tracking
        self.restart_count = 0
        self.last_restart = None
        
        # Notification settings
        self.notification_settings = self.config.get('notifications', {})
        
    def setup_logging(self):
        """Setup dedicated logging for this instance"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Create instance-specific log file
        instance_id = f"user_{self.user_id}" if self.user_id else "global"
        log_file = log_dir / f"auto_trader_{instance_id}.log"
        
        # Configure logging
        self.logger = logging.getLogger(f"AutoTrader_{instance_id}")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"AutoTrader instance initialized for {instance_id}")
    
    def enable_auto_trading(self, user_id: int = None):
        """Enable auto trading for a user"""
        if user_id:
            self.user_id = user_id
            self.setup_logging()  # Re-setup logging with user_id
        
        self.auto_trading_enabled = True
        self.db.update_user_settings(user_id or self.user_id, {'auto_trading': True})
        self.logger.info(f"Auto trading enabled for user {user_id or self.user_id}")
        self.send_notification("🤖 Auto Trading Enabled", f"Auto trading has been enabled for {self.current_pair}")
        
        if not self.is_running:
            self.start_auto_trading()
    
    def disable_auto_trading(self, user_id: int = None):
        """Disable auto trading for a user"""
        self.auto_trading_enabled = False
        self.db.update_user_settings(user_id or self.user_id, {'auto_trading': False})
        self.logger.info(f"Auto trading disabled for user {user_id or self.user_id}")
        self.send_notification("❌ Auto Trading Disabled", f"Auto trading has been disabled for {self.current_pair}")
        
        if self.is_running:
            self.stop_auto_trading()
    
    def set_trading_pair(self, pair: str):
        """Set the trading pair for single-pair operation"""
        old_pair = self.current_pair
        self.current_pair = pair.upper()
        self.config['trading_pair'] = self.current_pair
        
        # Update config file
        try:
            import yaml
            with open(Path('config.yaml'), 'w') as f:
                yaml.safe_dump(self.config, f, sort_keys=False)
            reload_config()
            self.config = get_config()
        except Exception as e:
            self.logger.error(f"Failed to update config file: {e}")
        
        self.logger.info(f"Trading pair changed from {old_pair} to {self.current_pair}")
        self.send_notification("🔄 Trading Pair Changed", f"Trading pair changed to {self.current_pair}")
    
    def start_auto_trading(self):
        """Start the auto trading loop"""
        if self.is_running:
            self.logger.warning("Auto trading is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.trading_thread.start()
        self.logger.info(f"Auto trading started for {self.current_pair}")
    
    def stop_auto_trading(self):
        """Stop the auto trading loop"""
        if not self.is_running:
            self.logger.warning("Auto trading is not running")
            return
        
        self.is_running = False
        self.stop_event.set()
        
        if self.trading_thread and self.trading_thread.is_alive():
            self.trading_thread.join(timeout=5)
        
        self.logger.info("Auto trading stopped")
    
    def restart_auto_trading(self, user_id: int = None):
        """Restart auto trading"""
        self.logger.info("Restarting auto trading...")
        self.restart_count += 1
        self.last_restart = datetime.now()
        
        # Stop current instance
        self.stop_auto_trading()
        
        # Wait a moment
        time.sleep(2)
        
        # Start new instance
        if self.auto_trading_enabled:
            self.start_auto_trading()
            self.logger.info("Auto trading restarted successfully")
            self.send_notification("🔄 Auto Trading Restarted", f"Auto trading has been restarted for {self.current_pair}")
        else:
            self.logger.info("Auto trading not restarted (disabled)")
    
    def _trading_loop(self):
        """Main trading loop"""
        heartbeat_interval = self.config.get('watchdog', {}).get('heartbeat_interval', 60)
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # Check if auto trading is still enabled
                if not self.auto_trading_enabled:
                    self.logger.info("Auto trading disabled, stopping loop")
                    break
                
                # Check trading hours
                if not self._is_trading_hours():
                    self.logger.debug("Outside trading hours, skipping execution")
                    time.sleep(heartbeat_interval)
                    continue
                
                # Execute trading logic
                self._execute_trading_cycle()
                
                # Heartbeat
                self.logger.debug(f"Trading cycle completed, waiting {heartbeat_interval}s")
                time.sleep(heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                self.send_notification("⚠️ Trading Error", f"Error in trading loop: {str(e)}")
                time.sleep(30)  # Wait before retry
    
    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours"""
        trading_hours = self.config.get('trading_hours', {})
        if not trading_hours.get('enabled', False):
            return True  # Always trade if hours not configured
        from datetime import datetime, time
        import pytz
        # Map common UTC offset to pytz
        tz_str = trading_hours.get('timezone', 'UTC')
        offset_map = {
            'UTC-5': 'Etc/GMT+5',
            'UTC+5': 'Etc/GMT-5',
            'UTC-6': 'Etc/GMT+6',
            'UTC-4': 'Etc/GMT+4',
            'UTC+8': 'Etc/GMT-8',
            # Add more as needed
        }
        tz_str = offset_map.get(tz_str, tz_str)
        try:
            tz = pytz.timezone(tz_str)
        except Exception as e:
            self.logger.warning(f"Unknown timezone '{tz_str}', defaulting to UTC. Error: {e}")
            tz = pytz.UTC
        now = datetime.now(tz)
        current_time = now.time()
        start_str = trading_hours.get('start', '00:00')
        end_str = trading_hours.get('end', '23:59')
        try:
            start_time = time.fromisoformat(start_str)
            end_time = time.fromisoformat(end_str)
            if start_time > end_time:
                return current_time >= start_time or current_time <= end_time
            else:
                return start_time <= current_time <= end_time
        except Exception as e:
            self.logger.error(f"Error parsing trading hours: {e}")
            return True  # Default to always trade
    
    def _execute_trading_cycle(self):
        """Execute one trading cycle"""
        try:
            # Get current market data
            df = self.strategies.get_market_data(self.current_pair, '1h', 100)
            if df.empty:
                self.logger.warning(f"No market data available for {self.current_pair}")
                return
            
            # Get user settings
            user_settings = self.db.get_user_settings(self.user_id) if self.user_id else {}
            strategy_type = user_settings.get('default_strategy', 'RSI_STRATEGY')
            
            # Execute strategy
            signal = self._execute_strategy(strategy_type, self.current_pair)
            
            if signal and signal.get('action'):
                self._execute_trade(signal)
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")
    
    def _execute_strategy(self, strategy_type: str, symbol: str):
        """Execute a specific trading strategy"""
        try:
            # Get balance for position sizing
            balance_response = self.api.get_balances()
            balance = 0
            if 'data' in balance_response:
                for asset in balance_response['data']:
                    if asset['asset'] == 'USDT':
                        balance = float(asset['total'])
                        break
            
            # Execute strategy based on type
            if strategy_type == 'RSI_STRATEGY':
                return self.strategies.rsi_strategy(symbol, balance)
            elif strategy_type == 'RSI_MULTI_TF':
                return self.strategies.rsi_multi_timeframe_strategy(symbol, balance)
            elif strategy_type == 'VOLUME_FILTER':
                return self.strategies.volume_filter_strategy(symbol, balance)
            elif strategy_type == 'ADVANCED_STRATEGY':
                return self.strategies.advanced_strategy(symbol, balance)
            elif strategy_type == 'GRID_TRADING':
                return self.strategies.grid_trading_strategy(symbol, balance)
            elif strategy_type == 'DCA':
                return self.strategies.dca_strategy(symbol, balance)
            else:
                self.logger.warning(f"Unknown strategy type: {strategy_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing strategy {strategy_type}: {e}")
            return None
    
    def _execute_trade(self, signal: dict):
        """Execute a trade based on signal"""
        try:
            action = signal.get('action')
            symbol = signal.get('symbol', self.current_pair)
            quantity = signal.get('quantity', 0)
            price = signal.get('price', 0)
            stop_loss = signal.get('stop_loss')
            take_profit = signal.get('take_profit')
            
            if not action or not quantity or not price:
                self.logger.warning(f"Invalid trade signal: {signal}")
                return
            
            # Place order
            order_response = self.api.place_order(
                symbol=symbol,
                side=action,
                order_type='MARKET',
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if 'error' in order_response:
                self.logger.error(f"Order failed: {order_response['error']}")
                self.send_notification("❌ Order Failed", f"Order failed: {order_response['error']}")
                return
            
            # Log successful trade
            self.logger.info(f"Trade executed: {action} {quantity} {symbol} @ {price}")
            self.send_notification(
                f"✅ Trade Executed",
                f"{action} {quantity:.8f} {symbol} @ ${price:.2f}"
            )
            
            # Add to trading history
            if self.user_id:
                self.db.add_trading_history(
                    user_id=self.user_id,
                    symbol=symbol,
                    side=action,
                    quantity=quantity,
                    price=price,
                    strategy=signal.get('strategy', 'Auto'),
                    status='FILLED'
                )
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            self.send_notification("❌ Trade Error", f"Error executing trade: {str(e)}")
    
    def send_notification(self, title: str, message: str):
        """Send notification via Telegram and/or email"""
        try:
            # Telegram notification
            if self.notification_settings.get('telegram', False) and self.user_id:
                # This would need to be implemented with the bot instance
                # For now, just log it
                self.logger.info(f"Telegram notification: {title} - {message}")
            
            # Email notification
            if self.notification_settings.get('email', False):
                self._send_email_notification(title, message)
                
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
    
    def _send_email_notification(self, title: str, message: str):
        """Send email notification"""
        try:
            email_address = self.notification_settings.get('email_address')
            if not email_address:
                return
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = "pionex-trading-bot@example.com"
            msg['To'] = email_address
            msg['Subject'] = f"Pionex Trading Bot - {title}"
            
            body = f"""
            {title}
            
            {message}
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Trading Pair: {self.current_pair}
            User ID: {self.user_id}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (you'd need to configure SMTP settings)
            # For now, just log it
            self.logger.info(f"Email notification: {title} - {message}")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
    
    def get_status(self) -> dict:
        """Get current bot status"""
        return {
            'is_running': self.is_running,
            'auto_trading_enabled': self.auto_trading_enabled,
            'current_pair': self.current_pair,
            'restart_count': self.restart_count,
            'last_restart': self.last_restart.isoformat() if self.last_restart else None,
            'trading_hours_active': self._is_trading_hours(),
            'user_id': self.user_id
        }
    
    def get_portfolio_snapshot(self) -> dict:
        """Get current portfolio snapshot"""
        try:
            balance_response = self.api.get_balances()
            positions_response = self.api.get_positions()
            
            portfolio = {
                'balance': balance_response.get('data', []),
                'positions': positions_response.get('data', []),
                'timestamp': datetime.now().isoformat(),
                'user_id': self.user_id
            }
            
            # Add to database
            if self.user_id:
                self.db.add_portfolio_snapshot(self.user_id, portfolio)
            
            return portfolio
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio snapshot: {e}")
            return {}

# Global auto trader instances
auto_traders = {}

def get_auto_trader(user_id: int) -> AutoTrader:
    """Get or create auto trader instance for user"""
    if user_id not in auto_traders:
        auto_traders[user_id] = AutoTrader(user_id)
    return auto_traders[user_id]

def start_auto_trading(user_id: int):
    """Start auto trading for a user"""
    trader = get_auto_trader(user_id)
    trader.enable_auto_trading(user_id)

def stop_auto_trading(user_id: int):
    """Stop auto trading for a user"""
    if user_id in auto_traders:
        trader = auto_traders[user_id]
        trader.disable_auto_trading(user_id)

def restart_auto_trading(user_id: int):
    """Restart auto trading for a user"""
    if user_id in auto_traders:
        trader = auto_traders[user_id]
        trader.restart_auto_trading(user_id)

def get_auto_trading_status(user_id: int) -> dict:
    """Get auto trading status for a user"""
    if user_id in auto_traders:
        return auto_traders[user_id].get_status()
    return {'is_running': False, 'auto_trading_enabled': False}

def add_strategy(user_id: int, symbol: str, strategy_type: str, parameters: dict = None):
    """Add a trading strategy for a user"""
    if user_id in auto_traders:
        trader = auto_traders[user_id]
        trader.db.add_active_strategy(user_id, symbol, strategy_type, parameters or {})

def remove_strategy(user_id: int, strategy_id: int):
    """Remove a trading strategy for a user"""
    if user_id in auto_traders:
        trader = auto_traders[user_id]
        trader.db.deactivate_strategy(strategy_id)

def get_portfolio_snapshot(user_id: int) -> dict:
    """Get portfolio snapshot for a user"""
    if user_id in auto_traders:
        return auto_traders[user_id].get_portfolio_snapshot()
    return {} 