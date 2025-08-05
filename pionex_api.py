import requests
import hmac
import hashlib
import time
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import urlencode
import random
import os
from dotenv import load_dotenv

from config_loader import get_config

load_dotenv()  # Load .env variables

class PionexAPI:
    def __init__(self):
        self.api_key = os.getenv('PIONEX_API_KEY')
        self.secret_key = os.getenv('PIONEX_SECRET_KEY')
        self.config = get_config()
        self.base_url = "https://api.pionex.com"
        self.retry_attempts = self.config.get('api', {}).get('retry_attempts', 3)
        self.retry_backoff = self.config.get('api', {}).get('retry_backoff', 1.5)
        self.timeout = self.config.get('api', {}).get('timeout', 30)
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_delay = 0.1
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PionexTradingBot/1.0'
        })

    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
        self.request_count += 1

    def _generate_signature(self, params: Dict) -> str:
        try:
            sorted_params = dict(sorted(params.items()))
            query_string = urlencode(sorted_params)
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return signature
        except Exception as e:
            self.logger.error(f"Error generating signature: {e}")
            raise

    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        import json as pyjson
        url = f"{self.base_url}{endpoint}"
        self._rate_limit()
        if params is None:
            params = {}
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PionexTradingBot/1.0'
        }
        body = ''
        if signed:
            timestamp = str(int(time.time() * 1000))
            params['timestamp'] = timestamp
            sorted_items = sorted(params.items())
            query_string = '&'.join(f'{k}={v}' for k, v in sorted_items)
            path_url = f"{endpoint}?{query_string}" if query_string else endpoint
            sign_str = f"{method.upper()}{path_url}"
            if method.upper() in ['POST', 'DELETE']:
                body = pyjson.dumps(params, separators=(',', ':')) if params else ''
                sign_str += body
            signature = hmac.new(self.secret_key.encode(), sign_str.encode(), hashlib.sha256).hexdigest()
            headers['PIONEX-KEY'] = self.api_key
            headers['PIONEX-SIGNATURE'] = signature
        # Debug prints
        print(f"[DEBUG] Request: {method.upper()} {url}")
        print(f"[DEBUG] Headers: {headers}")
        if method.upper() == 'GET':
            print(f"[DEBUG] Params: {params}")
        else:
            print(f"[DEBUG] Body: {pyjson.dumps(params, separators=(',', ':')) if params else ''}")
        last_exception = None
        for attempt in range(self.retry_attempts):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, data=pyjson.dumps(params), headers=headers, timeout=self.timeout)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url, data=pyjson.dumps(params), headers=headers, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                if response.status_code == 200:
                    data = response.json()
                    if 'code' in data and data['code'] != 0:
                        error_msg = data.get('msg', 'Unknown API error')
                        self.logger.error(f"API error: {error_msg} (code: {data['code']})")
                        return {'error': error_msg, 'code': data['code']}
                    return data
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue
                elif response.status_code >= 500:
                    self.logger.warning(f"Server error {response.status_code}, attempt {attempt + 1}/{self.retry_attempts}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_backoff ** attempt)
                    continue
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    self.logger.error(error_msg)
                    return {'error': error_msg}
            except requests.exceptions.Timeout:
                last_exception = f"Request timeout (attempt {attempt + 1}/{self.retry_attempts})"
                self.logger.warning(last_exception)
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_backoff ** attempt)
                continue
            except requests.exceptions.ConnectionError as e:
                last_exception = f"Connection error: {e} (attempt {attempt + 1}/{self.retry_attempts})"
                self.logger.warning(last_exception)
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_backoff ** attempt)
                continue
            except Exception as e:
                last_exception = f"Request error: {e} (attempt {attempt + 1}/{self.retry_attempts})"
                self.logger.error(last_exception)
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_backoff ** attempt)
                continue
        return {'error': f"All retry attempts failed. Last error: {last_exception}"}

    # --- Account Endpoints ---
    def get_balances(self) -> Dict:
        """GET /api/v1/account/balances"""
        return self._make_request('GET', '/api/v1/account/balances', signed=True)

    def get_assets(self) -> Dict:
        """GET /api/v1/account/assets"""
        return self._make_request('GET', '/api/v1/account/assets', signed=True)

    def get_positions(self) -> Dict:
        """GET /api/v1/account/balances (as a proxy for positions)"""
        return self._make_request('GET', '/api/v1/account/balances', signed=True)

    # --- Order Endpoints ---
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: str = None, client_order_id: str = None, **kwargs) -> Dict:
        """POST /api/v1/trade/order"""
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': quantity
        }
        if price:
            params['price'] = price
        if client_order_id:
            params['clientOrderId'] = client_order_id
        params.update(kwargs)
        return self._make_request('POST', '/api/v1/trade/order', params, signed=True)

    def get_order(self, order_id: int, symbol: str) -> Dict:
        """GET /api/v1/trade/order"""
        params = {'orderId': order_id, 'symbol': symbol}
        return self._make_request('GET', '/api/v1/trade/order', params, signed=True)

    def cancel_order(self, order_id: int, symbol: str) -> Dict:
        """DELETE /api/v1/trade/order"""
        params = {'orderId': order_id, 'symbol': symbol}
        return self._make_request('DELETE', '/api/v1/trade/order', params, signed=True)

    def get_open_orders(self, symbol: str = None) -> Dict:
        """GET /api/v1/trade/openOrders"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/api/v1/trade/openOrders', params, signed=True)

    def get_all_orders(self, symbol: str = None, limit: int = 100) -> Dict:
        """GET /api/v1/trade/allOrders"""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/api/v1/trade/allOrders', params, signed=True)

    # --- Fills (Trade History) Endpoints ---
    def get_fills(self, symbol: str = None, order_id: int = None) -> Dict:
        """GET /api/v1/trade/fills"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        if order_id:
            params['orderId'] = order_id
        return self._make_request('GET', '/api/v1/trade/fills', params, signed=True)

    # --- Grid Trading Endpoints ---
    def create_grid_bot(self, symbol: str, params: Dict) -> Dict:
        """POST /api/v1/grid/order"""
        params['symbol'] = symbol
        return self._make_request('POST', '/api/v1/grid/order', params, signed=True)

    def get_grid_bot(self, grid_id: str) -> Dict:
        """GET /api/v1/grid/order"""
        params = {'gridId': grid_id}
        return self._make_request('GET', '/api/v1/grid/order', params, signed=True)

    def stop_grid_bot(self, grid_id: str) -> Dict:
        """POST /api/v1/grid/order/stop"""
        params = {'gridId': grid_id}
        return self._make_request('POST', '/api/v1/grid/order/stop', params, signed=True)

    def list_grid_bots(self) -> Dict:
        """GET /api/v1/grid/order/list"""
        return self._make_request('GET', '/api/v1/grid/order/list', signed=True)

    # --- Market Data Endpoints (Public) ---
    def get_symbols(self) -> Dict:
        """GET /api/v1/common/symbols"""
        return self._make_request('GET', '/api/v1/common/symbols')

    def get_klines(self, symbol: str, interval: str = '1H', limit: int = 100) -> Dict:
        """GET /api/v1/market/klines"""
        # Convert interval format to match Pionex API requirements
        interval_map = {
            '1m': '1M',
            '5m': '5M',
            '15m': '15M',
            '30m': '30M',
            '1h': '1H',
            '4h': '4H',
            '8h': '8H',
            '12h': '12H',
            '1d': '1D'
        }

        # Convert interval to proper format
        api_interval = interval_map.get(interval.lower(), interval.upper())

        params = {
            'symbol': symbol,
            'interval': api_interval,
            'limit': min(limit, 500)  # Ensure limit doesn't exceed 500
        }

        response = self._make_request('GET', '/api/v1/market/klines', params)

        # Handle the response structure according to documentation
        if 'data' in response and isinstance(response['data'], dict) and 'klines' in response['data']:
            return response
        elif 'data' in response and isinstance(response['data'], list):
            # If data is directly a list, wrap it in the expected format
            return {
                'result': True,
                'data': {'klines': response['data']},
                'timestamp': response.get('timestamp', int(time.time() * 1000))
            }

        return response

    def get_ticker(self, symbol: str = None) -> Dict:
        """GET /api/v1/market/tickers"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/api/v1/market/tickers', params)

    def get_depth(self, symbol: str, limit: int = 100) -> Dict:
        """GET /api/v1/market/depth"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/api/v1/market/depth', params)

    def get_trades(self, symbol: str, limit: int = 100) -> Dict:
        """GET /api/v1/market/trades"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/api/v1/market/trades', params)

    def get_ticker_price(self, symbol: str) -> Dict:
        """Get current ticker price for a symbol"""
        params = {'symbol': symbol}
        response = self._make_request('GET', '/api/v1/market/tickers', params)

        if 'error' in response:
            return response

        if 'data' in response and isinstance(response['data'], dict) and 'tickers' in response['data']:
            for ticker in response['data']['tickers']:
                if isinstance(ticker, dict) and ticker.get('symbol') == symbol:
                    return {'data': {'price': ticker.get('close', '0')}}

        # If not found in list, return error
        return {'error': f"Symbol {symbol} not found in ticker data"}

    def get_trading_pairs(self) -> Dict:
        """Get trading pairs"""
        return self._make_request('GET', '/api/v1/market/symbols')

    def get_account_info(self) -> Dict:
        """Get account information - uses balances as a proxy for account status"""
        try:
            # Use get_balances as a proxy for account info since Pionex doesn't have a dedicated account info endpoint
            balances_response = self.get_balances()
            
            if 'error' in balances_response:
                return {'error': balances_response['error']}
            
            # Extract account info from balances response
            account_info = {
                'status': 'success',
                'data': {
                    'account_status': 'active',
                    'balances_count': len(balances_response.get('data', {}).get('balances', [])),
                    'last_updated': int(time.time() * 1000)
                }
            }
            
            return account_info
            
        except Exception as e:
            return {'error': f'Failed to get account info: {str(e)}'}

    def test_connection(self) -> Dict:
        try:
            balance = self.get_balances()
            if 'error' in balance:
                return {'error': f"Authentication error: {balance['error']}"}
            return {'status': 'connected'}
        except Exception as e:
            return {'error': f"Connection test failed: {str(e)}"} 