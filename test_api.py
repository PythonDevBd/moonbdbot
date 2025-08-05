#!/usr/bin/env python3

from pionex_api import PionexAPI
import json

def test_api():
    print("Testing Pionex API with correct interval format...")
    
    api = PionexAPI()
    
    # First, get all available symbols
    print("\n--- Getting all available symbols ---")
    result = api.get_symbols()
    
    # Handle different possible response structures
    symbols = []
    if 'data' in result:
        if isinstance(result['data'], list):
            symbols = [item['symbol'] for item in result['data'] if 'symbol' in item]
        elif isinstance(result['data'], dict) and 'symbols' in result['data']:
            symbols = [item['symbol'] for item in result['data']['symbols'] if 'symbol' in item]
        elif isinstance(result['data'], dict):
            # Try to find symbols in the data dictionary
            for key, value in result['data'].items():
                if isinstance(value, list):
                    symbols = [item['symbol'] for item in value if isinstance(item, dict) and 'symbol' in item]
                    if symbols:
                        break
    
    if symbols:
        print(f"Found {len(symbols)} symbols")
        
        # Find some common symbols
        common_symbols = ['XRP_USDT', 'TRX_USDT', 'UNI_USDT', 'LINK_USDT', 'ADA_USDT']
        available_common = [s for s in common_symbols if s in symbols]
        
        if available_common:
            print(f"Available common symbols: {available_common[:5]}")
            
            # Test with first available symbol
            test_symbol = available_common[0]
            print(f"\n--- Testing with {test_symbol} ---")
            
            # Test ticker price
            print(f"1. Testing ticker price for {test_symbol}...")
            result = api.get_ticker_price(test_symbol)
            if 'error' not in result:
                print(f"✅ SUCCESS: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ ERROR: {result.get('error', 'Unknown error')}")
            
            # Test klines with correct interval format
            print(f"\n2. Testing klines for {test_symbol} with 1H interval...")
            result = api.get_klines(test_symbol, '1H', 10)
            if 'error' not in result:
                print(f"✅ SUCCESS: Got klines data")
                if 'data' in result and 'klines' in result['data']:
                    print(f"   Number of klines: {len(result['data']['klines'])}")
                    if result['data']['klines']:
                        print(f"   First kline: {result['data']['klines'][0]}")
            else:
                print(f"❌ ERROR: {result.get('error', 'Unknown error')}")
            
            # Test klines with 5M interval
            print(f"\n3. Testing klines for {test_symbol} with 5M interval...")
            result = api.get_klines(test_symbol, '5M', 10)
            if 'error' not in result:
                print(f"✅ SUCCESS: Got klines data")
                if 'data' in result and 'klines' in result['data']:
                    print(f"   Number of klines: {len(result['data']['klines'])}")
            else:
                print(f"❌ ERROR: {result.get('error', 'Unknown error')}")
        else:
            print("No common symbols found in available symbols")
            print(f"First 10 available symbols: {symbols[:10]}")
    else:
        print("Could not get symbols list")
        print(f"Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        if 'data' in result:
            print(f"Data type: {type(result['data'])}, Data keys: {list(result['data'].keys()) if isinstance(result['data'], dict) else 'Not a dict'}")

if __name__ == "__main__":
    test_api() 