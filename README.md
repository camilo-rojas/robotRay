# RobotRay

Created by: Camilo Rojas - @camilo_rojas

<a href="https://www.buymeacoffee.com/camilorojas" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

Python based robot trader on naked put strategy for selected accounts.  

The strategy selected for this bot is to sell puts for a selected number of stocks. The selection of the stock list is currently manual.

## Entry:
The robot searches for opportunities in selling naked puts (sell to open), looking for days with a -4.5% daily price change, which normally increases volatility in the options for the stock.  With the increase in vega we will evaluate the option chain for opportunities that offer a yield of 1% monthly or more.  If we find an opportunity we will generate a prospect that will be managed. The amount of contracts and the R are all defined in a config file.

## Exit and Risk Management:
RobotRay will manage the trade and monitor the following conditions: 1) Risk Loss management will close (BTC) if losses are 2x the amount of premium collected, 2) we are at 21 days to expiration, 3) we reach 50% target of total premium.

The idea is to sell between 3 and 8 month Put options, and close (buy to close) to gain advantage of vega crush and short term volatility.  Worst case scenario of being assigned the contract, bot will confirm buying power.

This is a **high risk bot**.  For academic purposes only, not for real world implementation.

It connects info from Interactive Brokers for real market data and trading.  Also leverages information from other public data sources to build an analytics model to select trades.

All package requirements are included in the *requirements.txt* file in the project

## Future ideas:
1. Interactive Brokers automated trading
2. Report / Statistics of operation with full P&L reporting
3. Backtrading to review strategy for selected stocks
4. Automated stock selection and rejection based on portfolio and risk
5. Auto evaluate between open positions and new prospects to maximize % of success

## Architecture
The project architecture is the following:

### Bootstrap:
- rrServer - scheduling, threading

### View:
- rrTelegram - communications through Telegram

### Controller:
- rrController
- rrDataFetcher - invoked by rrDB controls data fetching mechanism routing to public or IB

### Model:
- rrDB - Handles DB manager for Stocks, Option Data and Intraday data
- rrThinker - Handles DB manager for Prospects and its lifecycle
- rrDFIB - Interactive Brokers data fetching
- rrDFPublic - Finviz and Yahoo data fetching

### Utilities:
- rrOptions - Support lib for Option formating and management
- rrLogger - Logging

### Parametrization:
- robotRay.ini - File with operational parameters and general configuration

## Getting Started
In a Python shell invoke the *python3 rrlib/rrServer.py* command to start the bot trading program.
Currently no command line parameters are supported, but operation can be configured from the ini file in the rrlib directory.

## Install on CentOS 8
- Generate your userid for robotRay, need sudo (wheel) group for TA-lib and sqlite3 if it needs to be installed, useradd, passwd, usermod -aG wheel
- Yum update python (3.8+), sqlite, ta-lib (https://mrjbq7.github.io/ta-lib/install.html), [tar, xz-devel, gcc, make for ta-lib install].  Or compile/install if not already
- Create your robotRay directory and git fetch https://github.com/camilo-rojas/robotRay
- Create your venv for python if required. python3 -m venv venv.  Activate the environment source venv/bin/activate
- Pip upgrade environment and install all requirements.txt
- Adjust robotRay.ini based from robotRay.sample.ini with your parameters and stock
* If you have problems installing pip install pysqlite3 with errors or problems be sure to install sudo yum install sqlite-devel
