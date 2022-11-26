import ccxt.pro as ccxt 
import asyncio
import sys
from datetime import date, datetime, timedelta
import time
PAIR_WITH="USDT"
async def get_soket_orderbook(name):
    global orderbook
    orderbook={}
    orderbook[name] = await Exchange.watchOrderBook(name+'/'+PAIR_WITH, limit=5)
    
async def refresh_all_orderbooks():
    tasks=[]
    for item1 in VOLATILE_VOLUME_LIST:
                tasks.append(asyncio.create_task(get_soket_orderbook(item1))) 
    result = await asyncio.wait(tasks) 
    
async def main():
    global ex, exchange, Exchange 
    Exchange=ccxt.binance({
    # 'rateLimit': 1000,  # unified exchange property
    # 'headers': {
    #     'YOUR_CUSTOM_HTTP_HEADER': 'YOUR_CUSTOM_VALUE',
    # },
    # 'options': {
    #     'adjustForTimeDifference': True,  # exchange-specific option
    # },

    'enableRateLimit': True
    })
                      
    ex=Exchange
    exchange=Exchange
    await Exchange.load_markets()
    
    try:
        today = "volatile_volume_" + str(date.today()) + ".txt"
        global VOLATILE_VOLUME_LIST
        VOLATILE_VOLUME_LIST=[line.strip() for line in open(today)]
        await refresh_all_orderbooks()
        print('############################## get price #######################################')

        print(orderbook["LTC"]['bids'][0][0])
        time.sleep(30)
        print(orderbook["LTC"]['bids'][0][0])
        print('############################## end get price ###################################')
        await exchange.close()
    except Exception as e:
        print(e)
        await exchange.close()


if __name__ == '__main__':
    req_version = (3,9)
    if sys.version_info[:2] < req_version: 
        print(f'This bot requires Python version 3.9 or higher/newer. You are running version {sys.version_info[:2]} - please upgrade your Python version!!{txcolors.DEFAULT}')
        sys.exit()
		# Load arguments then parse settings


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())