import yfinance as yf
import matplotlib.pyplot as plt
import math

def calculatePeriodReturn(ticker_data):
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

def runMovingAverageCrossoverStrategy(ticker_data, ticker, initial_cash): 
    current_cash = initial_cash
    position = 0
    trade_logs = []

    for row in ticker_data.iterrows():

        row_date = row[0].date()
        row_price = row[1]["Close", ticker]
        row_crossover = row[1]["Crossover", ticker]
        
        if (row_crossover == 2 and position == 0):
            position = math.floor(current_cash / row_price)
            current_cash = current_cash - (position * row_price)
            trade_log = str(row_date) + ", " + "BUY " + ", " + str(position) + ", " + str(round(current_cash, 2)) + ", " + str(round(row_price, 2))
            trade_logs.append(trade_log)

        elif (row_crossover == -2 and position != 0):
            current_cash = current_cash + (position * row_price)
            position = 0
            trade_log = str(row_date) + ", " + "SELL" + ", " + str(position) + ", " + str(round(current_cash, 2)) + ", " + str(round(row_price, 2))

            trade_logs.append(trade_log)

    if (position != 0):
        final_row_date = ticker_data.index[-1].date()
        final_row_price = ticker_data["Close", ticker].iloc[-1]
        current_cash = current_cash + (position * final_row_price)
        position = 0
        trade_log = str(final_row_date) + ", " + "EOP SELL" + ", " + str(position) + ", " + str(round(current_cash, 2)) + ", " + str(round(final_row_price, 2))
        trade_logs.append(trade_log)

    return trade_logs, current_cash

def displayChart(ticker_data, ticker, short_term_moving_average, long_term_moving_average, period):
    plt.figure(figsize = (15, 10))
    period_return = calculatePeriodReturn(ticker_data)

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
    plt.show()

def displayTradeLogs(trade_logs):
    print("----------------------------------------------------------------")
    print(f"{'DATE':<12} {'ACTION':<12} {'POSITION':<12} {'PRICE':<12} {'CASH':<12}")
    print("----------------------------------------------------------------")

    for trade_log in trade_logs:
        date, action, position, current_cash, price = trade_log.split(", ")
        print(f"{date:<12} {action:<12} {position:<12} {price:<12} {current_cash:<12}")
    print("----------------------------------------------------------------")

ticker = "bfly"
ticker = ticker.upper()
period = "10y" #valid periods are 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

ticker_data = yf.download(ticker, period = period, auto_adjust = True, progress = False)[["Close"]] #fetch closing price data with yfinance

short_term_moving_average = 50
long_term_moving_average = 200

ticker_data = applyMovingAverageCrossover(ticker_data, ticker, short_term_moving_average, long_term_moving_average)

initial_cash = 100000
trade_logs, current_cash = runMovingAverageCrossoverStrategy(ticker_data, ticker, initial_cash)

print("================================================================")
print("                        Strategy Summary                        ")


displayTradeLogs(trade_logs)

total_return = float(current_cash) - initial_cash
simple_rate_of_return = total_return / initial_cash * 100
print("Net deposits: " + str(round(initial_cash, 2)))
print("Cash: " + str(round(current_cash, 2)))

if (total_return > 0):
    total_return_prefix = " +"
else:
    total_return_prefix = " "
print("Total P&L:" + total_return_prefix + str(round(total_return, 2)))

if (simple_rate_of_return > 0):
    simple_rate_of_return_prefix = " +"
else:
    simple_rate_of_return_prefix = " "
print("Simple rate of return:" + simple_rate_of_return_prefix + str(round(simple_rate_of_return, 2)) + " %")
print("================================================================")

displayChart(ticker_data, ticker, short_term_moving_average, long_term_moving_average, period)