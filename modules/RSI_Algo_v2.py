# No future support offered, use this script at own risk - test before using real funds
# If you lose money using this MOD (and you will at some point) you've only got yourself to blame!

# TRADE_SLOTS: 1
# STOP_LOSS: 0.5
# TAKE_PROFIT: 0.2
  # USE_TRAILING_STOP_LOSS: True
  # TRAILING_STOP_LOSS: 0.1
  # TRAILING_TAKE_PROFIT: 0.01
#in tickers.txt
# GMT
# APE

from tradingview_ta import TA_Handler, Interval, Exchange
from binance.client import Client, BinanceAPIException
import os
import sys
import glob
from datetime import date, datetime, timedelta
import time
import threading
import array
import statistics
import numpy as np
from math import exp, cos
from analysis_buffer import AnalysisBuffer
from helpers.os_utils import(rchop)
from helpers.parameters import parse_args, load_config
import pandas
import pandas as pd
import pandas_ta as ta
import pandas_ta as pta
import ccxt
import requests
import talib as ta 
import pandas_datareader.data as web
from talib import RSI, BBANDS
import matplotlib.pyplot as plt
import re

args = parse_args()
DEFAULT_CONFIG_FILE = 'config.yml'

config_file = args.config if args.config else DEFAULT_CONFIG_FILE
parsed_config = load_config(config_file)

USE_MOST_VOLUME_COINS = parsed_config['trading_options']['USE_MOST_VOLUME_COINS']
PAIR_WITH = parsed_config['trading_options']['PAIR_WITH']
SELL_ON_SIGNAL_ONLY = parsed_config['trading_options']['SELL_ON_SIGNAL_ONLY']
TEST_MODE = parsed_config['script_options']['TEST_MODE']
LOG_FILE = parsed_config['script_options'].get('LOG_FILE')

INTERVAL = Interval.INTERVAL_1_MINUTE
INTERVAL1MIN = Interval.INTERVAL_1_MINUTE

RSI_MIN = 40
RSI_MIN2 = 0
RSI_MAX = 60

class txcolors:
    BUY = '\033[92m'
    WARNING = '\033[93m'
    SELL_LOSS = '\033[91m'
    SELL_PROFIT = '\033[32m'
    DIM = '\033[2m\033[35m'
    DEFAULT = '\033[39m'
    
EXCHANGE = 'BINANCE'
SCREENER = 'CRYPTO'

if USE_MOST_VOLUME_COINS == True:
    TICKERS = "volatile_volume_" + str(date.today()) + ".txt"
else:
    TICKERS = 'tickers.txt'

TIME_TO_WAIT = 1
FULL_LOG = False
DEBUG = True

SIGNAL_NAME = 'RSI_Algo'
SIGNAL_FILE_BUY = 'signals/' + SIGNAL_NAME + '.buy'
SIGNAL_FILE_SELL ='signals/' + SIGNAL_NAME + '.sell'

def write_log(logline):
    try:
        timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")
        if TEST_MODE:
            file_prefix = 'test_'
        else:
            file_prefix = 'live_'
            
        with open(file_prefix + LOG_FILE,'a') as f:
            f.write(timestamp + ' ' + logline + '\n')
        print(f'{logline}')
    except Exception as e:
        print(f'{"write_log"}: Exception in function: {e}')
        print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
        exit(1)
        
def crossunder(arr1, arr2):
    if arr1 != arr2:
        if arr1 > arr2 and arr2 < arr1:
            CrossUnder = True
        else:
            CrossUnder = False
    else:
        CrossUnder = False
    return CrossUnder

def crossover(arr1, arr2):
    if arr1 != arr2:
        if arr1 < arr2 and arr2 > arr1:
            CrossOver = True
        else:
            CrossOver = False
    else:
        CrossOver = False
    return CrossOver
    
def cross(arr1, arr2):
    if round(arr1,4) == round(arr2,4):
        Cross = True
    else:
        Cross = False
    return Cross
    
def analyze(pairs):
    signal_coins = {}
    analysis = {}
    handler = {}
    analysis1MIN = {}
    handler1MIN = {}
    
    if os.path.exists(SIGNAL_FILE_BUY ):
        os.remove(SIGNAL_FILE_BUY )

    for pair in pairs:
        handler[pair] = TA_Handler(
            symbol=pair,
            exchange=EXCHANGE,
            screener=SCREENER,
            interval=INTERVAL,
            timeout= 5)
        handler1MIN[pair] = TA_Handler(
            symbol=pair,
            exchange=EXCHANGE,
            screener=SCREENER,
            interval=INTERVAL1MIN,
            timeout= 5)
       
    for pair in pairs:
        exchange = ccxt.binance()
        try:
            coins = exchange.fetch_ohlcv(pair, timeframe='1m', limit=25)
            coins = pd.DataFrame(coins, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

            for i in range(4):
                analysis = handler[pair].get_analysis()
                analysis1MIN = handler1MIN[pair].get_analysis()
                
            RSI2 = coins.ta.rsi(length=2)
            SMA50_1MIN = round(analysis1MIN.indicators['SMA50'],4)
            SMA20_1MIN = round(analysis1MIN.indicators['SMA20'],4)
            SMA200_1MIN = round(analysis1MIN.indicators['SMA200'],4)
            RSI2 = RSI2.iloc[-1]
            
            buySignal = crossover(RSI2,RSI_MIN)
            sellSignal = crossunder(RSI2,RSI_MAX)
            #buySignal = crossunder(RSI2,RSI_MIN2) and RSI2 <= RSI_MIN
            
            if buySignal == True:
                signal_coins[pair] = pair
                write_log(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - Buy Signal Detected{txcolors.DEFAULT}') 
                with open(SIGNAL_FILE_BUY,'a+') as f:
                    f.write(pair + '\n')
            
            if SELL_ON_SIGNAL_ONLY == True:
                if sellSignal == True:
                    write_log(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - Sell Signal Detected{txcolors.DEFAULT}')
                    if SELL_ON_SIGNAL_ONLY == True:
                        with open(SIGNAL_FILE_SELL,'a+') as f:
                            f.write(pair + '\n')
            #time.sleep(5)
                
        except Exception as e:
            print(SIGNAL_NAME + ":")
            print("Exception:")
            print(e)
            print (f'Coin: {pair}')
            print (f'handler: {handler[pair]}')
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
            
    return signal_coins

def do_work():
    signal_coins = {}
    pairs = {}

    pairs=[line.strip() for line in open(TICKERS)]
    for line in open(TICKERS):
        pairs=[line.strip() + PAIR_WITH for line in open(TICKERS)] 
    
    while True:
        try:
            if not threading.main_thread().is_alive(): exit()
            print(f'Signals {SIGNAL_NAME}: Analyzing {len(pairs)} coins')
            signal_coins = analyze(pairs)
            print(f'Signals {SIGNAL_NAME}: {len(signal_coins)} coins with Buy Signals. Waiting {TIME_TO_WAIT} minutes for next analysis.')
            time.sleep((TIME_TO_WAIT*5))
        except Exception as e:
            print(f'{SIGNAL_NAME}: Exception do_work(): {e}')
            pass
        except KeyboardInterrupt as ki:
            pass