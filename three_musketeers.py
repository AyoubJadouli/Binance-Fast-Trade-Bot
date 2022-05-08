# No future support offered, use this script at own risk - test before using real funds
# If you lose money using this MOD (and you will at some point) you've only got yourself to blame!

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
import pandas as pd
import pandas_ta as ta
import ccxt
import requests
from prettytable import PrettyTable, from_html_one
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

#INTERVAL1MIN = Interval.INTERVAL_1_MINUTE
#INTERVAL5MIN = Interval.INTERVAL_5_MINUTES

    # INTERVAL_1_MINUTE = "1m"
    # INTERVAL_5_MINUTES = "5m"
    # INTERVAL_15_MINUTES = "15m"
    # INTERVAL_30_MINUTES = "30m"
    # INTERVAL_1_HOUR = "1h"
    # INTERVAL_2_HOURS = "2h"
    # INTERVAL_4_HOURS = "4h"
    # INTERVAL_1_DAY = "1d"
    # INTERVAL_1_WEEK = "1W"
    # INTERVAL_1_MONTH = "1M"

#OSC_INDICATORS = ['RSI', 'Stoch.RSI', 'Mom', 'MACD', 'UO', 'BBP']

#RSI_MIN = 10
#RSI_MAX = 60
#STOCH_MIN = 10
#STOCH_MAX = 60

#RSI_BUY = 0.3
#STOCH_BUY = 10


class txcolors:
    BUY = '\033[92m'
    WARNING = '\033[93m'
    SELL_LOSS = '\033[91m'
    SELL_PROFIT = '\033[32m'
    DIM = '\033[2m\033[35m'
    DEFAULT = '\033[39m'    
    
EXCHANGE = 'BINANCE'
SCREENER = 'CRYPTO'

global UpperTrendSignal, UnderTrendSignal, SHOW_TABLE_COINS_BOUGHT, coins_bought

UpperTrendSignal=0 
UnderTrendSignal=0
coins_bought = {}

if USE_MOST_VOLUME_COINS == True:        
    TICKERS = "volatile_volume_" + str(date.today()) + ".txt"
else:
    TICKERS = 'tickers.txt'

TIME_TO_WAIT = 1
FULL_LOG = False
DEBUG = True

SIGNAL_NAME = 'Three_Musketeers'
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
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            result = ansi_escape.sub('', logline)
            f.write(timestamp + ' ' + result + '\n')
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
    
