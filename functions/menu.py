

    
async def async_renew_list(in_init=False):
    try:
        global tickers, VOLATILE_VOLUME, FLAG_PAUSE, COINS_MAX_VOLUME, COINS_MIN_VOLUME
        volatile_volume_empty = False
        volatile_volume_time = False
        if USE_MOST_VOLUME_COINS == True:
            today = "volatile_volume_" + str(date.today()) + ".txt"
            if VOLATILE_VOLUME == "":
                volatile_volume_empty = True
            else:
                now = datetime.now()
                dt_string = datetime.strptime(now.strftime("%d-%m-%Y %H_%M_%S"),"%d-%m-%Y %H_%M_%S")
                tuple1 = dt_string.timetuple()
                timestamp1 = time.mktime(tuple1)

                #timestampNOW = now.timestamp()
                dt_string_old = datetime.strptime(VOLATILE_VOLUME.replace("(", " ").replace(")", "").replace("volatile_volume_", ""),"%d-%m-%Y %H_%M_%S") + timedelta(minutes = UPDATE_MOST_VOLUME_COINS)               
                tuple2 = dt_string_old.timetuple()
                timestamp2 = time.mktime(tuple2)
                if timestamp1 > timestamp2:
                    volatile_volume_time = True

            if volatile_volume_time or volatile_volume_empty or os.path.exists(today) == False:
                print(f'{txcolors.WARNING}BOT: {txcolors.DEFAULT}A new Volatily Volume list will be created...{txcolors.DEFAULT}')
                stop_signal_threads()
                FLAG_PAUSE = True
                if TEST_MODE == True:
                    jsonfile = "test_" + COINS_BOUGHT
                else: 
                    jsonfile = "live_" + COINS_BOUGHT
                    
                VOLATILE_VOLUME = get_volume_list()
                
                if os.path.exists(jsonfile):    
                    with open(jsonfile,'r') as f:
                        coins_bought_list = json.load(f)
   
                    
                    with open(today,'r') as f:
                        lines_today = f.readlines()
                    
                    #coinstosave = []

                    for coin_bought in list(coins_bought_list):
                        coin_bought = coin_bought.replace("USDT", "") + "\n"
                        if not coin_bought in list(lines_today):
                            lines_today.append(coin_bought)
                    # for coin in coins_bought_list:
                        # coinstosave.append(coin.replace(PAIR_WITH,"") + "\n")
                    
                    # for c in coinstosave:
                        # for l in lines_today:
                            # if c == l:
                                # break
                            # else:
                                # lines_today.append(c)
                                # break                
                            
                    with open(today,'w') as f:
                        f.writelines(lines_today)

                    print(f'{txcolors.WARNING}BOT: {txcolors.DEFAULT}A new Volatily Volume list has been created, {len(list(coins_bought_list))} coin(s) added...{txcolors.DEFAULT}')
                    FLAG_PAUSE = False
                    #renew_list()
                    load_signal_threads()     
                
        else:
            if in_init:
                stop_signal_threads()
                
                FLAG_PAUSE = True
                
                if TEST_MODE == True:
                    jsonfile = "test_" + COINS_BOUGHT
                else: 
                    jsonfile = "live_" + COINS_BOUGHT
                    
                if os.path.exists(jsonfile): 
                    with open(jsonfile,'r') as f:
                        coins_bought_list = json.load(f)

                    with open(TICKERS_LIST,'r') as f:
                            lines_tickers = f.readlines()
                            
                    if os.path.exists(TICKERS_LIST.replace(".txt",".backup")): 
                        os.remove(TICKERS_LIST.replace(".txt",".backup"))
                        
                    with open(TICKERS_LIST.replace(".txt",".backup"),'w') as f:
                        f.writelines(lines_tickers)
                    
                    new_lines_tickers = []
                    for line_tickers in lines_tickers:
                        if "\n" in line_tickers:
                            new_lines_tickers.append(line_tickers)
                        else:
                            new_lines_tickers.append(line_tickers + "\n")
                                    
                    for coin_bought in list(coins_bought_list):
                        coin_bought = coin_bought.replace("USDT", "") + "\n"
                        if not coin_bought in new_lines_tickers:
                            new_lines_tickers.append(coin_bought)
                            
                    with open(TICKERS_LIST,'w') as f:
                        f.writelines(new_lines_tickers)
                    
            tickers=[line.strip() for line in open(TICKERS_LIST)]
    except Exception as e:
        write_log(f'{txcolors.WARNING}BOT: {txcolors.WARNING}renew_list(): Exception in function: {e}{txcolors.DEFAULT}')
        write_log("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
        pass    

def new_or_continue():
    if TEST_MODE:
        file_prefix = 'test_'
    else:
        file_prefix = 'live_'      
    
    if os.path.exists(file_prefix + str(COINS_BOUGHT)) or os.path.exists(file_prefix + str(BOT_STATS)):
        LOOP = True
        END = False
        while LOOP:
            if ALWAYS_OVERWRITE and ALWAYS_CONTINUE or ALWAYS_OVERWRITE == False and ALWAYS_CONTINUE == False:
                print(f'{txcolors.WARNING}BOT: {txcolors.DEFAULT}The configuration is incorrect, ALWAYS_OVERWRITE and ALWAYS_CONTINUE cannot be true or both can be false{txcolors.DEFAULT}')
                exit(1)
            if ASK_ME:
                print(f'{txcolors.WARNING}BOT: {txcolors.DEFAULT}Do you want to continue previous session?[y/n]{txcolors.DEFAULT}')
                x = input("#: ")
            else:
                if ALWAYS_OVERWRITE:
                    x = "n"
                if ALWAYS_CONTINUE:
                    x = "y"

            if x == "y" or x == "n":
                if x == "y":
                    print(f'{txcolors.WARNING}BOT: {txcolors.DEFAULT}Continuing with the session started ...{txcolors.DEFAULT}')
                    LOOP = False
                    END = True
                else:
                    print(f'{txcolors.WARNING}BOT: {txcolors.DEFAULT}Deleting previous sessions ...')
                    if USE_MOST_VOLUME_COINS == False:
                        if os.path.exists(TICKERS_LIST.replace(".txt",".backup")):
                            with open(TICKERS_LIST.replace(".txt",".backup") ,'r') as f:
                                lines_tickers = f.readlines()                            
                            with open(TICKERS_LIST,'w') as f:
                                f.writelines(lines_tickers)
                            os.remove(TICKERS_LIST.replace(".txt",".backup"))     
                    if os.path.exists(file_prefix + COINS_BOUGHT): os.remove(file_prefix + COINS_BOUGHT)
                    if os.path.exists(file_prefix + BOT_STATS): os.remove(file_prefix + BOT_STATS)
                    if os.path.exists(EXTERNAL_COINS): os.remove(EXTERNAL_COINS)
                    if os.path.exists(file_prefix + TRADES_LOG_FILE): os.remove(file_prefix + TRADES_LOG_FILE)
                    if os.path.exists(file_prefix + HISTORY_LOG_FILE): os.remove(file_prefix + HISTORY_LOG_FILE)
                    if os.path.exists(EXTERNAL_COINS): os.remove(EXTERNAL_COINS)
                    if os.path.exists(file_prefix + LOG_FILE): os.remove(file_prefix + LOG_FILE)
                    files = []
                    folder = "signals"
                    files = [item for sublist in [glob.glob(folder + ext) for ext in ["/*.pause", "/*.buy","/*.sell"]] for item in sublist]
                    for filename in files:
                        if os.path.exists(filename): os.remove(filename)
                    print(f'{txcolors.WARNING}BOT: {txcolors.DEFAULT}Session deleted, continuing ...{txcolors.DEFAULT}')
                    LOOP = False
                    END = True
            else:
                print(f'{txcolors.WARNING}BOT: {txcolors.DEFAULT}Press the y key or the or key ...{txcolors.DEFAULT}')
                LOOP = True
        return END

		
async def menu():
    try:
        global COINS_MAX_VOLUME, COINS_MIN_VOLUME
        global SCREEN_MODE, PAUSEBOT_MANUAL, BUY_PAUSED
        END = False
        LOOP = True
        stop_signal_threads()
        while LOOP:
            time.sleep(1)
            print(f'')
            print(f'')
            print(f'{txcolors.MENUOPTION}[1]{txcolors.WARNING}Reload Configuration{txcolors.DEFAULT}')
            print(f'{txcolors.MENUOPTION}[2]{txcolors.WARNING}Reload modules{txcolors.DEFAULT}')
            print(f'{txcolors.MENUOPTION}[3]{txcolors.WARNING}Reload Volatily Volume List{txcolors.DEFAULT}')
            if BUY_PAUSED == False: #PAUSEBOT_MANUAL == False or 
                print(f'{txcolors.MENUOPTION}[4]{txcolors.WARNING}Stop Purchases{txcolors.DEFAULT}')
            else:
                print(f'{txcolors.MENUOPTION}[4]{txcolors.WARNING}Start Purchases{txcolors.DEFAULT}')
            print(f'{txcolors.MENUOPTION}[5]{txcolors.WARNING}Sell Specific Coin{txcolors.DEFAULT}')
            print(f'{txcolors.MENUOPTION}[6]{txcolors.WARNING}Sell All Coins{txcolors.DEFAULT}')
            print(f'{txcolors.MENUOPTION}[7]{txcolors.WARNING}Exit BOT{txcolors.DEFAULT}')
            x = input('Please enter your choice: ')
            x = int(x)
            print(f'')
            print(f'')
            if x == 1:
                load_settings()
                #print(f'TICKERS_LIST(menu): ' + TICKERS_LIST)
                renew_list()
                LOOP = False
                load_signal_threads()
                print(f'{txcolors.WARNING}BOT: {txcolors.WARNING}Reaload Completed{txcolors.DEFAULT}')
            elif x == 2:
                stop_signal_threads()
                load_signal_threads()
                print(f'{txcolors.WARNING}BOT: {txcolors.WARNING}Modules Realoaded Completed{txcolors.DEFAULT}')
                LOOP = False
            elif x == 3:
                stop_signal_threads()
                #load_signal_threads()
                global VOLATILE_VOLUME
                if USE_MOST_VOLUME_COINS == True:
                    os.remove(VOLATILE_VOLUME + ".txt")
                    VOLATILE_VOLUME = get_volume_list()
                    renew_list()
                else:
                    print(f'{txcolors.WARNING}BOT: {txcolors.WARNING}USE_MOST_VOLUME_COINS must be true in config.yml{txcolors.DEFAULT}')
                    LOOP = False
                print(f'{txcolors.WARNING}BOT: {txcolors.WARNING}VOLATILE_VOLUME Realoaded Completed{txcolors.DEFAULT}')
                load_signal_threads()
                LOOP = False
            elif x == 4:
                if BUY_PAUSED == False:
                    set_config("BUY_PAUSED", True)
                    PAUSEBOT_MANUAL = True
                    BUY_PAUSED = True
                    stop_signal_threads()
                    load_signal_threads()                  
                    LOOP = False
                else:
                    PAUSEBOT_MANUAL = False
                    set_config("BUY_PAUSED", False)
                    BUY_PAUSED = False
                    stop_signal_threads()
                    load_signal_threads()
                    LOOP = False
            elif x == 5:
                #part of extracted from the code of OlorinSledge
                stop_signal_threads()
                while not x == "n":
                    last_price = get_price()
                    print_table_coins_bought()
                    print(f'{txcolors.WARNING}\nType in the Symbol you wish to sell. [n] to continue BOT.{txcolors.DEFAULT}')
                    x = input("#: ")
                    if x == "":
                        break
                    sell_coin(x.upper() + PAIR_WITH)
                load_signal_threads()
                LOOP = False
                
            elif x == 6:
                stop_signal_threads()
                print(f'{txcolors.WARNING}BOT: {txcolors.WARNING}Do you want to sell all coins?[y/n]{txcolors.DEFAULT}')
                sellall = input("#: ")
                if sellall.upper() == "Y":
                    sell_all('Sell all, manual choice!')
                load_signal_threads()
                LOOP = False
            elif x == 7:
                # stop external signal threads
                stop_signal_threads()
                # ask user if they want to sell all coins
                #print(f'\n\n\n')
                #print(f'{txcolors.WARNING}BOT: {txcolors.WARNING}Program execution ended by user!\n\nDo you want to sell all coins?[y/n]{txcolors.DEFAULT}')
                #sellall = input("#: ")
                #if sellall.upper() == "Y":
                    # sell all coins
                    #sell_all('Program execution ended by user!')
                    #END = True
                    #LOOP = False
                print(f'{txcolors.WARNING}BOT: {txcolors.WARNING}Program execution ended by user!{txcolors.DEFAULT}')
                sys.exit(0)
                #else:
                    #END = True
                    #LOOP = False
            else:
                print(f'wrong choice')
                LOOP = True
    except Exception as e:
        write_log(f'{txcolors.WARNING}BOT: {txcolors.WARNING} Exception in menu(): {e}{txcolors.DEFAULT}')
        write_log("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
        pass
    except KeyboardInterrupt as ki:
        await menu()
    return END
    
def print_banner2():
    __header__='''
\033[92m ___ _                        __   __   _      _   _ _ _ _          _____            _ _             ___     _   
\033[92m| _ (_)_ _  __ _ _ _  __ ___  \ \ / ___| |__ _| |_(_| (_| |_ _  _  |_   __ _ __ _ __| (_)_ _  __ _  | _ )___| |_ 
\033[92m| _ | | ' \/ _` | ' \/ _/ -_)  \ V / _ | / _` |  _| | | |  _| || |   | || '_/ _` / _` | | ' \/ _` | | _ / _ |  _|
\033[92m|___|_|_||_\__,_|_||_\__\___|   \_/\___|_\__,_|\__|_|_|_|\__|\_, |   |_||_| \__,_\__,_|_|_||_\__, | |___\___/\__|
\033[92m In intensive collaboration with one10001                    |__/                            |___/ by ABJ    '''
    print(__header__)
    
def print_banner():
         

    __header__='''
\033[92m__________________________________________________________________________________________
\033[92m                                   Binance Fast trader
\033[92m_____________________________________     by ABJ     _____________________________________'''
    print(__header__)

