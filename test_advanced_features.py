#!/usr/bin/env python3
"""
Advanced Features Test Script for Pionex Trading Bot
Tests all new advanced trading features
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from pionex_api import PionexAPI
from trading_strategies import TradingStrategies
from database import Database
from config import SUPPORTED_PAIRS, STRATEGY_TYPES

def test_rsi_multi_timeframe():
    """Test RSI Multi-Timeframe Strategy"""
    print("📊 Testing RSI Multi-Timeframe Strategy...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        symbol = "BTCUSDT"
        balance = 1000
        
        signal = strategies.rsi_multi_timeframe_strategy(symbol, balance)
        print(f"📊 Signal: {signal['action']}")
        print(f"📝 Reason: {signal['reason']}")
        
        if 'rsi_5m' in signal and 'rsi_1h' in signal:
            print(f"📈 RSI 5m: {signal['rsi_5m']:.2f}")
            print(f"📈 RSI 1h: {signal['rsi_1h']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ RSI Multi-Timeframe test failed: {e}")
        return False

def test_volume_filter():
    """Test Volume Filter Strategy"""
    print("📊 Testing Volume Filter Strategy...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        symbol = "BTCUSDT"
        balance = 1000
        
        signal = strategies.volume_filter_strategy(symbol, balance)
        print(f"📊 Signal: {signal['action']}")
        print(f"📝 Reason: {signal['reason']}")
        
        if 'volume_ratio' in signal:
            print(f"📊 Volume Ratio: {signal['volume_ratio']:.2f}x")
        
        return True
        
    except Exception as e:
        print(f"❌ Volume Filter test failed: {e}")
        return False

def test_advanced_strategy():
    """Test Advanced Strategy"""
    print("📊 Testing Advanced Strategy...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        symbol = "BTCUSDT"
        balance = 1000
        
        signal = strategies.advanced_strategy(symbol, balance)
        print(f"📊 Signal: {signal['action']}")
        print(f"📝 Reason: {signal['reason']}")
        
        if 'rsi' in signal:
            print(f"📈 RSI: {signal['rsi']:.2f}")
        if 'macd_crossover' in signal:
            print(f"📊 MACD: {signal['macd_crossover']}")
        if 'volume_ratio' in signal:
            print(f"📊 Volume: {signal['volume_ratio']:.2f}x")
        if 'candlestick_pattern' in signal:
            print(f"🕯️ Pattern: {signal['candlestick_pattern']}")
        if 'stop_loss' in signal:
            print(f"🛑 Stop Loss: ${signal['stop_loss']:.2f}")
        if 'take_profit' in signal:
            print(f"🎯 Take Profit: ${signal['take_profit']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced Strategy test failed: {e}")
        return False

def test_macd_calculation():
    """Test MACD Calculation"""
    print("📊 Testing MACD Calculation...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        symbol = "BTCUSDT"
        df = strategies.get_market_data(symbol, '1h', 100)
        
        if not df.empty:
            macd_data = strategies.calculate_macd(df['close'].tolist())
            print(f"📊 MACD Line: {macd_data['macd']:.4f}")
            print(f"📊 Signal Line: {macd_data['signal']:.4f}")
            print(f"📊 Histogram: {macd_data['histogram']:.4f}")
            print(f"📊 Crossover: {macd_data['crossover']}")
        
        return True
        
    except Exception as e:
        print(f"❌ MACD test failed: {e}")
        return False

def test_candlestick_patterns():
    """Test Candlestick Pattern Analysis"""
    print("🕯️ Testing Candlestick Pattern Analysis...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        symbol = "BTCUSDT"
        df = strategies.get_market_data(symbol, '1h', 100)
        
        if not df.empty:
            candlestick = strategies.analyze_candlestick_patterns(df)
            print(f"🕯️ Pattern: {candlestick['pattern']}")
            print(f"📊 Signal: {candlestick['signal']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Candlestick test failed: {e}")
        return False

def test_trailing_stop():
    """Test Trailing Stop Calculation"""
    print("📊 Testing Trailing Stop Calculation...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        # Test scenarios
        entry_price = 50000
        current_price = 51000  # Price moved up
        current_stop = 49500
        
        should_update, new_stop = strategies.should_update_trailing_stop(
            entry_price, current_price, current_stop, 0.01
        )
        
        print(f"📊 Entry Price: ${entry_price}")
        print(f"📊 Current Price: ${current_price}")
        print(f"📊 Current Stop: ${current_stop}")
        print(f"📊 New Stop: ${new_stop}")
        print(f"📊 Should Update: {should_update}")
        
        return True
        
    except Exception as e:
        print(f"❌ Trailing Stop test failed: {e}")
        return False

def test_ema_calculation():
    """Test EMA Calculation"""
    print("📊 Testing EMA Calculation...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        symbol = "BTCUSDT"
        df = strategies.get_market_data(symbol, '1h', 100)
        
        if not df.empty:
            volume_ema = strategies.calculate_ema(df['volume'].tolist(), 20)
            current_volume = df['volume'].iloc[-1]
            
            print(f"📊 Volume EMA (20): {volume_ema:.0f}")
            print(f"📊 Current Volume: {current_volume:.0f}")
            print(f"📊 Volume Ratio: {current_volume/volume_ema:.2f}x")
        
        return True
        
    except Exception as e:
        print(f"❌ EMA test failed: {e}")
        return False

def test_all_strategies():
    """Test all available strategies"""
    print("🎯 Testing All Strategies...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        symbol = "BTCUSDT"
        balance = 1000
        
        strategy_list = [
            "RSI_STRATEGY",
            "RSI_MULTI_TF", 
            "VOLUME_FILTER",
            "ADVANCED_STRATEGY",
            "GRID_TRADING",
            "DCA"
        ]
        
        for strategy in strategy_list:
            print(f"\n📊 Testing {strategy}...")
            signal = strategies.get_strategy_signal(strategy, symbol, balance)
            print(f"  Signal: {signal['action']}")
            print(f"  Reason: {signal['reason']}")
            
            if 'stop_loss' in signal:
                print(f"  Stop Loss: ${signal['stop_loss']:.2f}")
            if 'take_profit' in signal:
                print(f"  Take Profit: ${signal['take_profit']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ All strategies test failed: {e}")
        return False

def main():
    """Run all advanced feature tests"""
    print("🧪 Starting Advanced Features Tests...")
    print("=" * 60)
    
    tests = [
        ("RSI Multi-Timeframe", test_rsi_multi_timeframe),
        ("Volume Filter", test_volume_filter),
        ("Advanced Strategy", test_advanced_strategy),
        ("MACD Calculation", test_macd_calculation),
        ("Candlestick Patterns", test_candlestick_patterns),
        ("Trailing Stop", test_trailing_stop),
        ("EMA Calculation", test_ema_calculation),
        ("All Strategies", test_all_strategies),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                print(f"✅ {test_name} test passed")
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Advanced Features Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All advanced features tests passed!")
        print("\n✅ New Features Available:")
        print("• RSI Multi-Timeframe Analysis")
        print("• Volume Filter with EMA")
        print("• Advanced Strategy with MACD & Candlestick")
        print("• Dynamic Stop Loss & Take Profit")
        print("• Trailing Stop Functionality")
        print("• Enhanced Technical Analysis")
        return True
    else:
        print("⚠️ Some advanced features tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 