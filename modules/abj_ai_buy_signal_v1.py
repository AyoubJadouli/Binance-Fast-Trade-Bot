
# ABJ AI MOD

#Best accuracy 98.15% w7 tp:004
# Normalization_File='/UltimeTradingBot/Binance-Fast-Trade-Bot/AI/tp40_w7_max3min_Norm_v1.json'
# Model_FileName='/UltimeTradingBot/Binance-Fast-Trade-Bot/AI/tp40_w7_max3min_Model_v1.hdf5'
# WINDOW_SIZE=7

#97% w30 tp:008
Normalization_File='/UltimeTradingBot/Binance-Fast-Trade-Bot/AI/tp80_w30_max10min_Norm_v1.json'
Model_FileName='/UltimeTradingBot/Binance-Fast-Trade-Bot/AI/tp80_w30_max10min_Model_v1.hdf5'
WINDOW_SIZE=7

window=WINDOW_SIZE
MAX_FORCAST_SIZE=3
BUY_PERCENT=0.29
SELL_PERCENT=0.2
DATA_DIR='/UltimeTradingBot/Data/'
hard_prediction_value=0.5e-01

import sys
import pandas as pd
import json
import time
import timeit
import numpy as np
import urllib
#import ccxt
import  ccxt  
import random
from keras.models import load_model
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import asyncio
import timeit
import tensorflow as tf
from pyparsing import anyOpenTag
TIME_TO_WAIT = 0.3 # Minutes to wait between analysis
ANNOYED_MOD=False
import gc
gc.collect()  


#CHOOSEN_INTERVAL="1m" # 5m 1m-5m 5m-15m 15m 1h 4h

# use for environment variables
import os
# use if needed to pass args to external modules
import sys
# used for directory handling
import glob

import threading
import time
from datetime import date, datetime, timedelta

from helpers.parameters import parse_args, load_config

# Load creds modules
from helpers.handle_creds import (
    load_correct_creds
)
global graph,model

#graph = tf.get_default_graph()

# Settings
args = parse_args()
DEFAULT_CONFIG_FILE = 'config.yml'
DEFAULT_CREDS_FILE = 'creds.yml'

config_file = args.config if args.config else DEFAULT_CONFIG_FILE
creds_file = args.creds if args.creds else DEFAULT_CREDS_FILE
parsed_creds = load_config(creds_file)
parsed_config = load_config(config_file)

# Load trading vars
PAIR_WITH = parsed_config['trading_options']['PAIR_WITH']
EX_PAIRS = parsed_config['trading_options']['EX_PAIRS']
TEST_MODE = parsed_config['script_options']['TEST_MODE']
#TICKERS = parsed_config['trading_options']['TICKERS_LIST']
USE_MOST_VOLUME_COINS = parsed_config['trading_options']['USE_MOST_VOLUME_COINS']

ANNOYED_MOD= parsed_config['trading_options']['ANNOYED_MOD']
WISE_ANNOYED_MOD= parsed_config['trading_options']['WISE_ANNOYED_MOD']
RSI_MIN=  float(parsed_config['trading_options']['RSI_MIN'])
RSI_BUY=  float(parsed_config['trading_options']['RSI_BUY'])
BTC_CHECK_LEVEL=  int(parsed_config['trading_options']['BTC_CHECK_LEVEL'])
CHOOSEN_INTERVAL=  parsed_config['trading_options']['CHOOSEN_INTERVAL']

if USE_MOST_VOLUME_COINS == True:
        #if ABOVE_COINS_VOLUME == True:
    TICKERS = "volatile_volume_" + str(date.today()) + ".txt"
else:
    TICKERS = 'tickers.txt' #'signalsample.txt'
    
MY_EXCHANGE = 'BINANCE'
MY_SCREENER = 'CRYPTO'


FULL_LOG = False # List anylysis result to console

SIGNAL_NAME = 'abj_ai_buy_signal_v1'
SIGNAL_FILE = 'signals/' + SIGNAL_NAME + '.buy'

