import yfinance as yf
from pprint import pprint
import matplotlib.pyplot as plt
import pandas as pd

def calculatePeriodReturn(ticker_data):
    period_start_price = ticker_data["Close"].iloc[0]
    period_end_price = ticker_data["Close"].iloc[-1]

    period_return = (period_end_price - period_start_price) / period_start_price * 100
    period_return = round(period_return.values[0], 2)
    return period_return

def applyMovingAverageCrossover(ticker_data, short_term_moving_average, long_term_moving_average, ticker):
    ticker_data[str(short_term_moving_average) + " MA", ticker] = ticker_data["Close"].rolling(short_term_moving_average).mean() #Calculate moving average
    ticker_data[str(long_term_moving_average) + " MA", ticker] = ticker_data["Close"].rolling(long_term_moving_average).mean()

    ticker_data.columns = ticker_data.columns.set_names(["Data", "Ticker"], level=[0, 1]) #Rename dataframe "Price" to "Data"

    ticker_data["Trend"] = 0 #Initialize Trend column
    ticker_data.loc[ticker_data["9 MA", ticker] > ticker_data["20 MA", ticker], "Trend"] = 1   #Set Trend column to 1 (upwards) for all rows where 9MA > 20MA
    ticker_data.loc[ticker_data["9 MA", ticker] < ticker_data["20 MA", ticker], "Trend"] = -1 

    ticker_data["Crossover"] = ticker_data["Trend"].diff()
    return ticker_data

ticker = "duol"
ticker = ticker.upper()
period = "1y" # valid periods are 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

ticker_info = yf.Ticker(ticker).info
ticker_data = yf.download(ticker, period = period, auto_adjust = True, progress = False)[["Close"]] #Fetch closing price data with yfinance

# pprint(ticker_info)
ticker_short_name = ticker_info["shortName"]

short_term_moving_average = 9
long_term_moving_average = 20

ticker_data = applyMovingAverageCrossover(ticker_data, short_term_moving_average, long_term_moving_average, ticker)

# pd.set_option('display.max_rows', None) #Display all rows
# print(ticker_data)

plt.figure(figsize = (15, 10))
period_return = calculatePeriodReturn(ticker_data)

plt.plot(ticker_data.index, ticker_data["Close"], label = ticker, color = "black", linewidth = 2, zorder = 1) # valid colours are red, green, blue, orange, purple, yellow, pink, cyan, magenta, brown, gray, black, white
plt.plot(ticker_data.index, ticker_data[str(short_term_moving_average) + " MA", ticker], label = str(short_term_moving_average) + "-day MA", color = "cyan", zorder = 2)
plt.plot(ticker_data.index, ticker_data[str(long_term_moving_average) + " MA", ticker], label = str(long_term_moving_average) + "-day MA", color = "magenta", zorder = 2)

plt.scatter(ticker_data.index[ticker_data["Crossover"] == 2], ticker_data["Close"][ticker_data["Crossover"] == 2], marker = "o", color = "green", label="Buy Signal", s = 50, zorder = 3) #zorder = 3 so scatter points appear above plot lines
plt.scatter(ticker_data.index[ticker_data["Crossover"] == -2], ticker_data["Close"][ticker_data["Crossover"] == -2], marker = "o", color = "red", label="Sell Signal", s = 50, zorder = 3)

if (period_return > 0):
    period_return_prefix = " +"
else:
    period_return_prefix = " "

plt.title(ticker_short_name + " Chart (Return:" + period_return_prefix + str(period_return) + "%)")

plt.xlabel("Date ("+ period.upper() + " Range)")
plt.ylabel("Price")
plt.legend(loc="upper left")
plt.grid(True)
plt.show()