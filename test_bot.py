#!/usr/bin/env python3
"""
Test script for Pionex Trading Bot
Tests bot functionality without executing real trades
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

def test_api_connection():
    """Test Pionex API connection"""
    print("🔌 Testing API connection...")
    
    try:
        api = PionexAPI()
        balances = api.get_balances()
        print('Balances:', balances)
        
        if 'error' in balances:
            print(f"❌ API connection failed: {balances['error']}")
            return False
        
        print("✅ API connection successful")
        return True
        
    except Exception as e:
        print(f"❌ API connection test failed: {e}")
        return False

def test_balance_retrieval():
    """Test balance retrieval"""
    print("💰 Testing balance retrieval...")
    
    try:
        api = PionexAPI()
        balances = api.get_balances()
        print('Balances:', balances)
        
        if 'error' in balances:
            print(f"❌ Balance retrieval failed: {balances['error']}")
            return False
        
        print("✅ Balance retrieval successful")
        if 'data' in balances:
            print(f"📊 Found {len(balances['data'])} assets")
        
        return True
        
    except Exception as e:
        print(f"❌ Balance retrieval test failed: {e}")
        return False

def test_positions_retrieval():
    """Test positions retrieval"""
    print("📊 Testing positions retrieval...")
    
    try:
        api = PionexAPI()
        positions = api.get_positions()
        
        if 'error' in positions:
            print(f"❌ Positions retrieval failed: {positions['error']}")
            return False
        
        print("✅ Positions retrieval successful")
        if 'data' in positions and 'balances' in positions['data']:
            balances = positions['data']['balances']
            non_zero_balances = [b for b in balances if float(b.get('free', 0)) > 0 or float(b.get('frozen', 0)) > 0]
            print(f"📈 Found {len(non_zero_balances)} non-zero balances")
        else:
            print("📈 No position data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Positions retrieval test failed: {e}")
        return False

def test_market_data():
    """Test market data retrieval"""
    print("📈 Testing market data retrieval...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        # Test with BTCUSDT
        symbol = "BTCUSDT"
        ticker = api.get_ticker_price(symbol)
        
        if 'error' in ticker:
            print(f"❌ Market data retrieval failed: {ticker['error']}")
            return False
        
        print(f"✅ Market data retrieval successful for {symbol}")
        if 'price' in ticker:
            print(f"💰 Current price: ${float(ticker['price']):.2f}")
        
        # Test RSI calculation
        df = strategies.get_market_data(symbol, '1h', 100)
        if not df.empty:
            rsi = strategies.calculate_rsi(df['close'].tolist())
            print(f"📊 RSI (14): {rsi:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False

def test_strategies():
    """Test trading strategies"""
    print("🎯 Testing trading strategies...")
    
    try:
        api = PionexAPI()
        strategies = TradingStrategies(api)
        
        # Test RSI strategy
        symbol = "BTCUSDT"
        balance = 1000  # Test with $1000 balance
        
        signal = strategies.rsi_strategy(symbol, balance)
        print(f"📊 RSI Strategy Signal: {signal['action']}")
        print(f"📝 Reason: {signal['reason']}")
        
        # Test grid strategy
        grid_signal = strategies.grid_trading_strategy(symbol, balance)
        print(f"📊 Grid Strategy Signal: {grid_signal['action']}")
        print(f"📝 Reason: {grid_signal['reason']}")
        
        # Test DCA strategy
        dca_signal = strategies.dca_strategy(symbol, balance)
        print(f"📊 DCA Strategy Signal: {dca_signal['action']}")
        print(f"📝 Reason: {dca_signal['reason']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategies test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("🗄️ Testing database functionality...")
    
    try:
        db = Database()
        
        # Test user addition
        test_user_id = 123456789
        db.add_user(test_user_id, "test_user", "Test", "User")
        print("✅ User addition successful")
        
        # Test settings retrieval
        settings = db.get_user_settings(test_user_id)
        print("✅ Settings retrieval successful")
        print(f"📊 Default strategy: {settings.get('default_strategy', 'N/A')}")
        
        # Test settings update
        db.update_user_settings(test_user_id, {'auto_trading': True})
        print("✅ Settings update successful")
        
        # Test trading history
        db.add_trading_history(
            test_user_id, "BTCUSDT", "BUY", "MARKET", 
            0.001, 50000.0, "FILLED", "test_order_123", "RSI_STRATEGY"
        )
        print("✅ Trading history addition successful")
        
        history = db.get_trading_history(test_user_id, 5)
        print(f"📋 Retrieved {len(history)} trading records")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_supported_pairs():
    """Test supported trading pairs"""
    print("🔄 Testing supported trading pairs...")
    
    try:
        api = PionexAPI()
        pairs_response = api.get_trading_pairs()
        
        if 'error' in pairs_response:
            print(f"❌ Trading pairs retrieval failed: {pairs_response['error']}")
            return False
        
        print("✅ Trading pairs retrieval successful")
        
        # Test some supported pairs
        for pair in SUPPORTED_PAIRS[:3]:  # Test first 3 pairs
            ticker = api.get_ticker_price(pair)
            if 'error' not in ticker:
                print(f"✅ {pair}: ${float(ticker.get('price', 0)):.2f}")
            else:
                print(f"❌ {pair}: Error getting price")
        
        return True
        
    except Exception as e:
        print(f"❌ Trading pairs test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting Pionex Trading Bot Tests...")
    print("=" * 50)
    
    tests = [
        ("API Connection", test_api_connection),
        ("Balance Retrieval", test_balance_retrieval),
        ("Positions Retrieval", test_positions_retrieval),
        ("Market Data", test_market_data),
        ("Trading Strategies", test_strategies),
        ("Database", test_database),
        ("Supported Pairs", test_supported_pairs),
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
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready to run.")
        return True
    else:
        print("⚠️ Some tests failed. Please check your configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 