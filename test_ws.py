import asyncio
import os
import logging
from pionex_ws import PionexWebSocket

logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv('PIONEX_API_KEY')
SECRET_KEY = os.getenv('PIONEX_SECRET_KEY')

async def main():
    ws = PionexWebSocket(API_KEY, SECRET_KEY)

    async def ticker_handler(data):
        print(f"[TICKER] {data}")

    async def orderbook_handler(data):
        print(f"[ORDERBOOK] {data}")

    ws.set_handler('market.ticker', ticker_handler)
    ws.set_handler('market.depth', orderbook_handler)

    # Start connection in background
    asyncio.create_task(ws.connect())
    await asyncio.sleep(2)  # Wait for connection

    # Subscribe to BTCUSDT ticker and orderbook
    await ws.subscribe('market.ticker', {"symbol": "BTCUSDT"})
    await ws.subscribe('market.depth', {"symbol": "BTCUSDT", "level": 20})

    # Run for 30 seconds
    await asyncio.sleep(30)
    await ws.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 