import logging
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path

from config_loader import get_config
from pionex_api import PionexAPI
from database import Database

class FuturesTrading:
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.api = PionexAPI()
        self.db = Database()
        self.config = get_config()
        self.logger = self._setup_logging()
        
        # Futures configuration
        self.futures_config = self.config.get('futures', {})
        self.grid_config = self.futures_config.get('grid', {})
        self.hedging_config = self.futures_config.get('hedging', {})
        
        # Active strategies tracking
        self.active_grids = {}
        self.active_hedging = {}
        self.liquidation_warnings = {}
        
    def _setup_logging(self):
        """Setup futures trading logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        instance_id = f"user_{self.user_id}" if self.user_id else "global"
        logger = logging.getLogger(f"FuturesTrading_{instance_id}")
        logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_dir / f"futures_trading_{instance_id}.log")
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
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def create_futures_grid(self, symbol: str, grid_type: str, upper_price: float, 
                           lower_price: float, grid_number: int, investment: float,
                           leverage: int = 10, margin_type: str = "ISOLATED") -> Dict:
        """Create a futures grid trading strategy"""
        try:
            # Validate parameters
            if grid_number < 2 or grid_number > self.grid_config.get('max_grids', 100):
                return {'error': f"Grid number must be between 2 and {self.grid_config.get('max_grids', 100)}"}
            
            if investment < self.grid_config.get('min_investment', 10.0):
                return {'error': f"Investment must be at least ${self.grid_config.get('min_investment', 10.0)}"}
            
            if investment > self.grid_config.get('max_investment', 10000.0):
                return {'error': f"Investment must be less than ${self.grid_config.get('max_investment', 10000.0)}"}
            
            # Calculate grid parameters
            grid_spacing = (upper_price - lower_price) / (grid_number - 1)
            investment_per_grid = investment / grid_number
            
            # Set leverage and margin type
            self.api.set_leverage(symbol, leverage)
            self.api.set_margin_type(symbol, margin_type)
            
            # Create grid orders
            grid_orders = []
            for i in range(grid_number):
                price = lower_price + (i * grid_spacing)
                quantity = investment_per_grid / price
                
                # Place buy order at this grid level
                buy_order = self.api.place_order(
                    symbol=symbol,
                    side='BUY',
                    order_type='LIMIT',
                    quantity=quantity,
                    price=price,
                    leverage=leverage,
                    margin_type=margin_type
                )
                
                if 'error' not in buy_order:
                    grid_orders.append({
                        'order_id': buy_order.get('orderId'),
                        'price': price,
                        'quantity': quantity,
                        'side': 'BUY',
                        'grid_level': i
                    })
            
            # Store grid strategy
            grid_strategy = {
                'symbol': symbol,
                'grid_type': grid_type,
                'upper_price': upper_price,
                'lower_price': lower_price,
                'grid_number': grid_number,
                'investment': investment,
                'leverage': leverage,
                'margin_type': margin_type,
                'orders': grid_orders,
                'created_at': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
            
            # Store in database
            if self.user_id:
                self.db.add_active_strategy(
                    self.user_id, symbol, 'FUTURES_GRID', grid_strategy
                )
            
            self.active_grids[f"{symbol}_{grid_type}"] = grid_strategy
            self.logger.info(f"Created futures grid for {symbol}: {grid_number} grids, ${investment} investment")
            
            return {
                'success': True,
                'grid_id': f"{symbol}_{grid_type}",
                'orders_placed': len(grid_orders),
                'strategy': grid_strategy
            }
            
        except Exception as e:
            self.logger.error(f"Error creating futures grid: {e}")
            return {'error': str(e)}
    
    def create_hedging_grid(self, symbol: str, upper_price: float, lower_price: float,
                           grid_number: int, investment: float, hedge_ratio: float = 0.5) -> Dict:
        """Create a hedging grid strategy"""
        try:
            # Validate parameters
            if not self.hedging_config.get('enabled', False):
                return {'error': 'Hedging is disabled in configuration'}
            
            max_positions = self.hedging_config.get('max_positions', 5)
            if grid_number > max_positions:
                return {'error': f"Grid number exceeds max positions: {max_positions}"}
            
            # Calculate grid parameters
            grid_spacing = (upper_price - lower_price) / (grid_number - 1)
            long_investment = investment * hedge_ratio
            short_investment = investment * (1 - hedge_ratio)
            
            # Create long and short grids
            long_orders = []
            short_orders = []
            
            for i in range(grid_number):
                price = lower_price + (i * grid_spacing)
                
                # Long position
                long_quantity = (long_investment / grid_number) / price
                long_order = self.api.place_order(
                    symbol=symbol,
                    side='BUY',
                    order_type='LIMIT',
                    quantity=long_quantity,
                    price=price
                )
                
                if 'error' not in long_order:
                    long_orders.append({
                        'order_id': long_order.get('orderId'),
                        'price': price,
                        'quantity': long_quantity,
                        'side': 'BUY',
                        'grid_level': i
                    })
                
                # Short position (hedge)
                short_quantity = (short_investment / grid_number) / price
                short_order = self.api.place_order(
                    symbol=symbol,
                    side='SELL',
                    order_type='LIMIT',
                    quantity=short_quantity,
                    price=price
                )
                
                if 'error' not in short_order:
                    short_orders.append({
                        'order_id': short_order.get('orderId'),
                        'price': price,
                        'quantity': short_quantity,
                        'side': 'SELL',
                        'grid_level': i
                    })
            
            # Store hedging strategy
            hedging_strategy = {
                'symbol': symbol,
                'upper_price': upper_price,
                'lower_price': lower_price,
                'grid_number': grid_number,
                'investment': investment,
                'hedge_ratio': hedge_ratio,
                'long_orders': long_orders,
                'short_orders': short_orders,
                'created_at': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
            
            # Store in database
            if self.user_id:
                self.db.add_active_strategy(
                    self.user_id, symbol, 'HEDGING_GRID', hedging_strategy
                )
            
            self.active_hedging[f"{symbol}_hedge"] = hedging_strategy
            self.logger.info(f"Created hedging grid for {symbol}: {grid_number} grids, ${investment} investment")
            
            return {
                'success': True,
                'hedge_id': f"{symbol}_hedge",
                'long_orders': len(long_orders),
                'short_orders': len(short_orders),
                'strategy': hedging_strategy
            }
            
        except Exception as e:
            self.logger.error(f"Error creating hedging grid: {e}")
            return {'error': str(e)}
    
    def get_dynamic_limits(self) -> Dict:
        """Get dynamic limits based on account balance"""
        try:
            # Get account balance
            balance_response = self.api.get_balances()
            if 'error' in balance_response:
                return {'error': balance_response['error']}
            
            # Calculate total balance
            total_balance = 0
            for asset in balance_response.get('data', []):
                if asset['asset'] == 'USDT':
                    total_balance = float(asset['total'])
                    break
            
            # Get account limits
            limits_response = self.api.get_dynamic_limits()
            if 'error' in limits_response:
                return {'error': limits_response['error']}
            
            # Calculate dynamic limits
            max_positions = min(
                self.hedging_config.get('max_positions', 5),
                int(total_balance / 100)  # 1 position per $100
            )
            
            max_investment = min(
                total_balance * 0.8,  # 80% of balance
                self.grid_config.get('max_investment', 10000.0)
            )
            
            max_grids = min(
                self.grid_config.get('max_grids', 100),
                int(total_balance / 50)  # 1 grid per $50
            )
            
            return {
                'total_balance': total_balance,
                'max_positions': max_positions,
                'max_investment': max_investment,
                'max_grids': max_grids,
                'limits': limits_response.get('data', {})
            }
            
        except Exception as e:
            self.logger.error(f"Error getting dynamic limits: {e}")
            return {'error': str(e)}
    
    def check_liquidation_risk(self, symbol: str) -> Dict:
        """Check liquidation risk for a symbol"""
        try:
            # Get positions
            positions_response = self.api.get_positions()
            if 'error' in positions_response:
                return {'error': positions_response['error']}
            
            # Get liquidation warnings
            liquidation_response = self.api.get_liquidation_warning()
            if 'error' in liquidation_response:
                return {'error': liquidation_response['error']}
            
            # Get mark price
            mark_price_response = self.api.get_mark_price(symbol)
            if 'error' in mark_price_response:
                return {'error': mark_price_response['error']}
            
            mark_price = float(mark_price_response.get('markPrice', 0))
            
            # Calculate risk for each position
            risk_positions = []
            total_risk = 0
            
            for position in positions_response.get('data', []):
                if position['symbol'] == symbol and float(position.get('positionAmt', 0)) != 0:
                    position_amt = float(position['positionAmt'])
                    entry_price = float(position['entryPrice'])
                    unrealized_pnl = float(position.get('unrealizedPnl', 0))
                    margin_type = position.get('marginType', 'ISOLATED')
                    leverage = int(position.get('leverage', 1))
                    
                    # Calculate liquidation price
                    if margin_type == 'ISOLATED':
                        # Simplified liquidation calculation
                        liquidation_price = entry_price * (1 - 1/leverage)
                    else:
                        # Cross margin calculation
                        liquidation_price = entry_price * 0.8  # Approximate
                    
                    # Calculate distance to liquidation
                    if position_amt > 0:  # Long position
                        distance_to_liquidation = (mark_price - liquidation_price) / mark_price * 100
                    else:  # Short position
                        distance_to_liquidation = (liquidation_price - mark_price) / mark_price * 100
                    
                    risk_level = 'LOW'
                    if distance_to_liquidation < 5:
                        risk_level = 'CRITICAL'
                    elif distance_to_liquidation < 10:
                        risk_level = 'HIGH'
                    elif distance_to_liquidation < 20:
                        risk_level = 'MEDIUM'
                    
                    risk_positions.append({
                        'symbol': symbol,
                        'position_amt': position_amt,
                        'entry_price': entry_price,
                        'mark_price': mark_price,
                        'liquidation_price': liquidation_price,
                        'distance_to_liquidation': distance_to_liquidation,
                        'risk_level': risk_level,
                        'unrealized_pnl': unrealized_pnl,
                        'leverage': leverage,
                        'margin_type': margin_type
                    })
                    
                    total_risk += abs(unrealized_pnl)
            
            # Store liquidation warnings
            if risk_positions:
                self.liquidation_warnings[symbol] = {
                    'positions': risk_positions,
                    'total_risk': total_risk,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Send warnings for critical positions
                for position in risk_positions:
                    if position['risk_level'] == 'CRITICAL':
                        self._send_liquidation_warning(symbol, position)
            
            return {
                'symbol': symbol,
                'mark_price': mark_price,
                'risk_positions': risk_positions,
                'total_risk': total_risk,
                'warnings': liquidation_response.get('data', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error checking liquidation risk: {e}")
            return {'error': str(e)}
    
    def _send_liquidation_warning(self, symbol: str, position: Dict):
        """Send liquidation warning notification"""
        warning_msg = f"⚠️ LIQUIDATION WARNING - {symbol}\n"
        warning_msg += f"Position: {position['position_amt']:.8f}\n"
        warning_msg += f"Entry Price: ${position['entry_price']:.2f}\n"
        warning_msg += f"Mark Price: ${position['mark_price']:.2f}\n"
        warning_msg += f"Liquidation Price: ${position['liquidation_price']:.2f}\n"
        warning_msg += f"Distance to Liquidation: {position['distance_to_liquidation']:.2f}%\n"
        warning_msg += f"Risk Level: {position['risk_level']}\n"
        warning_msg += f"Unrealized PnL: ${position['unrealized_pnl']:.2f}"
        
        self.logger.warning(warning_msg)
        
        # Send notification if configured
        if self.config.get('notifications', {}).get('telegram', False):
            # This would be integrated with the bot notification system
            pass
    
    def manage_grid_strategy(self, grid_id: str) -> Dict:
        """Manage an active grid strategy"""
        try:
            if grid_id not in self.active_grids:
                return {'error': 'Grid strategy not found'}
            
            grid_strategy = self.active_grids[grid_id]
            symbol = grid_strategy['symbol']
            
            # Get current market price
            ticker_response = self.api.get_ticker_price(symbol)
            if 'error' in ticker_response:
                return {'error': ticker_response['error']}
            
            current_price = float(ticker_response.get('price', 0))
            
            # Check which orders should be executed
            executed_orders = []
            for order in grid_strategy['orders']:
                order_price = order['price']
                
                if order['side'] == 'BUY' and current_price <= order_price:
                    # Execute buy order
                    executed_orders.append(order)
                elif order['side'] == 'SELL' and current_price >= order_price:
                    # Execute sell order
                    executed_orders.append(order)
            
            # Update strategy status
            if executed_orders:
                grid_strategy['last_execution'] = datetime.now().isoformat()
                grid_strategy['executed_orders'] = executed_orders
                
                self.logger.info(f"Executed {len(executed_orders)} orders for grid {grid_id}")
            
            return {
                'grid_id': grid_id,
                'current_price': current_price,
                'executed_orders': len(executed_orders),
                'total_orders': len(grid_strategy['orders']),
                'status': grid_strategy['status']
            }
            
        except Exception as e:
            self.logger.error(f"Error managing grid strategy: {e}")
            return {'error': str(e)}
    
    def close_grid_strategy(self, grid_id: str) -> Dict:
        """Close a grid strategy and cancel all orders"""
        try:
            if grid_id not in self.active_grids:
                return {'error': 'Grid strategy not found'}
            
            grid_strategy = self.active_grids[grid_id]
            symbol = grid_strategy['symbol']
            
            # Cancel all open orders
            cancelled_orders = []
            for order in grid_strategy['orders']:
                if order.get('order_id'):
                    cancel_response = self.api.cancel_order(symbol, order['order_id'])
                    if 'error' not in cancel_response:
                        cancelled_orders.append(order['order_id'])
            
            # Update strategy status
            grid_strategy['status'] = 'CLOSED'
            grid_strategy['closed_at'] = datetime.now().isoformat()
            grid_strategy['cancelled_orders'] = cancelled_orders
            
            # Remove from active grids
            del self.active_grids[grid_id]
            
            # Update database
            if self.user_id:
                self.db.deactivate_strategy(grid_id)
            
            self.logger.info(f"Closed grid strategy {grid_id}, cancelled {len(cancelled_orders)} orders")
            
            return {
                'grid_id': grid_id,
                'cancelled_orders': len(cancelled_orders),
                'status': 'CLOSED'
            }
            
        except Exception as e:
            self.logger.error(f"Error closing grid strategy: {e}")
            return {'error': str(e)}
    
    def get_strategy_status(self) -> Dict:
        """Get status of all active strategies"""
        return {
            'active_grids': len(self.active_grids),
            'active_hedging': len(self.active_hedging),
            'liquidation_warnings': len(self.liquidation_warnings),
            'grids': list(self.active_grids.keys()),
            'hedging': list(self.active_hedging.keys()),
            'warnings': list(self.liquidation_warnings.keys())
        }
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics for all strategies"""
        try:
            total_pnl = 0
            total_positions = 0
            strategy_metrics = {}
            
            # Calculate metrics for each active strategy
            for grid_id, strategy in self.active_grids.items():
                symbol = strategy['symbol']
                positions_response = self.api.get_positions()
                
                if 'data' in positions_response:
                    for position in positions_response['data']:
                        if position['symbol'] == symbol:
                            pnl = float(position.get('unrealizedPnl', 0))
                            total_pnl += pnl
                            total_positions += 1
                            
                            strategy_metrics[grid_id] = {
                                'symbol': symbol,
                                'pnl': pnl,
                                'position_amt': float(position.get('positionAmt', 0)),
                                'entry_price': float(position.get('entryPrice', 0)),
                                'mark_price': float(position.get('markPrice', 0))
                            }
            
            return {
                'total_pnl': total_pnl,
                'total_positions': total_positions,
                'strategy_metrics': strategy_metrics,
                'active_strategies': len(self.active_grids) + len(self.active_hedging)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}

