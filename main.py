import yfinance as yf
import matplotlib.pyplot as plt
import math
import sys

def calculatePeriodReturn(ticker_data, ticker):
    period_start_price = ticker_data["Close", ticker].iloc[0]
    period_end_price = ticker_data["Close", ticker].iloc[-1]

    period_return = (period_end_price - period_start_price) / period_start_price * 100
    period_return = round(period_return, 2)
    return period_return

def applyMovingAverageCrossover(ticker_data, ticker, short_term_moving_average, long_term_moving_average):
    ticker_data[str(short_term_moving_average) + " MA", ticker] = ticker_data["Close", ticker].rolling(short_term_moving_average).mean() #calculate moving average
    ticker_data[str(long_term_moving_average) + " MA", ticker] = ticker_data["Close", ticker].rolling(long_term_moving_average).mean()

    ticker_data.columns = ticker_data.columns.set_names(["Data", "Ticker"], level=[0, 1]) #rename dataframe "Price" to "Data"

    ticker_data["Trend", ticker] = 0 #initialize Trend column
    ticker_data.loc[ticker_data[str(short_term_moving_average) + " MA", ticker] > ticker_data[str(long_term_moving_average) + " MA", ticker], "Trend"] = 1 #set Trend column to 1 (upwards) for all rows where short term MA > long term MA
    ticker_data.loc[ticker_data[str(short_term_moving_average) + " MA", ticker] < ticker_data[str(long_term_moving_average) + " MA", ticker], "Trend"] = -1 

    ticker_data["Crossover", ticker] = ticker_data["Trend", ticker].diff()
    return ticker_data

def runMovingAverageCrossoverStrategy(ticker_data, ticker, net_deposits): 
    current_balance = net_deposits
    if (current_balance <= 0):
        print("\nError: Initial balance must be greater than zero.\n")
        sys.exit(1)
    position_size = 0
    trade_logs = []
    equity_curve = []

    for row in ticker_data.iterrows():

        row_date = row[0].date()
        row_price = row[1]["Close", ticker]
        row_crossover = row[1]["Crossover", ticker]
        
        if (row_crossover == 2 and position_size == 0):
            position_size = math.floor(current_balance / row_price)
            current_balance = current_balance - (position_size * row_price)
            trade_log = str(row_date) + ", " + "BUY " + ", " + str(position_size) + ", " + str(round(current_balance, 2)) + ", " + str(round(row_price, 2))
            trade_logs.append(trade_log)
        elif (row_crossover == -2 and position_size != 0):
            current_balance = current_balance + (position_size * row_price)
            position_size = 0
            trade_log = str(row_date) + ", " + "SELL" + ", " + str(position_size) + ", " + str(round(current_balance, 2)) + ", " + str(round(row_price, 2))
            trade_logs.append(trade_log)
        
        portfolio_value = current_balance + position_size * row_price
        equity_curve.append((row_date, portfolio_value))

    if (position_size != 0):
        final_row_date = ticker_data.index[-1].date()
        final_row_price = ticker_data["Close", ticker].iloc[-1]
        current_balance = current_balance + (position_size * final_row_price)
        position_size = 0
        trade_log = str(final_row_date) + ", " + "EOP SELL" + ", " + str(position_size) + ", " + str(round(current_balance, 2)) + ", " + str(round(final_row_price, 2))
        trade_logs.append(trade_log)
        equity_curve.append((final_row_date, current_balance))

    return trade_logs, current_balance, equity_curve

def buildChart(ticker_data, ticker, short_term_moving_average, long_term_moving_average, period):
    plt.figure(figsize = (10, 5))
    period_return = calculatePeriodReturn(ticker_data, ticker)

    plt.plot(ticker_data.index, ticker_data["Close", ticker], label = ticker, color = "black", linewidth = 2, zorder = 1) # valid colours are red, green, blue, orange, purple, yellow, pink, cyan, magenta, brown, gray, black, white
    plt.plot(ticker_data.index, ticker_data[str(short_term_moving_average) + " MA", ticker], label = str(short_term_moving_average) + "-day MA", color = "cyan", zorder = 2)
    plt.plot(ticker_data.index, ticker_data[str(long_term_moving_average) + " MA", ticker], label = str(long_term_moving_average) + "-day MA", color = "magenta", zorder = 2)

    plt.scatter(ticker_data.index[ticker_data["Crossover", ticker] == 2], ticker_data["Close", ticker][ticker_data["Crossover", ticker] == 2], marker = "o", color = "green", label="Buy Signal", s = 50, zorder = 3) #zorder = 3 so scatter points appear above plot lines
    plt.scatter(ticker_data.index[ticker_data["Crossover", ticker] == -2], ticker_data["Close", ticker][ticker_data["Crossover", ticker] == -2], marker = "o", color = "red", label="Sell Signal", s = 50, zorder = 3)

    ticker_info = yf.Ticker(ticker).info    
    ticker_name = ticker_info["longName"] #attribute could be shortName, longName, displayName (meli melo)
    if (period_return > 0):
        period_return_prefix = " +"
    else:
        period_return_prefix = " "
    plt.title(ticker_name + " " + period.upper() + " Chart (Return:" + period_return_prefix + str(period_return) + "%)")

    period_start_date = ticker_data.index[0].date()
    period_end_date = ticker_data.index[-1].date()
    plt.xlabel("Date (" + str(period_start_date) + " to " + str(period_end_date) + ")")

    ticker_currency = ticker_info["currency"]
    plt.ylabel("Price (" + ticker_currency + ")")
    plt.legend(loc="upper left")
    plt.grid(True)

