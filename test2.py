import asyncio
import ccxt.pro as ccxtpro


async def main():
    coinbase = ccxtpro.coinbasepro({'enableRateLimit': True})

    exchange = coinbase
    symbol = "BTC/USDT"

    print(coinbase, dir(coinbase))
    

    while True:
        orderbook = await exchange.watch_order_book(symbol)
        print(exchange.iso8601(exchange.milliseconds()), symbol, orderbook['asks'][0], orderbook['bids'][0])


asyncio.get_event_loop().run_until_complete(main())