X_AI_EX_FILE = 'AI_EXBUY'

Exchange=ccxt.binance()
ex=Exchange
exchange=Exchange
pairs=[line.strip() for line in open(TICKERS)]

GoodDeal=[]
BadDeal=[]
pair="ETH/USDT"
min_win_percent=BUY_PERCENT
max_time_window=MAX_FORCAST_SIZE
window=WINDOW_SIZE
import warnings
warnings.filterwarnings('ignore')
PRERR=True
def prerr(err):
    if PRERR:
        print("\033[0;31m Error in "+str(sys._getframe().f_code.co_name) +" \033[0;33m"+str(err))

PDEBUG=True
def pdebug(err):
    if PDEBUG:
        print("\033[0;31m Error in "+str(sys._getframe().f_code.co_name) +" \033[0;33m"+str(err))


try:
    MetaData=pd.read_csv("../Data/MetaData.csv")
except:
    MetaData=get_crypto_metadata(pairs)
try:
    model = load_model(Model_FileName)
    print(Model_FileName+' Loaded')
except:
    prerr('AI Module not Loaded')



##############################################################################################################################################
##############################################################################################################################################
#####################################################   AI FUNCTIONS          ################################################################
##############################################################################################################################################
##############################################################################################################################################
# # Get list of all IDs on binance
def give_first_kline_open_stamp(interval, symbol, start_ts=1499990400000):
        '''
        Returns the first kline from an interval and start timestamp and symbol
        :param interval:  1w, 1d, 1m etc - the bar length to query
        :param symbol:    BTCUSDT or LTCBTC etc
        :param start_ts:  Timestamp in miliseconds to start the query from
        :return:          The first open candle timestamp
        '''

        url_stub = "http://api.binance.com/api/v1/klines?interval="

        #/api/v1/klines?interval=1m&startTime=1536349500000&symbol=ETCBNB
        addInterval   = url_stub     + str(interval) + "&"
        addStarttime  = addInterval   + "startTime="  + str(start_ts) + "&"
        addSymbol     = addStarttime + "symbol="     + str(symbol)
        url_to_get = addSymbol

        kline_data = urllib.request.urlopen(url_to_get).read().decode("utf-8")
        kline_data = json.loads(kline_data)

        return kline_data[0][0]

def get_crypto_metadata(pair_list):
    pairs=pair_list
    ids = []
    #ids = all_ids()
    for halalpair in pairs:
    #    print( halalpair.replace('/',''))
        ids.append(halalpair.replace('/',''))
    #print(ids)
    MetaData=pd.DataFrame(ids)
    MetaData["Pair"]=pairs
    counters=0
    for this_id in ids:
        '''
        Find launch Week of symbol, start at Binance launch date 2017-07-14 (1499990400000)
        Find launch Day of symbol in week
        Find launch minute of symbol in day
        '''

        symbol_launch_week_stamp   = give_first_kline_open_stamp('1w', this_id, 1499990400000 )
        symbol_launch_day_stamp    = give_first_kline_open_stamp('1d', this_id, symbol_launch_week_stamp)
        symbol_launch_minute_stamp = give_first_kline_open_stamp('1m', this_id, symbol_launch_day_stamp)
        MetaData.loc[counters,"launch_week_stamp"]=str(symbol_launch_week_stamp)
        MetaData.loc[counters,"launch_day_stamp"]=str(symbol_launch_day_stamp)
        MetaData.loc[counters,"launch_minute"]=pd.to_datetime(symbol_launch_minute_stamp, unit='ms')

        counters += 1

        #print("Week stamp", symbol_launch_week_stamp)
        #print("Day  stamp", symbol_launch_day_stamp)
        #print("Min  stamp", symbol_launch_minute_stamp)
        print(counters,end=" ")
        #print(this_id, "launched", symbol_launch_minute_stamp )
    return MetaData
    #print("")
    