def displayTradeLogs(trade_logs):
    if (len(trade_logs) != 0):
        print(f"{'Date':<12} {'Action':<12} {'Position':<12} {'Price':<12} {'Balance':<12}")
        print("----------------------------------------------------------------")

        for trade_log in trade_logs:
            date, action, position_size, current_balance, price = trade_log.split(", ")
            print(f"{date:<12} {action:<12} {position_size:<12} {price:<12} {current_balance:<12}")
    else:
        print("No trades were executed during this period.")

def displayStrategySummary(trade_logs, current_balance, net_deposits):
    print("\n================================================================")
    print("                  MA Crossover Strategy Summary                   ")
    displayTradeLogs(trade_logs)
    total_trades = int(len(trade_logs) / 2)
    print("\nTotal trades: " + str(total_trades))

    if (total_trades != 0):
        winning_trades = 0
        i = 0
        while (i < len(trade_logs)):
            _, _, _, _, price_i = trade_logs[i].split(", ")
            _, _, _, _, price_next = trade_logs[i + 1].split(", ")
            if (float(price_next) > float(price_i)):
                winning_trades += 1
            i += 2
        win_rate = winning_trades / total_trades * 100
        print("Win rate: " + str(round(win_rate, 2)) + "%")

    print("Net deposits: " + str(round(net_deposits, 2)))
    print("Current balance: " + str(round(current_balance, 2)))

    total_profit_and_loss = float(current_balance) - net_deposits

    if (total_profit_and_loss > 0):
        total_profit_and_loss_prefix = " +"
    else:
        total_profit_and_loss_prefix = " "
    print("Total P&L:" + total_profit_and_loss_prefix + str(round(total_profit_and_loss, 2)))

    simple_rate_of_return = total_profit_and_loss / net_deposits * 100
    if (simple_rate_of_return > 0):
        simple_rate_of_return_prefix = " +"
    else:
        simple_rate_of_return_prefix = " "
    print("Simple rate of return:" + simple_rate_of_return_prefix + str(round(simple_rate_of_return, 2)) + "%")

    print("================================================================")

def buildEquityCurve(equity_curve, ticker_data, ticker):
    dates = []
    values = []
    for date, value in equity_curve:
        dates.append(date)
        values.append(value)    
    
    plt.figure(figsize=(10,5))
    plt.plot(dates, values, label="Portfolio Value", color="blue")

    strategy_return = (round(values[-1], 2) - round(values[0], 2)) / round(values[0], 2) * 100
    if (strategy_return > 0):
        strategy_return_prefix = " +"
    else:
        strategy_return_prefix = " "
    plt.title("MA Crossover Strategy Equity Curve (Return:" + strategy_return_prefix + str(round(strategy_return, 2)) + "%)")
    
    period_start_date = ticker_data.index[0].date()
    period_end_date = ticker_data.index[-1].date()
    plt.xlabel("Date (" + str(period_start_date) + " to " + str(period_end_date) + ")")    
    
    ticker_info = yf.Ticker(ticker).info    
    ticker_currency = ticker_info["currency"]
    plt.ylabel("Portfolio Value (" + ticker_currency + ")")
    plt.grid(True)
    plt.legend()

ticker = input("\nEnter ticker: ").upper()
period = input("Enter period: ")

try:
    ticker_data = yf.download(ticker, period = period, auto_adjust = True, progress = False)[["Close"]] #fetch closing price data with yfinance
    if (ticker_data.empty):
        print("Error: Data could not be downloaded for " + ticker + ".\n")
        sys.exit(1)
except Exception as e:
    print("\nError: Data could not be downloaded for " + ticker + " - " + str(e) + ".\n")
    sys.exit(1)

short_term_moving_average = 50
long_term_moving_average = 200

ticker_data = applyMovingAverageCrossover(ticker_data, ticker, short_term_moving_average, long_term_moving_average)

net_deposits = 10000
trade_logs, current_balance, equity_curve = runMovingAverageCrossoverStrategy(ticker_data, ticker, net_deposits)

displayStrategySummary(trade_logs, current_balance, net_deposits)

display_chart = input("Display charts? (y/n): ").lower()
if (display_chart == "y"):
    print("\nLoading Charts...\n")
    buildChart(ticker_data, ticker, short_term_moving_average, long_term_moving_average, period)
    buildEquityCurve(equity_curve, ticker_data, ticker)
    plt.show()