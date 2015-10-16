from flask import Flask, render_template, redirect, url_for, request, session, flash
from functools import wraps
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from yahoo_finance import Share
from forms import StockSearchForm, LoginForm, RegisterForm, TradeForm, FullTradeForm
import datetime
import os
import config
# from helpers import set_color, clean_stock_search, set_stock_data, convert_yhoo_date, write_stock_to_db

# --------------------------------------------------------------------

# Instatiate and configure app:
app = Flask(__name__)

app.config.from_object('config.ProdConfig')

# ------------------------------------------------------------------

# create sqlalchemy object 
db = SQLAlchemy(app)

# Import db models to be used, AFTER creating db or it fails!
from models import *

# ------------------------------------------------------------------

# helper functions to clean up app.py / view file

def pretty_numbers(value):
	return '${:,.2f}'.format(value)

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

# This is to take out non-numeric characters from an integer input string.
def clean_int_input(number):
	punctuation = '''!()-[]{ };:'"\,<>./?@#$%^&*_~qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'''
	no_punct = ""
	for char in number:
		if char not in punctuation:
			no_punct = no_punct + char
			# no_punct = int(no_punct)
# what to do if there aren't any numeric characters in the field
		elif len(no_punct) == 0:
			no_punct = 0
			flash('Invalid quantity. Please try again.')
	no_punct = int(no_punct)
	return no_punct

# Puts various attributes into 'stock' via different Share methods.
def set_stock_data(stock):
	stock.name = stock.data_set["Name"]
	stock.symbol = stock.data_set["Symbol"].upper()
	stock.exchange = stock.get_stock_exchange()
	stock.price = stock.get_price()
	stock.price = float(stock.price)
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
	# not sure why this is causing problems, commenting for now
	# stock.div = float(stock.div)
	stock.ex_div = stock.data_set['ExDividendDate']
	stock.ex_div = convert_yhoo_date(stock.ex_div)
	stock.div_pay = stock.data_set['DividendPayDate']
	stock.div_pay = convert_yhoo_date(stock.div_pay)
	stock.view_count = 1
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
		db.session.add(Stock(stock.symbol, stock.name, stock.exchange, stock.price, \
			stock.div, stock.ex_div, stock.div_pay, stock.market_cap, stock.view_count))
		db.session.commit()
	else:
		# # need to convert these to datetimes
		# stock.ex_div = convert_yhoo_date(stock.ex_div)
		# stock.div_pay = convert_yhoo_date(stock.div_pay)

		write_stock = Stock.query.filter_by(symbol=stock.symbol).first()
		write_stock.view_count += 1
		write_stock.price = stock.price
		write_stock.div_yield = stock.div
		write_stock.ex_div = stock.ex_div
		write_stock.div_pay = stock.div_pay
		write_stock.market_cap = stock.market_cap

		# need to update price, div_yield, ex_div, div_pay, market_cap in db as well
		db.session.commit()

# login required decorator
def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('You need to log in first.')
			return redirect(url_for('login'))
	return wrap

# -------------------------------------------------------

# views

@app.errorhandler(404)
def not_found(e):
	flash('Resource not found.')
	if 'username' in session:
		loggedin_user = session['username']
	else:
		loggedin_user = None
	return render_template('/404.html', loggedin_user=loggedin_user)