def normalize(dataset,file=Normalization_File):
    global Normalization
    try:
        N=Normalization
    except:
        Normalization=None
    if(Normalization==None):
        #print('Loading normalization from file')
        with open(file) as json_file:
            Normalization = json.load(json_file)
    else:
        #print('normalization is loaded')
        pass

    mean=np.array(Normalization["mean"])
    std=np.array(Normalization["std"])
    dataset -= mean 
    dataset /= std
    return(dataset)

def Buy_Dessision(input):
    print("making prediction step0")
    A=np.array(input)
    A = A.reshape(1,A.shape[0])
    print("making prediction step1")
    # with tf.compat.v1.get_default_graph():
    predictions = model.predict(normalize(A))
    print("making prediction step2")
    rounded = [round(x[0]) for x in (predictions-hard_prediction_value)]
    print("making prediction step3")
    return(rounded[0])

def Buy_Dessision_Org(input):
    print("making prediction step0")
    A=np.array(input)
    A = A.reshape(1,A.shape[0])
    print("making prediction step1")
    # with tf.compat.v1.get_default_graph():
    predictions = model.predict(normalize(A))
    print("making prediction step2")
    rounded = [round(x[0]) for x in (predictions)]
    print("making prediction step3")
    return(rounded[0])

def Buy_Dessision_Normalized(input):
    A=np.array(input)
    A = A.reshape(1,A.shape[0])
    predictions = model.predict(A)
    rounded = [round(x[0]) for x in predictions]
    return(rounded[0])

def Buy_Dessision_Multi_In_Out(input):
    A=np.array(input)
    predictions = model.predict(normalize(A))
    rounded = [round(x[0]) for x in predictions]
    return(rounded)

def Buy_Dessision_Multi_In_Out_Normalized(input):
    A=np.array(input)
    predictions = model.predict(A)
    rounded = [round(x[0]) for x in predictions]
    return(rounded)

##################################################### V2.0 ################################################################################

def instant_pair_data(pair="GMT/BUSD",exchange=ccxt.binance(),window=WINDOW_SIZE):
    ex=exchange
    ticker = ex.fetch_ticker(pair)
    pair_current_price=ticker['info']['askPrice']
    #print(pair_current_price)

    ohlcv1m = ex.fetch_ohlcv(pair, '1m', limit=window+1)
    ohlcv5m = ex.fetch_ohlcv(pair, '5m', limit=window+1)
    ohlcv15m = ex.fetch_ohlcv(pair, '15m', limit=window+1)
    ohlcv1h = ex.fetch_ohlcv(pair, '1h', limit=window+1)
    ohlcv1d = ex.fetch_ohlcv(pair, '1d', limit=window+1)

    pair_data=pd.DataFrame()
    pair_data.loc[0,"price"]=float(pair_current_price)
    #minute
    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)]=ohlcv1m[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)]=ohlcv1m[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)]=ohlcv1m[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)]=ohlcv1m[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)]=ohlcv1m[-window_i-1][5]

    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][5]  

    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][5]  

    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)+"_15min"]=ohlcv15m[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)+"_15min"]=ohlcv15m[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)+"_15min"]=ohlcv15m[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)+"_15min"]=ohlcv15m[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)+"_15min"]=ohlcv5m[-window_i-1][5]  

    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][5]

    return  pair_data

