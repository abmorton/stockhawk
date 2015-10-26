# import datetime
# from functools import wraps
# from app import datetime, Share, desc, Mail, Message, Cache, SQLAlchemy, session, request, flash, render_template, redirect, url_for, Markup

# ------------------------------------------------------------------
# helper functions to clean up app.py / view file

def get_datetime_today():
	now = datetime.datetime.now()
	today = datetime.date(now.year, now.month, now.day)
	return today

# Converts numbers to $---,---,---.-- format and returns as string.
def pretty_numbers(value):
	return '${:,.2f}'.format(value)

def pretty_ints(value):
	return '{:,}'.format(value)

def pretty_percent(value):
	return '{:,.2f}%'.format(value)

def pretty_leaders(leaders):
	for l in leaders:
		l.prettyvalue = pretty_numbers(l.value)
	return leaders

# Determines the color for gains/loses by passing a boolean value
# to the html template
def set_color(change):
	if float(change) < 0.000000:
		return True
	else:
		return False

# cache
def get_leaderboard(user):
	allplayers = Portfolio.query.order_by(desc(Portfolio.value)).all()
	leaders = Portfolio.query.order_by(desc(Portfolio.value)).limit(5).all()
	leaders = pretty_leaders(leaders)
	allplayers = pretty_leaders(allplayers)

	if user != None:
		user = User.query.filter_by(name=session['username']).first()
		# finding player's position in leaderboard
		for idx, val in enumerate(allplayers):
			if user.portfolio == val:
				user.rank = idx+1
	else:
		loggedin_user = None # needed?
		user = None
	return user, allplayers, leaders

def get_user():
	if 'username' in session:
		loggedin_user = session['username']
		user = session['username']
	else:
		loggedin_user = None
		user = None
	return user

# bypass? or cache?
def get_account_details(portfolio, positions):
	value = portfolio.cash
	total_gain_loss = float(0.00)
	total_cost = float(0.00)
	for p in positions:
		stock_lookup_and_write(p.symbol)
		p.value = Stock.query.filter_by(symbol=p.symbol).first().price*p.sharecount
		p.prettyvalue = pretty_numbers(p.value)
		p.prettycost = pretty_numbers(p.cost)
		value += p.value
		p.gain_loss = p.value - p.cost
		p.gain_loss_percent = p.gain_loss/p.cost*100
		if p.gain_loss <= 0.0000:
			p.loss = True
		p.prettygain_loss = pretty_numbers(p.gain_loss)
		total_gain_loss = float(p.gain_loss) + total_gain_loss
		total_cost = float(p.cost) + total_cost
		p.prettygain_loss_percent = pretty_percent(p.gain_loss_percent)
	portfolio.total_cost = total_cost
	portfolio.prettytotal_cost = pretty_numbers(total_cost)
	portfolio.value = value
	portfolio.prettyvalue = pretty_numbers(portfolio.value)
	portfolio.prettycash = pretty_numbers(portfolio.cash)
	portfolio.total_stock_value = portfolio.value - portfolio.cash
	portfolio.prettytotal_stock_value = pretty_numbers(portfolio.total_stock_value)
	portfolio.total_gain_loss = total_gain_loss
	portfolio.prettytotal_gain_loss = pretty_numbers(portfolio.total_gain_loss)
	if portfolio.total_cost != 0.00:
		portfolio.total_gain_loss_percent = portfolio.total_gain_loss/portfolio.total_cost*100
		portfolio.prettytotal_gain_loss_percent = pretty_percent(portfolio.total_gain_loss_percent)
	else:
		portfolio.total_gain_loss_percent = 0
		portfolio.prettytotal_gain_loss_percent = "0%"
	if portfolio.total_gain_loss < 0.00:
		portfolio.loss = True

	db.session.commit() # not necessary?
	return portfolio, positions

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

# bypass?
# @db_if_yahoo_fail
def get_Share(symbol):
	stock = Share(clean_stock_search(symbol))
	return stock

