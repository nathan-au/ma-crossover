import yfinance as yf
import pprint as pp
import matplotlib.pyplot as plt

# ticker = input("Enter ticker: ")
ticker = "meta"
ticker = ticker.upper()

ticker_info = yf.Ticker(ticker).info
ticker_df = yf.download(ticker, period="1y", auto_adjust = True, progress = False)

pp.pprint(ticker_info)
# print(ticker_df)

plt.figure(figsize=(10, 5))
plt.plot(ticker_df.index, ticker_df["Close"], label=ticker)
plt.title(ticker + " Chart")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend(loc="upper left")
plt.grid(True)
plt.show()