# Global futures trading instances
futures_traders = {}

def get_futures_trader(user_id: int) -> FuturesTrading:
    """Get or create futures trader instance for user"""
    if user_id not in futures_traders:
        futures_traders[user_id] = FuturesTrading(user_id)
    return futures_traders[user_id]

def create_futures_grid(user_id: int, symbol: str, grid_type: str, upper_price: float,
                       lower_price: float, grid_number: int, investment: float,
                       leverage: int = 10, margin_type: str = "ISOLATED") -> Dict:
    """Create a futures grid strategy for a user"""
    trader = get_futures_trader(user_id)
    return trader.create_futures_grid(symbol, grid_type, upper_price, lower_price,
                                    grid_number, investment, leverage, margin_type)

def create_hedging_grid(user_id: int, symbol: str, upper_price: float, lower_price: float,
                       grid_number: int, investment: float, hedge_ratio: float = 0.5) -> Dict:
    """Create a hedging grid strategy for a user"""
    trader = get_futures_trader(user_id)
    return trader.create_hedging_grid(symbol, upper_price, lower_price, grid_number,
                                    investment, hedge_ratio)

def get_dynamic_limits(user_id: int) -> Dict:
    """Get dynamic limits for a user"""
    trader = get_futures_trader(user_id)
    return trader.get_dynamic_limits()

def check_liquidation_risk(user_id: int, symbol: str) -> Dict:
    """Check liquidation risk for a user"""
    trader = get_futures_trader(user_id)
    return trader.check_liquidation_risk(symbol)

def get_strategy_status(user_id: int) -> Dict:
    """Get strategy status for a user"""
    trader = get_futures_trader(user_id)
    return trader.get_strategy_status()

def get_performance_metrics(user_id: int) -> Dict:
    """Get performance metrics for a user"""
    trader = get_futures_trader(user_id)
    return trader.get_performance_metrics() 