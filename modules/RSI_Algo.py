# No future support offered, use this script at own risk - test before using real funds
# If you lose money using this MOD (and you will at some point) you've only got yourself to blame!

#this module works better activating sale only by signal(SELL_ON_SIGNAL_ONLY)

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
import json

args = parse_args()
DEFAULT_CONFIG_FILE = 'config.yml'

config_file = args.config if args.config else DEFAULT_CONFIG_FILE
parsed_config = load_config(config_file)

USE_MOST_VOLUME_COINS = parsed_config['trading_options']['USE_MOST_VOLUME_COINS']
PAIR_WITH = parsed_config['trading_options']['PAIR_WITH']
SELL_ON_SIGNAL_ONLY = parsed_config['trading_options']['SELL_ON_SIGNAL_ONLY']
TEST_MODE = parsed_config['script_options']['TEST_MODE']
LOG_FILE = parsed_config['script_options'].get('LOG_FILE')
COINS_BOUGHT = parsed_config['script_options'].get('COINS_BOUGHT')

#INTERVAL = Interval.INTERVAL_1_MINUTE
INTERVAL1MIN = Interval.INTERVAL_1_MINUTE
INTERVAL5MIN = Interval.INTERVAL_5_MINUTES


RSI_MIN = 30
RSI_MAX = 70
#if after n seconds the coin was not sold exceeding RSI_MAX it will be sold at the same purchase value or a little more
TIME_MAX = 2820 # 45 minutes

#MACD_MIN = -0.00070 
#MACD_MAX = 0.00060
#RSI_SIG = 30

class txcolors:
    BUY = '\033[92m'
    WARNING = '\033[93m'
    SELL_LOSS = '\033[91m'
    SELL_PROFIT = '\033[32m'
    DIM = '\033[2m\033[35m'
    Red = "\033[31m"
    DEFAULT = '\033[39m'    
    
EXCHANGE = 'BINANCE'
SCREENER = 'CRYPTO'

global bought, timeHold
#bought = {} #UpperTrendSignal, UnderTrendSignal
#timeHold = {}
#UpperTrendSignal=0 
#UnderTrendSignal=0

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
JSON_FILE_BOUGHT = SIGNAL_NAME + '.json'

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
    if round(arr1,5) == round(arr2,5):
        Cross = True
    else:				
        Cross = False
    return Cross
    
def get_analysis(tf, p):
    exchange = ccxt.binance()
    data = exchange.fetch_ohlcv(p, timeframe=tf, limit=25)
    c = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    #coins['VWAP'] = ((((coins.high + coins.low + coins.close) / 3) * coins.volume) / coins.volume)
    return c 

def load_json(p):
    try:
        bought_coin = {}
        value1 = 0
        value2 = 0
        if TEST_MODE:
            file_prefix = 'test_'
        else:
            file_prefix = 'live_'
        coins_bought_file_path = file_prefix + COINS_BOUGHT
        if os.path.exists(coins_bought_file_path) and os.path.getsize(coins_bought_file_path) > 2:
            with open(coins_bought_file_path,'r') as f:
                bought_coin = json.load(f)
            if p in bought_coin:
                value1 = round(float(bought_coin[p]['bought_at']),5)
                value2 = round(float(bought_coin[p]['timestamp']),5)
                bought_coin = {}
    except Exception as e:
        print(f'{SIGNAL_NAME}: {txcolors.Red} {"load_json"}: Exception in function: {e}')
        print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
   
    return value1, value2
    
