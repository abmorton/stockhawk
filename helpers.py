import datetime 
from app import *

# helper functions to clean up app.py / view file

def set_color(change):
	if change < 0.0000000:
		loss = True
	else:
		loss = None
	return loss

# This is to take out punctuation and white spaces from the stock search string.
def clean_stock_search(symbol):
	punctuation = '''!()-[]{ };:'"\,<>./?@#$%^&*_~0123456789'''
	no_punct = ""
	for char in symbol:
		if char not in punctuation:
			no_punct = no_punct + char
	if len(no_punct) == 0:
		no_punct = 'RETRY'
	return no_punct

# Puts various attributes into 'stock' via different Share methods.
def set_stock_data(stock):
	stock.name = stock.data_set["Name"]
	stock.symbol = stock.data_set["Symbol"].upper()
	stock.exchange = stock.get_stock_exchange()
	stock.price = stock.get_price()
	stock.change = stock.get_change()
	stock.percent_change = stock.data_set["PercentChange"]
	stock.afterhours = stock.data_set['AfterHoursChangeRealtime']
	stock.last_traded = stock.get_trade_datetime()
	stock.prev_close = stock.get_prev_close()
	stock.open = stock.get_open()
	stock.bid = stock.data_set['Bid']
	stock.ask = stock.data_set['Ask']
	stock.yr_target = stock.data_set['OneyrTargetPrice']
	stock.volume = stock.get_volume()
	stock.av_volume = stock.get_avg_daily_volume()
	stock.day_low = stock.get_days_low()
	stock.day_high = stock.get_days_high()
	stock.day_range = stock.day_high+" - "+stock.day_low
	stock.year_high = stock.get_year_high()
	stock.year_low = stock.get_year_low()
	stock.year_range = stock.year_high+" - "+stock.year_low
	stock.market_cap = stock.data_set["MarketCapitalization"]
	stock.peratio = stock.data_set["PERatio"]
	stock.div = stock.data_set["DividendYield"]
	stock.ex_div = stock.data_set['ExDividendDate']
	stock.div_pay = stock.data_set['DividendPayDate']
	return stock

# Yahoo dates are strings that look like "8/12/2015"; we need to
# convert this into a python datetime format for the db. However, 
# we will still display the yahoo dates back to the user.
def convert_yhoo_date(yhoo_date):
	# argument yhoo_date should be stock.ev_div or stock.div_pay,
	# which are strings that look like "8/6/2015. They can also be None."
	if yhoo_date != None:
		# split and unpack month, day, year variables
		month, day, year = yhoo_date.split('/')
		# convert from strings to integers, for datetime.date function below
		month = int(month)
		day = int(day)
		year = int(year)
		# create datetime object 
		return datetime.date(year, month, day)
	else:
		return None

def write_stock_to_db(stock):
	# get all stocks to make sure we're not trying to add something 
	# that's already there. Eventually, I might want to update certain fields, 
	# but here I'm creating whole new records at once and some of the fields are 'unique'
	# so it's causing problems. Here, the input 'stock' argument is a stock object
	# which has been passed through the set_stock_data function.
	
	# it might be good to do this in a "if stock in stocks:"" kind of thing,
	# but I'm not sure now

	if Stock.query.filter_by(symbol=stock.symbol).first() == None:
		db.session.add(Stock(stock.symbol, stock.name, stock.exchange, stock.price, stock.div, stock.ex_div, stock.div_pay, stock.market_cap))
		db.session.commit()
	else:
		pass