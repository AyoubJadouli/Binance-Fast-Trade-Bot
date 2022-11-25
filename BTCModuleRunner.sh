#!/bin/bash
LOG_FILE=BTC_module.log
ERR_FILE=BTC_module.err 
MODULE=abj_ai_BTC_ONLY
#sleep 1
kill -9 $(ps aux | grep $MODULE |grep python | grep -v grep| awk '{print $2}') || sleep 1
nohup python -c "from modules."$MODULE" import *;do_work()" 1>$LOG_FILE 2>$ERR_FILE &