def analyze(pairs):
    #global bought, timeHold
    #global UpperTrendSignal, UnderTrendSignal
    signal_coins = {}
    #global bought = {}  
    #analysis = {}
    #handler = {}
    analysis1MIN = {}
    handler1MIN = {}
    #analysis5MIN = {}
    #handler5MIN = {}
    last_price = 0
    
    if os.path.exists(SIGNAL_FILE_BUY ):
        os.remove(SIGNAL_FILE_BUY )

    for pair in pairs:
        handler1MIN[pair] = TA_Handler(
            symbol=pair,
            exchange=EXCHANGE,
            screener=SCREENER,
            interval=INTERVAL1MIN,
            timeout= 10)
        # handler5MIN[pair] = TA_Handler(
            # symbol=pair,
            # exchange=EXCHANGE,
            # screener=SCREENER,
            # interval=INTERVAL5MIN,
            # timeout= 10)
    print(f'{SIGNAL_NAME}: {txcolors.BUY}Analyzing {len(pairs)} coins...{txcolors.DEFAULT}')   
    for pair in pairs:
        print(f'{SIGNAL_NAME}: {txcolors.BUY}Analyzing {pair} coin...{txcolors.DEFAULT}') 
        exchange = ccxt.binance()
        try:
            #coins = exchange.fetch_ohlcv(pair, timeframe='1m', limit=25)
            #coins = pd.DataFrame(coins, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            #coins['VWAP'] = ((((coins.high + coins.low + coins.close) / 3) * coins.volume) / coins.volume)

            coins = get_analysis('1m', pair)
            #UnderTrendSignal = (RSI <= RSI_SIG)
            #UpperTrendSignal = crossover (EMA15,EMA7)
            
            #if UnderTrendSignal == True:
                #write_log(f'{SIGNAL_NAME}: {txcolors.SELL_LOSS}Current pair {pair} is down...{txcolors.DEFAULT}')
                
            #if UpperTrendSignal == True:
               #write_log(f'{SIGNAL_NAME}: {txcolors.BUY}Current pair {pair} is high...{txcolors.DEFAULT}')
            
            #for i in range(4):
                #analysis = handler[pair].get_analysis()
            analysis1MIN = handler1MIN[pair].get_analysis()
                #analysis5MIN = handler5MIN[pair].get_analysis()
                #p = analysis.indicators["close"]
                

            #RSI2 = coins.ta.rsi(length=2)
            RSI10 = coins.ta.rsi(length=10)
            #MACD8 = coins.ta.macd(10, 12, 9)
            #MACD8list = MACD8['MACD_10_12_9'].tolist()
            #RSI = coins.ta.rsi(length=14)
            #MA13 = coins.ta.sma(length=3)
            EMA200_1MIN = analysis1MIN.indicators['EMA200']
            #SMA50_1MIN = round(analysis1MIN.indicators['SMA50'],5)
            
            #print(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - MACD8 = {round(MACD8,5)} {txcolors.DEFAULT}')
            
            #RSI2 = RSI2.iloc[-1]
            RSI10 = RSI10.iloc[-1]
            #RSI = RSI.iloc[-1]
            #MA13 = MA13.iloc[-1]
            #MACD8 = float(format(MACD8list[24],"6f"))
            CLOSE = round(coins['close'].iloc[-1],5)
            
            #print(f'EMA200_1MIN= {EMA200_1MIN}')
            print(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - RSI10 = {format(RSI10,"6f")}{txcolors.DEFAULT}')
            #print(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - MACD8 = {format(MACD8list[24],"6f")} {txcolors.DEFAULT}')
            #print(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - EMA500 = {EMA500} {txcolors.DEFAULT}')             
            #print(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - MACD8 = {MACD8} {txcolors.DEFAULT}')
            #buySignal = (RSI2 <= RSI_MIN) >= SMA50_1MIN
            #sellSignal = (RSI2 >= RSI_MAX) <= SMA50_1MIN
            
            #buySignal = (RSI2 <= RSI_MIN) and (EMA2 >= MA13) 
            #sellSignal = (RSI2 >= RSI_MAX) and (EMA2 <= MA13)
            
            #coins2 = get_analysis("1m", pair)
            
            #EMA15 = coins2.ta.ema(length=5)
            #MA13 = coins2.ta.sma(length=5)
            #EMA7 = coins2.ta.ema(length=7)
            
            #EMA15 = EMA15.iloc[-1]
            #MA13 = MA13.iloc[-1]
            #EMA7 = EMA7.iloc[-1]
            
            #UpperTrendSignal = crossover (EMA15,MA13)
            #UnderTrendSignal = crossunder (EMA15,MA13)
            
            # if RSI10 <= RSI_MIN:
                # buySignalRSI10 = True
            # else:
                # buySignalRSI10 = False
                
            # if RSI10 >= RSI_MAX:
                # SellSignalRSI10 = True
            # else:
                # SellSignalRSI10 = False
                
            # if MACD8 <= MACD_MIN:
                # buySignalMACD8 = True
            # else:
                # buySignalMACD8 = False
                
            # if MACD8 >= MACD_MAX:
                # SellSignalMACD8 = True
            # else:
                # SellSignalMACD8 = False

            #if UpperTrendSignal:
                #print(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - RSI2 = {txcolors.DEFAULT}{round(RSI2,5)} {txcolors.BUY}and UpperTrendSignal:{txcolors.DEFAULT}{UpperTrendSignal} {txcolors.BUY}SellSignalRSI2: {txcolors.DEFAULT}{SellSignalRSI2}{txcolors.DEFAULT}')
                
            #if UnderTrendSignal:            
                #print(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - RSI2 = {txcolors.DEFAULT}{round(RSI2,5)} {txcolors.BUY}and UnderTrendSignal:{txcolors.DEFAULT}{UnderTrendSignal} {txcolors.BUY}BuySignalRSI2: {txcolors.DEFAULT}{buySignalRSI2}{txcolors.DEFAULT}')
            #print(f'crossunder(EMA200_1MIN, CLOSE) = {crossunder(EMA200_1MIN, CLOSE)}')
            buySignal = RSI10 <= RSI_MIN #and crossunder(EMA200_1MIN, CLOSE)
            #buySignal = buySignalRSI2 and UnderTrendSignal
            #if buySignalRSI2 == True and UnderTrendSignal == True:
                #buySignal = True
                #print(f'{SIGNAL_NAME}: {txcolors.DIM}{pair} - BUY SIGNAL DETECT{txcolors.DEFAULT}')
            #else:
                #buySignal = False
                #print(f'{SIGNAL_NAME}: {txcolors.DIM}{pair} - NO BUY SIGNAL DETECT{txcolors.DEFAULT}')
                
            #buySignal = buySignalRSI2 and UnderTrendSignal    
            #sellSignal = SellSignalRSI2 and UpperTrendSignal
            
            #buySignal = buySignalRSI2 and buySignalMACD8 and CLOSE < EMA500
            #sellSignal = SellSignalRSI2 and SellSignalMACD8
            
            #buySignal = crossover(RSI2,RSI_MIN) or crossunder(RSI2,RSI_MAX)
            #sellSignal = crossunder(RSI2,RSI_MAX) or crossover(RSI2,RSI_MAX)
            
            #buySignal = crossover(RSI2,RSI_MIN)
            #sellSignal = crossunder(RSI2,RSI_MAX)
            
       
            #if buySignalRSI10 == True:
            #print(bought)
            if buySignal:
                signal_coins[pair] = pair
                #write_log(f'{SIGNAL_NAME}: {txcolors.DIM}{pair} - Buy Signal Detected - RSI10={round(RSI10,5)} CLOSE={round(CLOSE,5)}{txcolors.DEFAULT}') 
                # with open(JSON_FILE_BOUGHT, 'w') as file:
                    # json.dump(bought, file, indent=4)                
                with open(SIGNAL_FILE_BUY,'a+') as f:
                    f.write(pair + '\n')
            
            if SELL_ON_SIGNAL_ONLY == True:
                last_price, timeHold = load_json(pair)
                if last_price != 0:
                    #print(f'{pair} - last_price={last_price} timeHold={timeHold}')
                    time_held = timedelta(seconds=datetime.now().timestamp()-int(timeHold))
                    #print(f'{pair} - time_held= {round(time_held.total_seconds(),0)}')
                    if round(time_held.total_seconds(),0) >= TIME_MAX and TIME_MAX != 0:
                        timemax = True
                        sellSignal = CLOSE >= last_price
                    else:
                        timemax = False
                        sellSignal = RSI10 >= RSI_MAX and last_price !=0 and last_price < CLOSE
                    #For example, here it could be sold with 0.1% more than the purchase
                    #sellSignal = (load_json(pair)+((0.4 * load_json(pair))/100)) >= CLOSE
                    #if sellSignal:
                        #bought.pop(pair)
                        #timeHold.pop(pair)
                        #print(bought)
                    if sellSignal == True:
                        write_log(f'{SIGNAL_NAME}: {txcolors.BUY}{pair} - Sell Signal Detected RSI10={round(RSI10,5)} last_price={last_price} CLOSE={round(CLOSE,5)} timemax= {round(time_held.total_seconds(),0)}/{timemax} sellSignal= {sellSignal}{txcolors.DEFAULT}')
                        #if SELL_ON_SIGNAL_ONLY == True:
                        with open(SIGNAL_FILE_SELL,'a+') as f:
                            f.write(pair + '\n')
            #time.sleep(5)
                
        except Exception as e:
            print(f'{SIGNAL_NAME}: {txcolors.Red} {pair} - Exception: {e}')
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))            
            pass
    return signal_coins

