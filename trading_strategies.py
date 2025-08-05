import pandas as pd
import numpy as np
import ta
from typing import Dict, List, Tuple
from pionex_api import PionexAPI
from config_loader import get_config
from indicators import bollinger_bands, on_balance_volume, support_resistance_levels, trendline_slope
import time

class TradingStrategies:
    def __init__(self, api: PionexAPI):
        self.api = api
    
    def calculate_rsi(self, prices: List[float], period: int = None) -> List[float]:
        """Calculate RSI and return the full list of values"""
        config = get_config()
        if period is None:
            period = config['rsi']['period']
        if len(prices) < period:
            return [50.0] * len(prices)
        df = pd.DataFrame({'close': prices})
        rsi = ta.momentum.RSIIndicator(df['close'], window=period)
        return rsi.rsi().tolist()
    
    def calculate_ema(self, data: List[float], period: int = None) -> List[float]:
        """Calculate EMA and return the full list of values"""
        config = get_config()
        if period is None:
            period = config['volume_filter']['ema_period']
        if len(data) < period:
            return data
        df = pd.DataFrame({'value': data})
        ema = ta.trend.EMAIndicator(df['value'], window=period)
        return ema.ema_indicator().tolist()
    
    def calculate_macd(self, prices: List[float], fast: int = None, slow: int = None, signal: int = None) -> Tuple[List[float], List[float], List[float]]:
        """Calculate MACD and return (macd_line, signal_line, histogram) as lists"""
        config = get_config()
        if fast is None:
            fast = config['macd']['fast']
        if slow is None:
            slow = config['macd']['slow']
        if signal is None:
            signal = config['macd']['signal']
        if len(prices) < slow:
            return ([0] * len(prices), [0] * len(prices), [0] * len(prices))
        df = pd.DataFrame({'close': prices})
        macd = ta.trend.MACD(df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
        return (
            macd.macd().tolist(),
            macd.macd_signal().tolist(),
            macd.macd_diff().tolist()
        )
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[List[float], List[float], List[float]]:
        """Calculate Bollinger Bands and return (upper, middle, lower) as lists"""
        if len(prices) < period:
            return ([prices[-1]] * len(prices), [prices[-1]] * len(prices), [prices[-1]] * len(prices))
        df = pd.DataFrame({'close': prices})
        bb = ta.volatility.BollingerBands(df['close'], window=period, window_dev=std_dev)
        return (
            bb.bollinger_hband().tolist(),
            bb.bollinger_mavg().tolist(),
            bb.bollinger_lband().tolist()
        )
    
    def analyze_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze candlestick patterns"""
        if df.empty or len(df) < 2:
            return {'pattern': 'none', 'signal': 'neutral'}
        
        # Get last two candles
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Engulfing patterns
        bullish_engulfing = (current['open'] < previous['close'] and 
                            current['close'] > previous['open'] and
                            current['close'] - current['open'] > previous['open'] - previous['close'])
        
        bearish_engulfing = (current['open'] > previous['close'] and 
                             current['close'] < previous['open'] and
                             current['open'] - current['close'] > previous['close'] - previous['open'])
        
        # Pin bar (hammer/shooting star)
        body_size = abs(current['close'] - current['open'])
        total_range = current['high'] - current['low']
        
        if total_range > 0:
            body_ratio = body_size / total_range
            
            # Hammer (bullish pin bar)
            hammer = (body_ratio < 0.3 and 
                     current['close'] > current['open'] and
                     (current['high'] - current['close']) < (current['open'] - current['low']) * 0.3)
            
            # Shooting star (bearish pin bar)
            shooting_star = (body_ratio < 0.3 and 
                           current['close'] < current['open'] and
                           (current['open'] - current['low']) < (current['high'] - current['close']) * 0.3)
        else:
            hammer = shooting_star = False
        
        # Determine pattern and signal
        if bullish_engulfing or hammer:
            pattern = 'bullish_engulfing' if bullish_engulfing else 'hammer'
            signal = 'bullish'
        elif bearish_engulfing or shooting_star:
            pattern = 'bearish_engulfing' if bearish_engulfing else 'shooting_star'
            signal = 'bearish'
        else:
            pattern = 'none'
            signal = 'neutral'
        
        return {'pattern': pattern, 'signal': signal}
    
    def get_market_data(self, symbol: str, interval: str = '1H', limit: int = 100) -> pd.DataFrame:
        """Get market data for analysis"""
        try:
            klines_response = self.api.get_klines(symbol, interval, limit)
            
            if 'error' in klines_response:
                self.logger.error(f"Error fetching klines for {symbol}: {klines_response['error']}")
                return pd.DataFrame()
            
            # Handle the new response format
            if 'data' in klines_response and isinstance(klines_response['data'], dict):
                klines_data = klines_response['data'].get('klines', [])
            elif 'data' in klines_response and isinstance(klines_response['data'], list):
                klines_data = klines_response['data']
            else:
                self.logger.error(f"Unexpected klines response format for {symbol}")
                return pd.DataFrame()
            
            if not klines_data:
                self.logger.warning(f"No klines data received for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(klines_data)
            
            # Rename columns to match expected format
            column_mapping = {
                'time': 'timestamp',
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            
            # Only keep columns that exist
            existing_columns = [col for col in column_mapping.keys() if col in df.columns]
            df = df[existing_columns]
            
            # Convert string values to float
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Convert timestamp to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error in get_market_data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_basic_market_data(self, symbol: str) -> Dict:
        """Get basic market data when klines are not available"""
        try:
            # Get current ticker data
            ticker_response = self.api.get_ticker_price(symbol)
            if 'error' in ticker_response:
                return {'error': ticker_response['error']}
            
            current_price = float(ticker_response['data']['price'])
            
            # Create basic market data structure
            market_data = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': int(time.time() * 1000),
                'data_available': True,
                'source': 'ticker'
            }
            
            return market_data
        except Exception as e:
            return {'error': f"Failed to get market data: {str(e)}"}

    def calculate_simple_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI with limited data points"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI if not enough data
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def rsi_multi_timeframe_strategy(self, symbol: str, balance: float, position_size: float = None) -> Dict:
        """RSI Multi-Timeframe Strategy"""
        config = get_config()
        try:
            # Get market data for both timeframes
            df_5m = self.get_market_data(symbol, '5m', 100)
            df_1h = self.get_market_data(symbol, '1h', 100)
            
            if df_5m.empty or df_1h.empty:
                return {"action": "HOLD", "reason": "No market data available"}
            
            # Calculate RSI for both timeframes
            rsi_5m_list = self.calculate_rsi(df_5m['close'].tolist(), config['rsi']['period'])
            rsi_1h_list = self.calculate_rsi(df_1h['close'].tolist(), config['rsi']['period'])
            rsi_5m = rsi_5m_list[-1] if rsi_5m_list else 50.0
            rsi_1h = rsi_1h_list[-1] if rsi_1h_list else 50.0
            
            # Get current price
            ticker = self.api.get_ticker_price(symbol)
            current_price = float(ticker.get('price', 0)) if 'price' in ticker else 0
            
            if current_price == 0:
                return {"action": "HOLD", "reason": "Unable to get current price"}
            
            # Calculate position size
            if position_size is None:
                position_size = config['position_size']
            position_value = balance * position_size
            quantity = position_value / current_price
            
            # RSI Multi-Timeframe Logic
            if rsi_5m < config['rsi']['oversold'] and rsi_1h < config['rsi']['overbought']:
                return {
                    "action": "BUY",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "rsi_5m": rsi_5m,
                    "rsi_1h": rsi_1h,
                    "reason": f"RSI Multi-TF: 5m({rsi_5m:.2f}) < 30, 1h({rsi_1h:.2f}) < 50"
                }
            elif rsi_5m > config['rsi']['overbought'] and rsi_1h > config['rsi']['overbought']:
                return {
                    "action": "SELL",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "rsi_5m": rsi_5m,
                    "rsi_1h": rsi_1h,
                    "reason": f"RSI Multi-TF: 5m({rsi_5m:.2f}) > 70, 1h({rsi_1h:.2f}) > 50"
                }
            else:
                return {
                    "action": "HOLD",
                    "rsi_5m": rsi_5m,
                    "rsi_1h": rsi_1h,
                    "reason": f"RSI Multi-TF: 5m({rsi_5m:.2f}), 1h({rsi_1h:.2f}) - No signal"
                }
                
        except Exception as e:
            return {"action": "HOLD", "reason": f"Multi-TF RSI error: {str(e)}"}
    
    def volume_filter_strategy(self, symbol: str, balance: float, position_size: float = None) -> Dict:
        """Volume Filter Strategy with EMA"""
        config = get_config()
        try:
            # Get market data
            df = self.get_market_data(symbol, '1h', 100)
            if df.empty:
                return {"action": "HOLD", "reason": "No market data available"}
            
            # Calculate volume EMA
            period = config['volume_filter']['ema_period']
            volume_ema_list = self.calculate_ema(df['volume'].tolist(), period)
            volume_ema = volume_ema_list[-1] if volume_ema_list else 0
            current_volume = df['volume'].iloc[-1]
            
            # Volume filter condition
            if position_size is None:
                position_size = config['position_size']
            volume_filter = current_volume > (volume_ema * config['volume_filter']['multiplier'])
            
            # Get current price
            ticker = self.api.get_ticker_price(symbol)
            current_price = float(ticker.get('price', 0)) if 'price' in ticker else 0
            
            if current_price == 0:
                return {"action": "HOLD", "reason": "Unable to get current price"}
            
            # Calculate RSI
            rsi_list = self.calculate_rsi(df['close'].tolist(), config['rsi']['period'])
            rsi = rsi_list[-1] if rsi_list else 50.0
            
            # Calculate position size
            if position_size is None:
                position_size = config['position_size']
            position_value = balance * position_size
            quantity = position_value / current_price
            
            # Strategy logic with volume filter
            if rsi < config['rsi']['oversold'] and volume_filter:
                return {
                    "action": "BUY",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "rsi": rsi,
                    "volume_ema": volume_ema,
                    "current_volume": current_volume,
                    "reason": f"Volume Filter: RSI({rsi:.2f}) < 30, Volume > {config['volume_filter']['multiplier']}x EMA"
                }
            elif rsi > config['rsi']['overbought'] and volume_filter:
                return {
                    "action": "SELL",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "rsi": rsi,
                    "volume_ema": volume_ema,
                    "current_volume": current_volume,
                    "reason": f"Volume Filter: RSI({rsi:.2f}) > 70, Volume > {config['volume_filter']['multiplier']}x EMA"
                }
            else:
                return {
                    "action": "HOLD",
                    "rsi": rsi,
                    "volume_ema": volume_ema,
                    "current_volume": current_volume,
                    "reason": f"Volume Filter: RSI({rsi:.2f}), Volume filter: {volume_filter}"
                }
                
        except Exception as e:
            return {"action": "HOLD", "reason": f"Volume Filter error: {str(e)}"}
    
    def advanced_strategy(self, symbol: str, balance: float, position_size: float = None) -> Dict:
        """Advanced Strategy combining RSI, MACD, Volume, Candlestick, BB, OBV, S/R"""
        config = get_config()
        try:
            # Get market data
            df = self.get_market_data(symbol, '1h', 100)
            if df.empty:
                return {"action": "HOLD", "reason": "No market data available"}
            
            # Calculate all indicators
            rsi_list = self.calculate_rsi(df['close'].tolist(), config['rsi']['period'])
            rsi = rsi_list[-1] if rsi_list else 50.0
            macd_line, signal_line, histogram = self.calculate_macd(df['close'].tolist(), config['macd']['fast'], config['macd']['slow'], config['macd']['signal'])
            volume_ema_list = self.calculate_ema(df['volume'].tolist(), config['volume_filter']['ema_period'])
            volume_ema = volume_ema_list[-1] if volume_ema_list else 0
            current_volume = df['volume'].iloc[-1]
            candlestick = self.analyze_candlestick_patterns(df)
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(df['close'].tolist(), config['bollinger_bands']['window'], config['bollinger_bands']['n_std'])
            obv = on_balance_volume(df['close'].tolist(), df['volume'].tolist())
            sr = support_resistance_levels(df['close'].tolist(), config['support_resistance']['window'])
            trend_slope = trendline_slope(df['close'].tolist(), config['support_resistance']['window'])
            
            # Get current price
            ticker = self.api.get_ticker_price(symbol)
            current_price = float(ticker.get('price', 0)) if 'price' in ticker else 0
            
            if current_price == 0:
                return {"action": "HOLD", "reason": "Unable to get current price"}
            
            # Calculate position size
            if position_size is None:
                position_size = config['position_size']
            position_value = balance * position_size
            quantity = position_value / current_price
            
            # Volume filter
            volume_filter = current_volume > (volume_ema * config['volume_filter']['multiplier'])
            
            # MACD crossover analysis
            current_macd = macd_line[-1] if macd_line else 0
            current_signal = signal_line[-1] if signal_line else 0
            prev_macd = macd_line[-2] if len(macd_line) > 1 else 0
            prev_signal = signal_line[-2] if len(signal_line) > 1 else 0
            
            macd_crossover = "neutral"
            if current_macd > current_signal and prev_macd <= prev_signal:
                macd_crossover = "bullish"
            elif current_macd < current_signal and prev_macd >= prev_signal:
                macd_crossover = "bearish"
            
            # Bollinger Band squeeze/breakout
            current_bb_upper = bb_upper[-1] if bb_upper else current_price
            current_bb_lower = bb_lower[-1] if bb_lower else current_price
            current_bb_middle = bb_middle[-1] if bb_middle else current_price
            
            bb_bandwidth = (current_bb_upper - current_bb_lower) / current_bb_middle if current_bb_middle else 0
            bb_squeeze = bb_bandwidth < 0.02
            bb_breakout = current_price > current_bb_upper or current_price < current_bb_lower
            
            # OBV trend (simple: positive slope = bullish, negative = bearish)
            obv_trend = trendline_slope(list(pd.Series(df['close']).rolling(config['support_resistance']['window']).apply(lambda x: on_balance_volume(x.tolist(), df['volume'][-config['support_resistance']['window']:].tolist()) if len(x) == config['support_resistance']['window'] else 0)), config['support_resistance']['window'])
            
            # Support/Resistance proximity
            near_support = sr['support'] is not None and abs(current_price - sr['support']) / current_price < 0.01
            near_resistance = sr['resistance'] is not None and abs(current_price - sr['resistance']) / current_price < 0.01
            
            # Trend direction
            trend_up = trend_slope > 0
            trend_down = trend_slope < 0
            
            # Advanced strategy logic
            bullish_conditions = (
                rsi < config['rsi']['oversold'] and
                macd_crossover in ['bullish', 'neutral'] and
                volume_filter and
                candlestick['signal'] in ['bullish', 'neutral'] and
                (bb_breakout or bb_squeeze) and
                obv_trend > 0 and
                near_support and
                trend_up
            )
            bearish_conditions = (
                rsi > config['rsi']['overbought'] and
                macd_crossover in ['bearish', 'neutral'] and
                volume_filter and
                candlestick['signal'] in ['bearish', 'neutral'] and
                (bb_breakout or bb_squeeze) and
                obv_trend < 0 and
                near_resistance and
                trend_down
            )
            
            if bullish_conditions:
                return {
                    "action": "BUY",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "rsi": rsi,
                    "macd_crossover": macd_crossover,
                    "volume_ratio": current_volume / volume_ema,
                    "candlestick_pattern": candlestick['pattern'],
                    "bb_bandwidth": bb_bandwidth,
                    "obv": obv,
                    "support": sr['support'],
                    "resistance": sr['resistance'],
                    "trend_slope": trend_slope,
                    "stop_loss": current_price * (1 - config['stop_loss_percentage'] / 100),
                    "take_profit": current_price * (1 + config['take_profit_percentage'] / 100),
                    "reason": f"Advanced: RSI({rsi:.2f}), MACD({macd_crossover}), Volume({current_volume/volume_ema:.2f}x), BB({bb_bandwidth:.4f}), OBV({obv}), S/R({sr['support']}/{sr['resistance']}), Trend({trend_slope})"
                }
            elif bearish_conditions:
                return {
                    "action": "SELL",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "rsi": rsi,
                    "macd_crossover": macd_crossover,
                    "volume_ratio": current_volume / volume_ema,
                    "candlestick_pattern": candlestick['pattern'],
                    "bb_bandwidth": bb_bandwidth,
                    "obv": obv,
                    "support": sr['support'],
                    "resistance": sr['resistance'],
                    "trend_slope": trend_slope,
                    "stop_loss": current_price * (1 + config['stop_loss_percentage'] / 100),
                    "take_profit": current_price * (1 - config['take_profit_percentage'] / 100),
                    "reason": f"Advanced: RSI({rsi:.2f}), MACD({macd_crossover}), Volume({current_volume/volume_ema:.2f}x), BB({bb_bandwidth:.4f}), OBV({obv}), S/R({sr['support']}/{sr['resistance']}), Trend({trend_slope})"
                }
            else:
                return {
                    "action": "HOLD",
                    "rsi": rsi,
                    "macd_crossover": macd_crossover,
                    "volume_ratio": current_volume / volume_ema,
                    "candlestick_pattern": candlestick['pattern'],
                    "bb_bandwidth": bb_bandwidth,
                    "obv": obv,
                    "support": sr['support'],
                    "resistance": sr['resistance'],
                    "trend_slope": trend_slope,
                    "reason": f"Advanced: RSI({rsi:.2f}), MACD({macd_crossover}), Volume({current_volume/volume_ema:.2f}x), BB({bb_bandwidth:.4f}), OBV({obv}), S/R({sr['support']}/{sr['resistance']}), Trend({trend_slope}) - No signal"
                }
                
        except Exception as e:
            return {"action": "HOLD", "reason": f"Advanced strategy error: {str(e)}"}
    
    def rsi_strategy(self, symbol: str, balance: float, position_size: float = None) -> Dict:
        """RSI-based trading strategy"""
        config = get_config()
        try:
            # Get market data
            df = self.get_market_data(symbol, '1h', 100)
            if df.empty:
                return {"action": "HOLD", "reason": "No market data available"}
            
            # Calculate RSI
            rsi_list = self.calculate_rsi(df['close'].tolist(), config['rsi']['period'])
            rsi = rsi_list[-1] if rsi_list else 50.0
            
            # Get current price
            ticker = self.api.get_ticker_price(symbol)
            current_price = float(ticker.get('price', 0)) if 'price' in ticker else 0
            
            if current_price == 0:
                return {"action": "HOLD", "reason": "Unable to get current price"}
            
            # Calculate position size in USDT
            if position_size is None:
                position_size = config['position_size']
            position_value = balance * position_size
            quantity = position_value / current_price
            
            # RSI Strategy Logic
            if rsi < config['rsi']['oversold']:
                return {
                    "action": "BUY",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "rsi": rsi,
                    "stop_loss": current_price * (1 - config['stop_loss_percentage'] / 100),  # -1.5%
                    "take_profit": current_price * (1 + config['take_profit_percentage'] / 100),  # +2.5%
                    "reason": f"RSI oversold ({rsi:.2f})"
                }
            elif rsi > config['rsi']['overbought']:
                return {
                    "action": "SELL",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "rsi": rsi,
                    "stop_loss": current_price * (1 + config['stop_loss_percentage'] / 100),  # +1.5%
                    "take_profit": current_price * (1 - config['take_profit_percentage'] / 100),  # -2.5%
                    "reason": f"RSI overbought ({rsi:.2f})"
                }
            else:
                return {
                    "action": "HOLD",
                    "rsi": rsi,
                    "reason": f"RSI neutral ({rsi:.2f})"
                }
                
        except Exception as e:
            return {"action": "HOLD", "reason": f"Strategy error: {str(e)}"}
    
    def grid_trading_strategy(self, symbol: str, balance: float, grid_levels: int = None) -> Dict:
        """Grid trading strategy"""
        config = get_config()
        try:
            ticker = self.api.get_ticker_price(symbol)
            current_price = float(ticker.get('price', 0)) if 'price' in ticker else 0
            
            if current_price == 0:
                return {"action": "HOLD", "reason": "Unable to get current price"}
            
            # Calculate grid levels
            if grid_levels is None:
                grid_levels = config['grid_trading']['levels']
            grid_spacing = config['grid_trading']['spacing']
            grid_prices = []
            
            for i in range(grid_levels):
                price = current_price * (1 + (i - grid_levels//2) * grid_spacing)
                grid_prices.append(price)
            
            # Find closest grid level
            closest_grid = min(grid_prices, key=lambda x: abs(x - current_price))
            
            if current_price < closest_grid:
                return {
                    "action": "BUY",
                    "symbol": symbol,
                    "quantity": (balance * config['grid_trading']['position_size']) / current_price,
                    "price": current_price,
                    "stop_loss": current_price * (1 - config['stop_loss_percentage'] / 100),
                    "take_profit": current_price * (1 + config['take_profit_percentage'] / 100),
                    "reason": f"Grid buy at {current_price:.2f}"
                }
            elif current_price > closest_grid:
                return {
                    "action": "SELL",
                    "symbol": symbol,
                    "quantity": (balance * config['grid_trading']['position_size']) / current_price,
                    "price": current_price,
                    "stop_loss": current_price * (1 + config['stop_loss_percentage'] / 100),
                    "take_profit": current_price * (1 - config['take_profit_percentage'] / 100),
                    "reason": f"Grid sell at {current_price:.2f}"
                }
            else:
                return {
                    "action": "HOLD",
                    "reason": f"At grid level {closest_grid:.2f}"
                }
                
        except Exception as e:
            return {"action": "HOLD", "reason": f"Grid strategy error: {str(e)}"}
    
    def dca_strategy(self, symbol: str, balance: float, dca_amount: float = None) -> Dict:
        """Dollar Cost Averaging strategy"""
        config = get_config()
        try:
            ticker = self.api.get_ticker_price(symbol)
            current_price = float(ticker.get('price', 0)) if 'price' in ticker else 0
            
            if current_price == 0:
                return {"action": "HOLD", "reason": "Unable to get current price"}
            
            # Simple DCA - buy fixed amount
            if dca_amount is None:
                dca_amount = config['dca_strategy']['amount']
            quantity = dca_amount / current_price
            
            return {
                "action": "BUY",
                "symbol": symbol,
                "quantity": quantity,
                "price": current_price,
                "stop_loss": current_price * (1 - config['stop_loss_percentage'] / 100),
                "take_profit": current_price * (1 + config['take_profit_percentage'] / 100),
                "reason": f"DCA buy ${dca_amount}"
            }
            
        except Exception as e:
            return {"action": "HOLD", "reason": f"DCA strategy error: {str(e)}"}
    
    def get_strategy_signal(self, strategy: str, symbol: str, balance: float, **kwargs) -> Dict:
        """Get trading signal based on selected strategy"""
        config = get_config()
        if strategy == "RSI_STRATEGY":
            return self.rsi_strategy(symbol, balance, config['position_size'])
        elif strategy == "RSI_MULTI_TF":
            return self.rsi_multi_timeframe_strategy(symbol, balance, config['position_size'])
        elif strategy == "VOLUME_FILTER":
            return self.volume_filter_strategy(symbol, balance, config['position_size'])
        elif strategy == "ADVANCED_STRATEGY":
            return self.advanced_strategy(symbol, balance, config['position_size'])
        elif strategy == "GRID_TRADING":
            return self.grid_trading_strategy(symbol, balance, config['grid_trading']['levels'])
        elif strategy == "DCA":
            return self.dca_strategy(symbol, balance, config['dca_strategy']['amount'])
        else:
            return {"action": "HOLD", "reason": "Unknown strategy"}
    
    def calculate_portfolio_metrics(self, positions: List[Dict]) -> Dict:
        """Calculate portfolio performance metrics"""
        if not positions:
            return {"total_value": 0, "total_pnl": 0, "win_rate": 0}
        
        total_value = 0
        total_pnl = 0
        winning_positions = 0
        
        for position in positions:
            if 'unrealizedPnl' in position:
                pnl = float(position['unrealizedPnl'])
                total_pnl += pnl
                if pnl > 0:
                    winning_positions += 1
            
            if 'positionValue' in position:
                total_value += float(position['positionValue'])
        
        win_rate = (winning_positions / len(positions)) * 100 if positions else 0
        
        return {
            "total_value": total_value,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "position_count": len(positions)
        }
    
    def calculate_trailing_stop(self, entry_price: float, current_price: float, 
                               trailing_percentage: float = None) -> float:
        """Calculate trailing stop loss"""
        config = get_config()
        if trailing_percentage is None:
            trailing_percentage = config['trailing_stop']['percentage']
        if current_price > entry_price:
            # For long positions, trailing stop moves up
            return max(entry_price * (1 - trailing_percentage / 100), 
                      current_price * (1 - trailing_percentage / 100))
        else:
            # For short positions, trailing stop moves down
            return min(entry_price * (1 + trailing_percentage / 100), 
                      current_price * (1 + trailing_percentage / 100))
    
    def should_update_trailing_stop(self, entry_price: float, current_price: float, 
                                   current_stop: float, trailing_percentage: float = None) -> Tuple[bool, float]:
        """Check if trailing stop should be updated"""
        config = get_config()
        if trailing_percentage is None:
            trailing_percentage = config['trailing_stop']['percentage']
        new_stop = self.calculate_trailing_stop(entry_price, current_price, trailing_percentage)
        
        if current_price > entry_price:
            # For long positions, update if new stop is higher
            should_update = new_stop > current_stop
        else:
            # For short positions, update if new stop is lower
            should_update = new_stop < current_stop
        
        return should_update, new_stop 