# Puts various attributes into 'stock' via different Share methods.
def set_stock_data(stock):
	stock.name = stock.data_set["Name"]
	stock.symbol = stock.data_set["Symbol"].upper()
	stock.exchange = stock.get_stock_exchange()
	stock.price = float(stock.get_price())
	stock.prettyprice = pretty_numbers(stock.price)
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
	stock.day_range = str(stock.day_high)+" - "+str(stock.day_low)
	stock.year_high = stock.get_year_high()
	stock.year_low = stock.get_year_low()
	stock.year_range = str(stock.year_high)+" - "+str(stock.year_low)
	stock.market_cap = stock.data_set["MarketCapitalization"]
	stock.peratio = stock.data_set["PERatio"]
	if stock.peratio != None:
		stock.prettyperatio = pretty_numbers(float(stock.peratio))
	else:
		stock.prettyperatio = None
	stock.div = stock.data_set["DividendYield"]
	# not sure why this is causing problems, commenting for now
	# stock.div = float(stock.div)
	stock.prettyex_div = stock.data_set['ExDividendDate']
	stock.ex_div = convert_yhoo_date(stock.data_set['ExDividendDate'])
	stock.prettydiv_pay = stock.data_set['DividendPayDate']
	stock.div_pay = convert_yhoo_date(stock.data_set['DividendPayDate'])
	stock.view_count = 1
	stock.loss = set_color(stock.change)
	return stock

def write_stock_to_db(stock):
	# Here, the input 'stock' argument is a stock object
	# which has been passed through the set_stock_data function.
	# it might be worth taking the commit()s outside of the function
	if Stock.query.filter_by(symbol=stock.symbol).first() == None:
		db.session.add(Stock(stock.symbol, stock.name, stock.exchange, stock.price, \
			stock.div, stock.ex_div, stock.div_pay, stock.market_cap, stock.view_count))
		db.session.commit()
	else:
		write_stock = Stock.query.filter_by(symbol=stock.symbol).first()
		write_stock.view_count += 1
		write_stock.price = stock.price
		write_stock.div_yield = stock.div
		write_stock.ex_div = stock.ex_div
		write_stock.div_pay = stock.div_pay
		write_stock.market_cap = stock.market_cap
		db.session.commit()

# Look up a stock based on a 'cleaned' input string
def stock_lookup_and_write(symbol):
	stock = set_stock_data(Share(symbol))
	write_stock_to_db(stock)
	return stock

# I don't think I've implemented this everywhere yet, need to review.
def search_company(symbol):
	symbol = "%"+symbol+"%"
	# results = Stock.query.filter(Stock.name.ilike(symbol)).first()
	results = Stock.query.filter(Stock.name.ilike(symbol)).all()

	return results

# Yahoo dates are strings that look like "8/12/2015"; we need to
# convert this into a python datetime format for the db. 
def convert_yhoo_date(yhoo_date):
	# argument yhoo_date should look like "8/6/2015" or None.
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