def get_analysis(tf, p):
    exchange = ccxt.binance()
    c = exchange.fetch_ohlcv(p, timeframe=tf, limit=25)
    c = pd.DataFrame(c, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    #coins['VWAP'] = ((((coins.high + coins.low + coins.close) / 3) * coins.volume) / coins.volume)
    return c        
    
def analyze(pairs):
    global UpperTrendSignal, UnderTrendSignal, coins_bought
    signal_coins = {}
    #analysis = {}
    #handler = {}
    #analysis1MIN = {}
    #handler1MIN = {}
    #analysis5MIN = {}
    #handler5MIN = {}
    UnderTrendPercentage = 0
    UpperTrendSignal = 0
    
    if os.path.exists(SIGNAL_FILE_BUY ):
        os.remove(SIGNAL_FILE_BUY )

    # for pair in pairs:
        # handler[pair] = TA_Handler(
            # symbol=pair,
            # exchange=EXCHANGE,
            # screener=SCREENER,
            # interval=INTERVAL,
            # timeout= 10)
        # handler1MIN[pair] = TA_Handler(
            # symbol=pair,
            # exchange=EXCHANGE,
            # screener=SCREENER,
            # interval=INTERVAL1MIN,
            # timeout= 10)
        # handler5MIN[pair] = TA_Handler(
            # symbol=pair,
            # exchange=EXCHANGE,
            # screener=SCREENER,
            # interval=INTERVAL5MIN,
            # timeout= 10)
       
    for pair in pairs:
        #exchange = ccxt.binance()
        try:
            #coins = exchange.fetch_ohlcv(pair, timeframe='1m', limit=25)
            #coins = pd.DataFrame(coins, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            #coins['VWAP'] = ((((coins.high + coins.low + coins.close) / 3) * coins.volume) / coins.volume)
            
            coins = get_analysis("1m", pair)
            
            EMA2 = coins.ta.ema(length=2)
            MA3 = coins.ta.sma(length=3)
            
            coins2 = get_analysis("1m", pair)
            
            EMA19 = coins2.ta.ema(length=19)
            EMA7 = coins2.ta.ema(length=7)
            
            EMA19 = EMA19.iloc[-1]
            EMA7 = EMA7.iloc[-1]
            
            EMA2 = EMA2.iloc[-1]
            MA3 = MA3.iloc[-1]
		
            UnderTrendSignal = crossunder (EMA19,EMA7)
            UpperTrendSignal = crossover (EMA19,EMA7)
            
            buySignal =  crossunder (EMA2,MA3)
            sellSignal = crossover (EMA2,MA3)
            
            CrossMA3EMA2 = cross(MA3,EMA2)
            
            if CrossMA3EMA2:
                print(f'{SIGNAL_NAME}: {txcolors.DIM}Current pair {pair} had a cross... MA3: {round(MA3,4)} = EMA2: {round(EMA2,4)}{txcolors.DEFAULT}')
            
            if UnderTrendSignal == True:
                print(f'{SIGNAL_NAME}: {txcolors.BUY}Current pair {pair} is down...EMA19: {round(EMA19,4)} > EMA7: {round(EMA7,4)}{txcolors.DEFAULT}')
                #EMA2UnderTrendPercentage = round((EMA2*100)/MA3,4)
                #EMA7UnderTrendPercentage = round((EMA7*100)/EMA19,4)
                #print(f'{SIGNAL_NAME}:{txcolors.DIM} The percentage of EMA2 is {UnderTrendPercentage}{txcolors.DEFAULT}')
                
            if UpperTrendSignal == True:
                print(f'{SIGNAL_NAME}: {txcolors.SELL_LOSS}Current pair {pair} is high...EMA19: {round(EMA19,4)} < EMA7: {round(EMA7,4)}{txcolors.DEFAULT}')
                #EMA2UpperTrendPercentage = round((EMA2*100)/MA3,4)
                #EMA7UpperTrendPercentage = round((EMA7*100)/EMA19,4)
                #print(f'{SIGNAL_NAME}:{txcolors.DIM} The percentage of EMA2 is {UpperTrendPercentage}{txcolors.DEFAULT}')
            
            #for i in range(4):
            #analysis = handler[pair].get_analysis()
            #analysis1MIN = handler1MIN[pair].get_analysis()
            #analysis5MIN = handler5MIN[pair].get_analysis()
            #p = analysis.indicators["close"]
                
            #RSI = round(analysis.indicators['RSI'],2)
            #RSI1 = round(analysis.indicators['RSI[1]'],2)
            #STOCH_K = round(analysis.indicators['Stoch.K'],2)
            #STOCH_D = round(analysis.indicators['Stoch.D'],2)
            #RSI_DIFF = round(RSI - RSI1,2)
            
            #if cross(EMA2,MA3) == True:
                #write_log(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} Cross EMA2:{EMA2} == MA3:{MA3}{txcolors.DEFAULT}')
            
            #write_log(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} Cross EMA2:{EMA2} == MA3:{MA3}{txcolors.DEFAULT}')
            
            buySignal =  UnderTrendSignal and CrossMA3EMA2 #and EMA2UnderTrendPercentage >= 100.009 #and (STOCH_K >= STOCH_MIN and STOCH_K <= STOCH_MAX) and (STOCH_D >= STOCH_MIN and STOCH_D <= STOCH_MAX)
            sellSignal = UpperTrendSignal and sellSignal #and (STOCH_K >= STOCH_MIN and STOCH_K <= STOCH_MAX) and (STOCH_D >= STOCH_MIN and STOCH_D <= STOCH_MAX)

            if buySignal == True:
                signal_coins[pair] = pair
                #write_log(f'{SIGNAL_NAME}:{txcolors.DIM}{pair} - The percentage of EMA2 is {EMA2UnderTrendPercentage}{txcolors.DEFAULT}')
                #write_log(f'{SIGNAL_NAME}:{txcolors.DIM}{pair} - The percentage of EMA7 is {EMA7UnderTrendPercentage}{txcolors.DEFAULT}')
                write_log(f'{SIGNAL_NAME}:{txcolors.DIM} Current pair {pair} had a cross...MA3: {round(MA3,4)} = EMA2: {round(EMA2,4)}{txcolors.DEFAULT}')
                write_log(f'{SIGNAL_NAME}:{txcolors.BUY} {pair} - Buy Signal Detected \n{txcolors.DEFAULT}') #and STOCH_K:{STOCH_K} >= STOCH_MIN:{STOCH_MIN} and STOCH_K:{STOCH_K} <= STOCH_MAX:{STOCH_MAX} and STOCH_D:{STOCH_D} >= STOCH_MIN:{STOCH_MIN} and STOCH_D:{STOCH_D} <= STOCH_MAX:{STOCH_MAX}{txcolors.DEFAULT}')
                with open(SIGNAL_FILE_BUY,'a+') as f:
                    f.write(pair + '\n')
            
            if SELL_ON_SIGNAL_ONLY == True:            
                if sellSignal == True:
                    write_log(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - Sell Signal Detected - crossunder EMA19:{EMA19} < EMA7:{EMA7} and crossunder MA3:{MA3} < EMA2:{EMA2}{txcolors.DEFAULT}') #and STOCH_K:{STOCH_K} >= STOCH_MIN:{STOCH_MIN} and STOCH_K:{STOCH_K} <= STOCH_MAX:{STOCH_MAX} and STOCH_D:{STOCH_D} >= STOCH_MIN:{STOCH_MIN} and STOCH_D:{STOCH_D} <= STOCH_MAX:{STOCH_MAX}{txcolors.DEFAULT}')
                    if SELL_ON_SIGNAL_ONLY == True:
                        with open(SIGNAL_FILE_SELL,'a+') as f:
                            f.write(pair + '\n')
            #time.sleep(10)
            
        except Exception as e:
            print(SIGNAL_NAME + ":")
            print("Exception:")
            print(e)
            print (f'Coin: {pair}')
            #print (f'handler: {handler[pair]}')
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
            time.sleep((TIME_TO_WAIT*60))
        except Exception as e:
            print(f'{SIGNAL_NAME}: Exception do_work(): {e}')
            pass
        except KeyboardInterrupt as ki:
            pass