def instant_full_data(pair,exchange=ex,window=WINDOW_SIZE):
    start = timeit.default_timer()

    pdata=instant_pair_data(pair,exchange=exchange,window=WINDOW_SIZE)
    btcdata=instant_pair_data("BTC/USDT",exchange=exchange,window=WINDOW_SIZE).add_prefix("BTC_")
    Timestamp=pd.to_datetime(ex.fetchTime(),unit='ms')
    pdata=pd.concat([pdata,btcdata],axis=1)
    pdata.loc[0,"day"]=Timestamp.dayofweek+1
    pdata.loc[0,"hour"]=Timestamp.hour
    pdata.loc[0,"minute"]=Timestamp.minute
    stop = timeit.default_timer()
    print("synctime for "+str(pair)+" :"+str(stop-start))
    try:
        pdata.loc[0,"lunch_day"]=int(-(pd.to_datetime(MetaData[MetaData["Pair"] == (pair.split("/")[0]+"/USDT")]["launch_minute"])-pd.Timestamp('2020-01-01 00:00:00.000000')).dt.days)
    except:
        MData=get_crypto_metadata([pair.split("/")[0]+"/USDT"])
        pdata.loc[0,"lunch_day"]=int(-(pd.to_datetime(MData[MData["Pair"] == (pair.split("/")[0]+"/USDT")]["launch_minute"])-pd.Timestamp('2020-01-01 00:00:00.000000')).dt.days)
    for key in pdata.keys():
        if key.find("BTC")!=-1 and (key.find("open")!=-1 or
        key.find("high")!=-1 or key.find("low")!=-1 or key.find("close")!=-1):
            pdata[key]=(pdata["BTC_price"]-pdata[key])/pdata["BTC_price"]
        if key.find("BTC")==-1 and (key.find("open")!=-1 or
        key.find("high")!=-1 or key.find("low")!=-1 or key.find("close")!=-1):
            pdata[key]=(pdata["price"]-pdata[key])/pdata["price"]
    return pdata


import asyncio
PRERR=False


import timeit

window=WINDOW_SIZE
async def do_ohlcv1m(pair,window,ohlcv1m):
    # prerr("Preparing 1 minute candelstics")
    await asyncio.sleep(0)
    ohlcv1m.extend(ex.fetch_ohlcv(pair, '1m', limit=window+1))
    # prerr("-->  1 minute candelstics is ok <--")
async def do_ohlcv5m(pair,window,ohlcv1m):
    # prerr("Preparing 5 minutes candelstics")
    await asyncio.sleep(0)
    ohlcv1m.extend(ex.fetch_ohlcv(pair, '5m', limit=window+1))
    # prerr("-->  5 minutes candelstics is ok <--")
async def do_ohlcv15m(pair,window,ohlcv1m):
    # prerr("Preparing 15 minutes candelstics")
    await asyncio.sleep(0)
    ohlcv1m.extend(ex.fetch_ohlcv(pair, '15m', limit=window+1))
    # prerr("-->  15 minutes candelstics is ok <--")
async def do_ohlcv1h(pair,window,ohlcv1m):
    # prerr("Preparing 1 hour candelstics")
    await asyncio.sleep(0)
    ohlcv1m.extend(ex.fetch_ohlcv(pair, '1h', limit=window+1))
    # prerr("-->  1 hour candelstics is ok <--")
async def do_ohlcv1d(pair,window,ohlcv1m):
    # prerr("Preparing 1 day candelstics")
    await asyncio.sleep(0)
    ohlcv1m.extend(ex.fetch_ohlcv(pair, '1d', limit=window+1))
    # prerr("-->  1 day candelstics is ok <--")

async def do_get_ask_price(pair,price):
    # prerr("Preparing 1 day candelstics")
    await asyncio.sleep(0)
    ticker = ex.fetch_ticker(pair)
    price[0]+=float(ticker['info']['askPrice'])
    # prerr("-->  1 day candelstics is ok <--")



