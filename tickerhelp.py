from app import *
import pandas as pd 

data = pd.read_csv('companylist.csv')
tickers = data['Symbol']

tickers = tickers.unique()

stocks = Stock.query.all()

stocklist = []

for s in stocks:
	stocklist.append(s.symbol)

print stocklist

tickerlist = []

for t in tickers:
	if t not in stocklist:
		tickerlist.append(t)


for t in tickerlist[2500:2540]:
	try:
		# t = clean_stock_search(t)
		t = Share(t)
		print "got Share for " + t.symbol
		t = set_stock_data(t)
		print "set stock data for " + t.symbol
		try:
			write_stock_to_db(t)
			print "wrote " + t.symbol + " to db"
		except: 
			db.session.rollback()
			print "rolling back db.session"
	except:
		print "skipping " + t.symbol

