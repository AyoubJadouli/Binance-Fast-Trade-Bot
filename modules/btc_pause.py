"""
BTC Pause
Prevents buying when BTC is heading down.
Uses ma2, ma3, ma4, ma5, ma10, ma20

Add to Config as signal

Changes required to Bot Code:
def pause_bot()
while os.path.exists("signals/btc_pause.pause")

Helping you out?
Buy me a Beer ;)

nano.to/dano
(fast and feeless)
algo: 7S7UIKHMAO6WVA3VENMGZWPDHVG6FSKVVUYBZNGWNZXMDZSRDHXT43JOKM
(almost as fast, almost as feeless)
"""

import os
import re
import aiohttp
import asyncio
import time
import json
from datetime import datetime
# use if needed to pass args to external modules
import sys
#import bt as bt
from binance.client import Client, BinanceAPIException
from helpers.parameters import parse_args, load_config
from tradingview_ta import TA_Handler, Interval, Exchange
import pandas as pd
import pandas_ta as ta
import ccxt
import requests

# Load creds modules
from helpers.handle_creds import (
	load_correct_creds, load_discord_creds
)

# Settings
SIGNAL_NAME = 'btc_pause'
args = parse_args()
DEFAULT_CONFIG_FILE = 'config.yml'
DEFAULT_CREDS_FILE = 'creds.yml'

config_file = args.config if args.config else DEFAULT_CONFIG_FILE
creds_file = args.creds if args.creds else DEFAULT_CREDS_FILE
parsed_creds = load_config(creds_file)
parsed_config = load_config(config_file)

# Load trading vars
PAIR_WITH = parsed_config['trading_options']['PAIR_WITH']
DISCORD_WEBHOOK = load_discord_creds(parsed_creds)

# Load creds for correct environment
access_key, secret_key = load_correct_creds(parsed_creds)
client = Client(access_key, secret_key)

TIME_TO_WAIT = 1
FULL_LOG = False
DEBUG = True

# send message to discord
DISCORD = True

global paused 
paused = False
# Strategy Settings

LIMIT = 6
INTERVAL = '1m'
percent = 1
EXCHANGE = 'BINANCE'
SCREENER = 'CRYPTO'
SIGNAL_NAME = 'btc_pause'
SIGNAL_TYPE = 'pause'

class txcolors:
    BUY = '\033[92m'
    WARNING = '\033[93m'
    SELL_LOSS = '\033[91m'
    SELL_PROFIT = '\033[32m'
    DIM = '\033[2m\033[35m'
    Red = "\033[31m"
    DEFAULT = '\033[39m'

def msg_discord(msg):
	message = msg + '\n\n'
	mUrl = "https://discordapp.com/api/webhooks/"+DISCORD_WEBHOOK
	data = {"content": message}
	response = requests.post(mUrl, json=data)

def analyse_btc():
    global paused
    signal_coins = {}

    analysis1MIN = {}
    handler1MIN = {}

    pair = "BTC" + PAIR_WITH
    handler1MIN[pair] = TA_Handler(
        symbol=pair,
        exchange=EXCHANGE,
        screener=SCREENER,
        interval=INTERVAL,
        timeout= 10)
                        
    try:
        analysis1MIN = handler1MIN[pair].get_analysis()
    except Exception as e:
        print(f'{SIGNAL_NAME}Exception:')
        print(e)
        print (f'Coin: {pair}')
        print (f'handler: {handler1MIN[pair]}')
        pass

    btc200 = round(analysis1MIN.indicators['SMA200'],2)
    
    if PAIR_WITH != "BTC":
        # Normal Scan for LIMIT and INTERVAL
        exchange = ccxt.binance()
        try:
            btc = exchange.fetch_ohlcv("BTC" + PAIR_WITH, timeframe=INTERVAL, limit=25)
            btc = pd.DataFrame(btc, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            btc['VWAP'] = ((((btc.high + btc.low + btc.close) / 3) * btc.volume) / btc.volume)
            #print(btc)
        except BinanceAPIException as e:
            print('CCXT Error')
            print(e.status_code)
            print(e.message)
            print(e.code)

        try:
            btc2 = btc.ta.sma(length=2)
            btc3 = btc.ta.sma(length=3)
            btc4 = btc.ta.sma(length=4)
            btc5 = btc.ta.sma(length=5)
            btc10 = btc.ta.sma(length=10)
            btc20 = btc.ta.sma(length=20)
            #btc200 = btc.ta.sma(length=200)
            btc2 = round(float(btc2.iloc[-1]),2)
            btc3 = round(float(btc3.iloc[-1]),2)
            btc4 = round(float(btc4.iloc[-1]),2)
            btc5 = round(float(btc5.iloc[-1]),2)
            btc10 = round(float(btc10.iloc[-1]),2)
            btc20 = round(float(btc20.iloc[-1]),2)
            #btc200_1 = btc200.iloc[-1]

            #print(f'{SIGNAL_NAME}: {txcolors.BUY}{btc2:.2f} {btc3:.2f} {btc4:.2f} {btc5:.2f} {btc10:.2f} {btc20:.2f} {btc200[2]:.2f}{txcolors.DEFAULT}')
            print(f'{SIGNAL_NAME}: {txcolors.BUY}sma2:{btc2} sma3:{btc3} sma4:{btc4} sma5:{btc5} sma10:{btc10} sma20:{btc20} sma200:{btc200}{txcolors.DEFAULT}')

            paused = False
            #if btc2 > btc3 > btc4 > btc5 > btc10 > btc20 > btc200:
            if btc2 > btc3 > btc4 > btc5:
                paused = False
                print(f'{SIGNAL_NAME}: {txcolors.BUY}Market looks OK{txcolors.DEFAULT}')

            else:
                print(f'{SIGNAL_NAME}: Market not looking good{txcolors.DEFAULT}')
                paused = True
        except Exception as e:
            print(f'{SIGNAL_NAME}: Exception analyse_btc() 1: {e}{txcolors.DEFAULT}')
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
            pass
    return paused

def do_work():
    global paused
    while True:
        try:
            if PAIR_WITH != "BTC":
                paused = analyse_btc()
                if paused:
                    with open(f'signals/{SIGNAL_NAME}.{SIGNAL_TYPE}', 'a+') as f:
                        f.write('yes')
                    print(f'{SIGNAL_NAME}: {txcolors.BUY}Paused by BTC{txcolors.DEFAULT}')

                else:
                    if os.path.isfile(f'signals/{SIGNAL_NAME}.{SIGNAL_TYPE}'):
                        os.remove(f'signals/{SIGNAL_NAME}.{SIGNAL_TYPE}')
                    print(f'{SIGNAL_NAME}: {txcolors.BUY}Running...{txcolors.DEFAULT}')
                time.sleep(30)
            else:
                print(f'{SIGNAL_NAME}: {txcolors.SELL_LOSS}This module cannot run under its own currency as a base, closing the module......{txcolors.DEFAULT}')
        except Exception as e:
            print(f'{SIGNAL_NAME}: Exception do_work(): {e}{txcolors.DEFAULT}')
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
            continue
        except KeyboardInterrupt as ki:
            continue