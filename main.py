import yfinance as yf
from pprint import pprint
import matplotlib.pyplot as plt

# ticker = input("Enter ticker: ")
ticker = "duol"
ticker = ticker.upper()
p = "1y"

ticker_info = yf.Ticker(ticker).info
ticker_df = yf.download(ticker, period = p, auto_adjust = True, progress = False)
# valid period values: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

# pp.pprint(ticker_info)

short_term_length = 9
long_term_length = 20

ticker_df[str(short_term_length) + "_MA"] = ticker_df["Close"].rolling(short_term_length).mean()
ticker_df[str(long_term_length) + "_MA"] = ticker_df["Close"].rolling(long_term_length).mean()

print(ticker_df)

first_close_price = ticker_df["Close"].iloc[0]
last_close_price = ticker_df["Close"].iloc[-1]

year_return = (last_close_price - first_close_price) / first_close_price * 100

year_return_percent = year_return.values[0]
year_return_percent = round(year_return_percent, 2)
print(year_return_percent)

plt.figure(figsize = (10, 5))
plt.plot(ticker_df.index, ticker_df["Close"], label = ticker)
plt.plot(ticker_df.index, ticker_df[str(short_term_length) + "_MA"], label = str(short_term_length) + "-day MA")
plt.plot(ticker_df.index, ticker_df[str(long_term_length) + "_MA"], label = str(long_term_length) + "-day MA")

plt.title(ticker + " 1Y Chart (Return: " + str(year_return_percent) + "%)")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend(loc="upper left")
plt.grid(True)
plt.show()