async def async_instant_pair_data(pair="GMT/BUSD",exchange=ccxt.binance(),window=WINDOW_SIZE,pdata=pd.DataFrame()):
    #pair_data=pd.DataFrame()    
    
    pair_data=pdata
    ex=exchange

    ppp=[float(0)]
    #print(pair_current_price)
    ohlcv1m = []
    ohlcv5m = []
    ohlcv15m = []
    ohlcv1h = []
    ohlcv1d = []

    task_askprice = asyncio.create_task(do_get_ask_price(pair,ppp))
    task_ohlcv1m = asyncio.create_task(do_ohlcv1m(pair,window,ohlcv1m))
    task_ohlcv5m = asyncio.create_task(do_ohlcv5m(pair,window,ohlcv5m))
    task_ohlcv15m = asyncio.create_task(do_ohlcv15m(pair,window,ohlcv15m))
    task_ohlcv1h = asyncio.create_task(do_ohlcv1h(pair,window,ohlcv1h))
    task_ohlcv1d = asyncio.create_task(do_ohlcv1d(pair,window,ohlcv1d))

    await asyncio.wait([task_askprice,task_ohlcv1m,task_ohlcv5m,task_ohlcv15m,task_ohlcv1h,task_ohlcv1d])
    pair_current_price=ppp[0]
    #print("task1d   "+str(ohlcv1d))

    pair_data.loc[0,"price"]=float(pair_current_price)
    #minute
    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)]=ohlcv1m[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)]=ohlcv1m[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)]=ohlcv1m[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)]=ohlcv1m[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)]=ohlcv1m[-window_i-1][5]

    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)+"_day"]=ohlcv1d[-window_i-1][5]  

    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)+"_hour"]=ohlcv1h[-window_i-1][5]  

    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)+"_15min"]=ohlcv15m[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)+"_15min"]=ohlcv15m[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)+"_15min"]=ohlcv15m[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)+"_15min"]=ohlcv15m[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)+"_15min"]=ohlcv5m[-window_i-1][5]  

    for window_i in range(1,window+1):
        pair_data.loc[0,"high-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][2]
        pair_data.loc[0,"low-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][3]
        #pair_data.loc[0,"open-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][1]
        pair_data.loc[0,"close-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][4]
        #if(window_i!=1):
        pair_data.loc[0,"volume-"+str(window_i)+"_5min"]=ohlcv5m[-window_i-1][5]  
    return  pair_data



async def do_pdata(pair,exchange,window=WINDOW_SIZE,pdata=pd.DataFrame()):
    # prerr("Preparing 1 day candelstics")
    await async_instant_pair_data(pair=pair,exchange=exchange,window=window,pdata=pdata)
    # prerr("-->  1 day candelstics is ok <--")
async def do_whattime(TimestampAll):
    TimestampAll.append(pd.to_datetime(ex.fetchTime(),unit='ms'))
    
async def async_instant_full_data(pair,exchange=ex,window=WINDOW_SIZE):
    start = timeit.default_timer()
    pdata=pd.DataFrame()
    btcdata=pd.DataFrame()
    #async tascs
    TimestampAll=[]
    task_pdata=asyncio.create_task(do_pdata(pair=pair,exchange=exchange,window=window,pdata=pdata))
    task_btcdata=asyncio.create_task(do_pdata(pair="BTC/USDT",exchange=exchange,window=window,pdata=btcdata))
    task_whattime=asyncio.create_task(do_whattime(TimestampAll)) 
    #Timestamp=pd.to_datetime(ex.fetchTime(),unit='ms')
    await asyncio.wait([task_pdata, task_btcdata, task_whattime])
    Timestamp=TimestampAll[0]
    btcdata=btcdata.add_prefix("BTC_")
    pdata=pd.concat([pdata,btcdata],axis=1)
    pdata.loc[0,"day"]=Timestamp.dayofweek+1
    pdata.loc[0,"hour"]=Timestamp.hour
    pdata.loc[0,"minute"]=Timestamp.minute
    stop = timeit.default_timer()
    print("async time for "+str(pair)+" :"+str(stop-start))
    try:
        pdata.loc[0,"lunch_day"]=int(-(pd.to_datetime(MetaData[MetaData["Pair"] == (pair.split("/")[0]+"/USDT")]["launch_minute"])-pd.Timestamp('2020-01-01 00:00:00.000000')).dt.days)
    except:
        MData=get_crypto_metadata([pair.split("/")[0]+"/USDT"])
        pdata.loc[0,"lunch_day"]=int(-(pd.to_datetime(MData[MData["Pair"] == (pair.split("/")[0]+"/USDT")]["launch_minute"])-pd.Timestamp('2020-01-01 00:00:00.000000')).dt.days)
    for key in pdata.keys():
        if key.find("BTC")!=-1 and (key.find("open")!=-1 or
        key.find("high")!=-1 or key.find("low")!=-1 or key.find("close")!=-1):
            pdata[key]=(pdata["BTC_price"]-pdata[key])/pdata["BTC_price"]
        if key.find("BTC")==-1 and (key.find("open")!=-1 or
        key.find("high")!=-1 or key.find("low")!=-1 or key.find("close")!=-1):
            pdata[key]=(pdata["price"]-pdata[key])/pdata["price"]
    return pdata

async def do_async_instant_full_data(pdata,pair,exchange=ex,window=WINDOW_SIZE):
    
    start = timeit.default_timer()
    #pdata=pd.DataFrame()
    btcdata=pd.DataFrame()
    #async tascs
    TimestampAll=[] 
    task_pdata=asyncio.create_task(do_pdata(pair=pair,exchange=exchange,window=window,pdata=pdata))
    task_btcdata=asyncio.create_task(do_pdata(pair="BTC/USDT",exchange=exchange,window=window,pdata=btcdata))
    task_whattime=asyncio.create_task(do_whattime(TimestampAll)) 
    #Timestamp=pd.to_datetime(ex.fetchTime(),unit='ms')
    await asyncio.wait([task_pdata, task_btcdata, task_whattime])
    Timestamp=TimestampAll[0]
    btcdata=btcdata.add_prefix("BTC_")
    #pdata=pd.concat([pdata,btcdata],axis=1,copy=False)
    #pdata.join(btcdata)
    for k in btcdata.keys():
        pdata.loc[0,str(k)]=btcdata[str(k)][0]
    pdata.loc[0,"day"]=Timestamp.dayofweek+1
    pdata.loc[0,"hour"]=Timestamp.hour
    pdata.loc[0,"minute"]=Timestamp.minute
    stop = timeit.default_timer()
    print("async time for "+str(pair)+" :"+str(stop-start))
    try:
        pdata.loc[0,"lunch_day"]=int(-(pd.to_datetime(MetaData[MetaData["Pair"] == (pair.split("/")[0]+"/USDT")]["launch_minute"])-pd.Timestamp('2020-01-01 00:00:00.000000')).dt.days)
    except:
        MData=get_crypto_metadata([pair.split("/")[0]+"/USDT"])
        pdata.loc[0,"lunch_day"]=int(-(pd.to_datetime(MData[MData["Pair"] == (pair.split("/")[0]+"/USDT")]["launch_minute"])-pd.Timestamp('2020-01-01 00:00:00.000000')).dt.days)
    for key in pdata.keys():
        if key.find("BTC")!=-1 and (key.find("open")!=-1 or
        key.find("high")!=-1 or key.find("low")!=-1 or key.find("close")!=-1):
            pdata[key]=(pdata["BTC_price"]-pdata[key])/pdata["BTC_price"]
        if key.find("BTC")==-1 and (key.find("open")!=-1 or
        key.find("high")!=-1 or key.find("low")!=-1 or key.find("close")!=-1):
            pdata[key]=(pdata["price"]-pdata[key])/pdata["price"]

async def get_all_data_for(list_pair=pairs,exchange=ex,window=WINDOW_SIZE):
    #loop init data dic
    data_dic={}
    for pair in list_pair:
        data_dic[pair]=pd.DataFrame()
    
    ###loop tasklist
    task_list=[]
    for pair in list_pair:
        task_list.append(   asyncio.create_task(do_async_instant_full_data(pair=pair,exchange=exchange,window=window,pdata=data_dic[pair]))   )
    await asyncio.wait(task_list)

    return(data_dic)







##############################################################################################################################################
##############################################################################################################################################
#####################################################   END AI FUNCTIONS          ############################################################
##############################################################################################################################################
##############################################################################################################################################



PDEBUG=True


def analyze(pairs):
    signal_coins = {}
    print('########################################### Start Analyser ###################################################')
    if os.path.exists(SIGNAL_FILE):
        os.remove(SIGNAL_FILE)

    if os.path.exists(X_AI_EX_FILE):
        os.remove(X_AI_EX_FILE)
    #BTC_OK=btc_check(BTC_CHECK_LEVEL)
    break_out_flag = False
    iii=0
    for pair in pairs:
        print(f"-------> working on : {pair} <------------")
        pair_usdt=pair.split(PAIR_WITH)[0]+"/USDT"
        pair_usdt=pair_usdt.split('/USDT')[0]+"/USDT"
        print(f"-------> pair_usdt : {pair_usdt} <------------")
        try:
            pdata=instant_full_data(pair_usdt,exchange=ex,window=WINDOW_SIZE)
            print(f"{pdata}")
            BuyD=Buy_Dessision(pdata.iloc[0])
            print(f"XXXXXX=================  buy dession for :{pair} is {BuyD} ==================XXXXXXX")
            if int(BuyD) == 1:
                print("Good : " +pair)
                print("buying at"+str(pdata["price"].iloc[0]))
                bt=pd.to_datetime(ex.fetchTime(),unit='ms')
                pp=ex.fetch_ticker(pair_usdt)['info']['askPrice']
                GoodDeal.append({"pair":pair_usdt,
                            "buying_time":bt,
                            "buying_price":float(pdata["price"].iloc[0]),
                            "Selling_time":bt,
                            "selling_price":float(pp)})
                signal_coins[pair] = pair          
                with open(SIGNAL_FILE,'a+') as f: f.write(pair + '\n')
            
        except Exception as e:
            print(f'{SIGNAL_NAME}')
            print("Exception:")
            print(e)
            print (f'Coin: {pair}')
            #print (f'The handler interval: {interval}')
            #print (f'The handler pair: {the_handler}')
            with open(X_AI_EX_FILE,'a+') as f:
                    f.write(pair.removesuffix(PAIR_WITH) + '\n')
            continue
        
        
        if FULL_LOG:
                
                print(f'{SIGNAL_NAME}: {pair} \n'+
                    f'Seem Good deals {GoodDeal[iii]["pair"]} detection_price {GoodDeal[iii]["buying_price"]}\n'+
                    f'Recheck time {GoodDeal[iii]["Selling_time"]} recheck price {GoodDeal[iii]["selling_price"]}\n'

                    )
        iii+=1

            # for i in range(max_time_window*2):
            #     time.sleep(30)
            #     pp=ex.fetch_ticker(pair)['info']['askPrice']
            #     if((float(pdata.loc[0,"price"])*0.01*min_win_percent+float(pdata.loc[0,"price"])) <= float(pp)):
            #         GoodDeal.append({"pair":pair,
            #                          "buying_time":bt,
            #                          "buying_price":float(pdata["price"].iloc[0]),
            #                          "Selling_time":pd.to_datetime(ex.fetchTime(),unit='ms'),
            #                          "selling_price":float(pp)})
            #         print("+++ wining bought at:"+str(pdata.loc[0,"price"]) +" sold at: "+str(pp) )
            #         break_out_flag = True
            #         break     


            
    
    
    return signal_coins

def do_work():
    print(f'{SIGNAL_NAME} - Starting')
    while True:
        try:
            if not os.path.exists(TICKERS):
                time.sleep((TIME_TO_WAIT*60))
                continue

            signal_coins = {}
            pairs = {}

            pairs=[line.strip() for line in open(TICKERS)]
            for line in open(TICKERS):
                pairs=[line.strip() + PAIR_WITH for line in open(TICKERS)] 
            print("abj_ai_buy_signal_v1.py")
            if not threading.main_thread().is_alive(): exit()
            print(f'{SIGNAL_NAME}: Analyzing {len(pairs)} coins')
            signal_coins = analyze(pairs)
            print(f'{SIGNAL_NAME}: {len(signal_coins)} coins with Buy Signals. Waiting {TIME_TO_WAIT} minutes for next analysis.')

            time.sleep((TIME_TO_WAIT*60))
        except Exception as e:
            print(f'{SIGNAL_NAME}: Exception do_work() 1: {e}')
            continue
        except KeyboardInterrupt as ki:
            continue