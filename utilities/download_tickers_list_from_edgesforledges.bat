@echo off

For /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
For /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)

set Filename=tickers_INNOVATION%mydate%_%mytime%.txt
REM echo %Filename%

wget -qO- http://edgesforledges.com/watchlists/download/binance/fiat/usdt/innovation-zone | sed s/BINANCE\://g;s/USDT//g > %Filename%

echo Download Completed...

pause