@app.route('/')
def home():
	title = 'About StockHawk'
	if 'username' in session:
		loggedin_user = session['username']
	else:
		loggedin_user = None
	return render_template('index.html', title=title, loggedin_user=loggedin_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
	title = 'Register a new account'
	form = RegisterForm(request.form)

	if request.method == 'POST' and form.validate():
		now = datetime.datetime.now()
		username = form.username.data.lower()
		email = form.email.data
		password = form.password.data
		if User.query.filter_by(name=username).first() == None:
			if User.query.filter_by(email=email).first() == None:
				user = User(username, email, password, now)
				db.session.add(user)
				db.session.commit()

				# create portfolio for the user at the same time
				port = Portfolio(user.id, 1000000)
				db.session.add(port)
				db.session.commit()

				session['logged_in'] = True
				flash('Thanks for registering!')
				flash('$1,000,000.00 was added to your account.')
				flash('Please log in using your credentials.')	
				return redirect(url_for('stocks'))
			else:
				flash('That email is already registered with a user. Please log in or register another user.')
				return redirect(url_for('register'))
		else:
			flash('That user name already exists.')
			return redirect(url_for('register'))
	elif request.method == 'POST' and not form.validate():
		flash('Try again.')
		# return redirect(url_for('register'))
	elif request.method == 'GET':
		return render_template('register.html', title=title, form=form)
	return render_template('register.html', title=title, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	form = LoginForm(request.form)
	title = 'Login'

	if request.method == 'POST' and form.validate():
		user = User.query.filter_by(name=form.username.data).first()
		if user != None:
			userpw = user.password
			if userpw == form.password.data:
				session['logged_in'] = True
				# experiment
				session['username'] = request.form['username'] 
				flash('You were just logged in.')			
				user = User.query.filter_by(name=user.name).first()
				user.last_seen = datetime.datetime.now()
				db.session.commit()
				return redirect(url_for('user'))
			else:
				flash('Incorrect password for that user name, please try again.')
				return redirect(url_for('login'))
		else:
			flash('That user name does not exist in our system. Please try again or sign up for a new account.')
			return redirect(url_for('login'))
		return render_template('login.html', form=form, error=error, title=title)
	elif request.method == 'POST' and not form.validate():
		flash('Invalid username or password. Try again, or register a new account')
		return redirect(url_for('login'))
	elif request.method == 'GET':
		return render_template('login.html', form=form, error=error, title=title)

@app.route('/logout')
@login_required
def logout():
	session.pop('logged_in', None)
	session.pop('username', None)
	flash('You were just logged out.')
	return redirect(url_for('stocks'))

@app.route('/db_view')
def db_view():
	title = "Under the hood"

	if 'username' in session:
		loggedin_user = session['username']
	else:
		loggedin_user = None

	stocks = Stock.query.all()
	users = User.query.all()
	trades = Trade.query.all()
	portfolios = Portfolio.query.all()
	positions = Position.query.all()

	return render_template("db_view.html", title=title, stocks=stocks, users=users, trades=trades, positions=positions, portfolios=portfolios, loggedin_user=loggedin_user)

@app.route('/welcome')
def welcome():
	title = 'Welcome'

	if 'username' in session:
		loggedin_user = session['username']
	else:
		loggedin_user = None

	return render_template('welcome.html', title=title, loggedin_user=loggedin_user)

@app.route('/tos')
def tos():
	return render_template('tos.html')

@app.route('/news')
def news():
	title = 'News'

	if 'username' in session:
		loggedin_user = session['username']
	else:
		loggedin_user = None

	return render_template('news.html', title=title, loggedin_user=loggedin_user)

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user():
	form = FullTradeForm(request.form)
	if 'username' in session:
		loggedin_user = session['username']
		user = User.query.filter_by(name=session['username']).first()
		title = session['username']+"'s account"
	else:
		return redirect(url_for('login'))

	if request.method == 'GET':
		# find the user's portfolio and positions
		# later, I'll write a function to update the values for both
		portfolio = user.portfolio
		positions = portfolio.positions.all()
	
		# getting the cash and adding values of the positions below
		value = user.portfolio.cash
		for p in positions:
			value += p.value
		value = pretty_numbers(value)
		cash = pretty_numbers(user.portfolio.cash)
		for p in positions:
			p.prettyvalue = pretty_numbers(p.value)

		return render_template('account.html', title=title, user=user, cash=cash, value=value, form=form, loggedin_user=loggedin_user, positions=positions)
	
	elif request.method == 'POST' and form.validate():
		stock = Share(clean_stock_search(form.symbol.data))
		# stock = set_stock_data(stock)
		if stock.get_price() == None:
			# If it's POST, valid, but there's no such stock
			flash("Couldn't find stock matching "+form.symbol.data.upper()+". Try another symbol.")
			stock = None
			return redirect(url_for('user'))
		else:
			# if it's POSTed, validated, and there actually is a real stock
			stock = set_stock_data(stock)
			# let's capture the latest data on the stock in the db
			write_stock_to_db(stock)
			# get actual stock in db
			stock = Stock.query.filter_by(symbol=stock.symbol).first()
			# clean and turn into int
			share_amount = clean_int_input(form.share_amount.data)
			# price and total_cost should be float
			price = (stock.price)
			total_cost = float(share_amount*price)

			# accept buy_or_sell from FullTradeForm, assign 1 or -1 multiplier
			buy_or_sell = form.buy_or_sell.data
			if buy_or_sell == 'buy':
				bs_mult = 1
				# check to see if user has enough cash available
				cash = float(user.portfolio.cash)

				if cash > total_cost:
					can_buy = True
					new_cash = cash - total_cost

					# for new positions in a given stock
					if user.portfolio.positions.filter_by(symbol=stock.symbol).first() == None:
						# create & write the new position
						position = Position(user.portfolio.id, stock.symbol, total_cost, total_cost, share_amount, None)
						db.session.add(position)
						db.session.commit()
						flash(" Opened position in " + stock.name + ".")

						# now create trade (need datetime object)
						now = datetime.datetime.now()
						today = datetime.date(now.year, now.month, now.day)
						trade = Trade(stock.symbol, position.id, user.portfolio.id, total_cost, share_amount, today, stock.div_yield, stock.ex_div, stock.div_pay)
						db.session.add(trade)
						# db.session.commit()
						flash("You bought " + str(share_amount) + " shares of " + stock.name + " at " + pretty_numbers(price) + " per share.")
						# adjusting user.portfolio.cash
						user.portfolio.cash = new_cash
						db.session.commit()
						flash("Cash adjusted: -" + pretty_numbers(total_cost))

						# pos = " Opened position in " + stock.symbol

					elif user.portfolio.positions.filter_by(symbol=stock.symbol).all() != None:
						# flash("You already have a position in " + stock.symbol + ".")
						position = user.portfolio.positions.filter_by(symbol=stock.symbol).first()
						# found the position, now adjust share count. maybe should do this via Trade?

						now = datetime.datetime.now()
						today = datetime.date(now.year, now.month, now.day)
						trade = Trade(stock.symbol, position.id, user.portfolio.id, total_cost, share_amount, today, stock.div_yield, stock.ex_div, stock.div_pay)
						db.session.add(trade)
						flash("You bought " + str(share_amount) + " shares of " + stock.name + " at $" + str(price) + " per share.")
						
						user.portfolio.cash = new_cash
						position.cost = float(position.cost) + total_cost
						position.value = float(position.value) + total_cost
						position.sharecount += share_amount

						db.session.commit()
						flash('Cash, position cost, value, sharecount adjusted.')

				else:
					can_buy = False
					deficit = total_cost - cash
					flash("Sorry, that costs "+ pretty_numbers(total_cost) + ", which is $" + str(deficit) + " more than you have available. Try buying fewer shares.")
			else:
				bs_mult = -1
				# check to see if there are enough stocks in the 
				# position for this user's portfolio
				# positions = str(user.portfolio.positions.trades.symbol_id)
				# output = "Make sure you have enough shares to sell. Going to work on buys for now"
				flash("Selling is not yet implemented, try again tomorrow!")

			return redirect(url_for('user'))

	elif request.method == 'POST' and not form.validate():
		flash('Invalid values. Please try again.')
		return redirect(url_for('user'))

# This is to dynamically create pages/urls/views for each stock queried.
# Leaving it out for now, as it gets a little complicated with the db writes.
# @app.route('/stock/<symbol>')
# def stock(symbol):
# 	stock = Share(symbol)
# 	return render_template('stock.html', stock=stock, symbol=symbol)

@app.route('/trade', methods=['GET', 'POST'])
@login_required
def trade():
	tradeform = TradeForm(request.form)

	flash('I have not yet set up trading via the stock page. Try it from the user page.')

	# if 'username' in session:
	# 	loggedin_user = session['username']
	# else:
	# 	loggedin_user = None 

	# return redirect(url_for('user'))
	return redirect(url_for('user'))

@app.route('/stocks', methods=['GET', 'POST'])
def stocks():
	title = 'StockHawk'	
	stock = None
	form = StockSearchForm(request.form)
	tradeform = TradeForm(request.form)

	if 'username' in session:
		loggedin_user = session['username']
	else:
		loggedin_user = None 

	if request.method == 'POST':
		if form.validate():
			stock = Share(clean_stock_search(form.stocklookup.data))
			if stock.get_price() == None:
				flash("Couldn't find stock matching '"+form.stocklookup.data.upper()+"'. Try another symbol.")
				stock = None
				return redirect(url_for('stocks'))
			else:
				# the form is valid and there is a real stock

				# Boolean value, sent to template for conditional css formatting.
				loss = set_color(float(stock.get_change()))
				# setting up the stock object for display and writing to db.
				stock = set_stock_data(stock)
				# Some stocks appear to not have company names; this just identifies them as such.
				# Note, this might be a problem in the database since name is not nullable and is unique
				if stock.name != None:
					title = stock.symbol+" - "+stock.name
				else:
					title = stock.symbol+" - Unnamed company"
				# need to convert these into python datetime objects
				write_stock_to_db(stock)

				return render_template('stocks.html', form=form, tradeform=tradeform, stock=stock, title=title, loss=loss, loggedin_user=loggedin_user)
		elif not form.validate():
			flash("Please enter a stock.")
			return redirect(url_for('stocks'))
		return render_template('stocks.html', form=form, tradeform=tradeform, stock=stock, title=title, loss=loss, loggedin_user=loggedin_user)
	elif request.method == 'GET':
		stocks = Stock.query.order_by(desc(Stock.view_count)).limit(10).all()
		for s in stocks:
			s.prettyprice = pretty_numbers(s.price)
		return render_template('stocks.html', form=form, tradeform=tradeform, stock=stock, stocks=stocks, title=title, loggedin_user=loggedin_user)

if __name__ == '__main__':
	app.run()
