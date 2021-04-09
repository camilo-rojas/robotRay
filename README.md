# RobotRay

Created by: Camilo Rojas

Python based robot trader on naked put strategy for selected accounts.  

The strategy selected for this bot is to sell puts for a selected number of stocks. The selection of the stock list is currently manual.

ENTRY: The robot searches for opportunities in selling naked puts (sell to open), looking for days with a -4.5% daily price change, which normally increases volatility in the options for the stock.  With the increase in vega we will evaluate the option chain for opportunities that offer a yield of 1% monthly or more.  If we find an opportunity we will generate a prospect that will be managed. The amount of contracts and the R are all defined in a config file.

EXIT AND RISK MANAGEMENT: RobotRay will manage the trade and monitor the following conditions: 1) Risk Loss management will close (BTC) if losses are 2x the amount of premium collected, 2) we are at 21 days to expiration, 3) we reach 50% target of total premium.

The idea is to sell between 3 and 8 month Put options, and close (buy to close) to gain advantage of vega crush and short term volatility.  Worst case scenario of being assigned the contract, bot will confirm buying power.

This is a high risk bot.  For academic purposes only, not for real world implementation.

It connects info from Interactive Brokers for real market data and trading.  Also leverages information from other public data sources to build an analytics model to select trades.

All package requirements are included in the requirements.txt file in the project

FUTURE IDEAS:
1. Telegram integration for two way communication between bot and user
2. Interactive Brokers automated trading
3. Report / Statistics of operation with full P&L reporting
4. Backtrading to review strategy for selected stocks
5. Automated stock selection and rejection based on portfolio and risk
6. Auto evaluate between open positions and new prospects to maximize % of success
