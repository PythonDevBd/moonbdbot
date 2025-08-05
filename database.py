import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # User settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                default_strategy TEXT DEFAULT 'RSI_STRATEGY',
                default_leverage INTEGER DEFAULT 10,
                auto_trading BOOLEAN DEFAULT 0,
                risk_percentage REAL DEFAULT 10.0,
                max_positions INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Trading history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                side TEXT,
                order_type TEXT,
                quantity REAL,
                price REAL,
                status TEXT,
                order_id TEXT,
                strategy TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Active strategies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                strategy_type TEXT,
                parameters TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Portfolio snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_value REAL,
                total_pnl REAL,
                positions_count INTEGER,
                snapshot_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add new user to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        
        # Initialize user settings
        cursor.execute('''
            INSERT OR IGNORE INTO user_settings (user_id)
            VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Get user settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT default_strategy, default_leverage, auto_trading, risk_percentage, max_positions
            FROM user_settings WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'default_strategy': result[0],
                'default_leverage': result[1],
                'auto_trading': bool(result[2]),
                'risk_percentage': result[3],
                'max_positions': result[4]
            }
        return {}
    
    def update_user_settings(self, user_id: int, settings: Dict):
        """Update user settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = []
        values = []
        
        for key, value in settings.items():
            if key in ['default_strategy', 'default_leverage', 'auto_trading', 'risk_percentage', 'max_positions']:
                update_fields.append(f"{key} = ?")
                values.append(value)
        
        if update_fields:
            values.append(datetime.now())
            values.append(user_id)
            
            query = f'''
                UPDATE user_settings 
                SET {', '.join(update_fields)}, updated_at = ?
                WHERE user_id = ?
            '''
            cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def add_trading_history(self, user_id: int, symbol: str, side: str, order_type: str, 
                          quantity: float, price: float, status: str, order_id: str, strategy: str = None):
        """Add trading history record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trading_history 
            (user_id, symbol, side, order_type, quantity, price, status, order_id, strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, symbol, side, order_type, quantity, price, status, order_id, strategy))
        
        conn.commit()
        conn.close()
    
    def get_trading_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user trading history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, side, order_type, quantity, price, status, order_id, strategy, created_at
            FROM trading_history 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        history = []
        for row in results:
            history.append({
                'symbol': row[0],
                'side': row[1],
                'order_type': row[2],
                'quantity': row[3],
                'price': row[4],
                'status': row[5],
                'order_id': row[6],
                'strategy': row[7],
                'created_at': row[8]
            })
        
        return history
    
    def add_active_strategy(self, user_id: int, symbol: str, strategy_type: str, parameters: Dict):
        """Add active strategy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO active_strategies (user_id, symbol, strategy_type, parameters)
            VALUES (?, ?, ?, ?)
        ''', (user_id, symbol, strategy_type, json.dumps(parameters)))
        
        conn.commit()
        conn.close()
    
    def get_active_strategies(self, user_id: int) -> List[Dict]:
        """Get user active strategies"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, strategy_type, parameters, is_active, created_at
            FROM active_strategies 
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        strategies = []
        for row in results:
            strategies.append({
                'symbol': row[0],
                'strategy_type': row[1],
                'parameters': json.loads(row[2]),
                'is_active': bool(row[3]),
                'created_at': row[4]
            })
        
        return strategies
    
    def deactivate_strategy(self, user_id: int, symbol: str, strategy_type: str):
        """Deactivate strategy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE active_strategies 
            SET is_active = 0 
            WHERE user_id = ? AND symbol = ? AND strategy_type = ?
        ''', (user_id, symbol, strategy_type))
        
        conn.commit()
        conn.close()
    
    def add_portfolio_snapshot(self, user_id: int, total_value: float, total_pnl: float, 
                             positions_count: int, snapshot_data: Dict):
        """Add portfolio snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO portfolio_snapshots 
            (user_id, total_value, total_pnl, positions_count, snapshot_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, total_value, total_pnl, positions_count, json.dumps(snapshot_data)))
        
        conn.commit()
        conn.close()
    
    def get_portfolio_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get portfolio history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT total_value, total_pnl, positions_count, snapshot_data, created_at
            FROM portfolio_snapshots 
            WHERE user_id = ? 
            AND created_at >= datetime('now', '-{} days')
            ORDER BY created_at DESC
        '''.format(days), (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        history = []
        for row in results:
            history.append({
                'total_value': row[0],
                'total_pnl': row[1],
                'positions_count': row[2],
                'snapshot_data': json.loads(row[3]),
                'created_at': row[4]
            })
        
        return history 