def trade(stock, share_amount, buy_or_sell, user, portfolio, positions):
	stock = set_stock_data(stock)
	write_stock_to_db(stock) # NOW?
	# get actual stock in db ##   WHY?
	stock = Stock.query.filter_by(symbol=stock.symbol).first()
	# price and total_cost should be float
	price = (stock.price) #I don't think this is strictly necessary.
	total_cost = float(share_amount*price)
	today = get_datetime_today()

	# 1 or -1 multiplier against share_amount
	if buy_or_sell == 'buy':
		# wants to buy
		bs_mult = 1
		total_cost = total_cost*bs_mult
		# check to see if user has enough cash available
		cash = float(portfolio.cash)

		if cash > total_cost:
			new_cash = cash - total_cost

			# for new positions in a given stock
			if portfolio.positions.filter_by(symbol=stock.symbol).first() == None:
				# create & write the new position
				position = Position(user.portfolio.id, stock.symbol, total_cost, total_cost, share_amount, None)
				db.session.add(position)
				db.session.commit()
				flash(" Opened position in " + stock.name + ".")
				# now create trade (need datetime object)
				trade = Trade(stock.symbol, position.id, user.portfolio.id, total_cost, share_amount, today, stock.div_yield, stock.ex_div, stock.div_pay)
				db.session.add(trade)
				# db.session.commit()
				flash("You bought " + str(share_amount) + " shares of " + stock.name + " at " + pretty_numbers(price) + " per share.")
				# adjusting user.portfolio.cash
				user.portfolio.cash = new_cash
				db.session.commit()
				flash("Cash adjusted: -" + pretty_numbers(total_cost))
			# for already existing positions
			elif user.portfolio.positions.filter_by(symbol=stock.symbol).all() != None:
				position = user.portfolio.positions.filter_by(symbol=stock.symbol).first()
				# found the position, now adjust share count. 
				trade = Trade(stock.symbol, position.id, user.portfolio.id, total_cost, share_amount, today, stock.div_yield, stock.ex_div, stock.div_pay)
				db.session.add(trade)
				flash("You bought " + str(share_amount) + " shares of " + stock.name + " at " + pretty_numbers(price) + " per share.")
				user.portfolio.cash = new_cash
				position.cost = float(position.cost) + total_cost
				position.value = float(position.value) + total_cost
				position.sharecount += share_amount
				db.session.commit()
		else:
			deficit = total_cost - cash
			flash("Sorry, that costs "+ pretty_numbers(total_cost) + ", which is " + pretty_numbers(deficit) + " more than you have available. Try buying fewer shares.")
	else:
		# wants to sell
		bs_mult = -1
		total_cost = total_cost*bs_mult
		# check to see if there are enough stocks in the user's position
		position = user.portfolio.positions.filter_by(symbol=stock.symbol).first()
		if position != None:
			if position.sharecount >= share_amount:
				trade = Trade(stock.symbol, position.id, user.portfolio.id, total_cost, -1*share_amount, today, stock.div_yield, stock.ex_div, stock.div_pay)
				db.session.add(trade)
				flash("You sold " + str(share_amount) + " shares of " + stock.name + " at " + pretty_numbers(stock.price) + " per share. Adding " + pretty_numbers(total_cost*-1) + " to your cash balance.")
				# update position
				user.portfolio.cash = float(user.portfolio.cash) - total_cost
				position.cost = float(position.cost) + total_cost
				position.value = float(position.value) + total_cost
				position.sharecount = position.sharecount + share_amount*bs_mult
				# I'll remove this one if I can figure out the bug with Heroku's db.
				db.session.commit()
				# close position if no more shares
				if position.sharecount == 0:
					try:
						db.session.delete(position)
						db.session.commit()
						flash("Your position in " + stock.name + " has been closed.")
					except:
						flash("Your position in " + stock.name + " is now empty. I'm working on a way to remove it from the database.")
			else:
				flash("You only have " + str(position.sharecount) + " shares of " + str(stock.symbol) + ". Try selling fewer shares.")
		else:
			flash("You don't have any shares of " + stock.symbol + " to sell.")

def new_user_email(user):
	msg = Message('Welcome to StockHawk, {}!'.format(user.name), sender=('Adam', config.BaseConfig.MAIL_USERNAME), recipients=[user.email])
	msg.html = "<h3>Hi %s,</h3><p>Thanks for registering an account with StockHawk. We've added $1,000,000 of play money to your account. <a href='http://stockhawk.herokuapp.com/login'>Sign in</a> and start trading!<br><br>Good luck!<br> - Adam</p>" % user.name
	mail.send(msg)

def reset_password_email(user):
	pass

def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('You need to log in first.')
			return redirect(url_for('login'))
	return wrap

def login_reminder(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			message = Markup("<a href='/login'>Sign in</a> or <a href='/register'>register</a> to play.")
			flash(message)
			return f(*args, **kwargs)	
	return wrap

# Started, but not finished this decorator. I need to think about if it makes sense to implement this. There might be use cases for a similar decorator to limit trading times/days, but again, that might not serve a purpose.

# def after_hours_mode(f):
# 	@wraps(f)
# 	def wrap(*args, **kwargs):
# 		now = datetime.datetime.utcnow()
# 		if now.weekday() >= 5:
# 			#don't allow queries UNLESS the stock is NOT in db
# 			pass
# 		else:
# 			return f(*args, **kwargs)
# 	return wrap


# If there's no connectivity to yahoo-finance api, bypass and query db instead, but also indicate this to user
# def db_if_yahoo_fail(f):
# 	@wraps(f)
# 	def wrap(*args, **kwargs):
# 		try:
# 			f(*args, **kwargs)
# 			return flash('hi')
# 		except:
# 			flash("Couldn't connect to yahoo-finance API, getting quotes from database.")
# 			# return search_company(*args)
# 			return redirect(url_for('news'))
# 	return wrap

# -------------------------------------------------------