def do_work():
    signal_coins = {}
    pairs = {}
    #global bought, timeHold
    #bought = {}
    #timeHold = {}
    pairs=[line.strip() for line in open(TICKERS)]
    for line in open(TICKERS):
        pairs=[line.strip() + PAIR_WITH for line in open(TICKERS)] 
    while True:
        try:
            if not threading.main_thread().is_alive(): exit()
            print(f'Signals {SIGNAL_NAME}: Analyzing {len(pairs)} coins{txcolors.DEFAULT}')
            signal_coins = analyze(pairs)
            if len(signal_coins) > 0:
                print(f'Signals {SIGNAL_NAME}: {len(signal_coins)} coins  of {len(pairs)} with Buy Signals. Waiting {TIME_TO_WAIT} minutes for next analysis.{txcolors.DEFAULT}')
                time.sleep(TIME_TO_WAIT*60)
            else:
                print(f'Signals {SIGNAL_NAME}: {len(signal_coins)} coins  of {len(pairs)} with Buy Signals. Waiting 5 seconds for next analysis.{txcolors.DEFAULT}')
                time.sleep(5)
        except Exception as e:
            print(f'{SIGNAL_NAME}: {txcolors.Red}: Exception do_work(): {e}{txcolors.DEFAULT}')
            pass
        except KeyboardInterrupt as ki:
            pass