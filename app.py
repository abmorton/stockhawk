from flask import Flask, render_template, redirect, url_for, request, session, flash
from functools import wraps
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from yahoo_finance import Share
from forms import StockSearchForm, LoginForm, RegisterForm
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
		stock_vc = Stock.query.filter_by(symbol=stock.symbol).first()
		stock_vc.view_count += 1
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

@app.route('/')
def home():
	title = 'StockHawk'
	return render_template('index.html', title=title)

@app.route('/register', methods=['GET', 'POST'])
def register():
	title = 'Register a new account'
	form = RegisterForm(request.form)

	if request.method == 'POST' and form.validate():
		now = datetime.datetime.now()
		username = form.username.data
		email = form.email.data
		password = form.password.data
		if User.query.filter_by(name=username).first() == None:
			if User.query.filter_by(email=email).first() == None:
				user = User(username, email, password, now)
				db.session.add(user)
				db.session.commit()
				session['logged_in'] = True
				flash('Thanks for registering!')
				flash('You were just logged in.')	
				return redirect(url_for('user'))
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
				# this line might break some logic.
				# session['user'] = user
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
	flash('You were just logged out.')
	return redirect(url_for('home'))

@app.route('/db_view')
def db_view():
	title = 'Database preview'
	stocks = Stock.query.order_by(desc(Stock.view_count))
	users = User.query.order_by(desc(User.last_seen))
	return render_template("db_view.html", title=title, stocks=stocks, users=users)

@app.route('/welcome')
def welcome():
	title = 'Welcome'
	return render_template('welcome.html', title=title)

@app.route('/tos')
def tos():
	return render_template('tos.html')

@app.route('/news')
def news():
	title = 'News'
	return render_template('news.html', title=title)

@app.route('/user')
@login_required
def user():
	title = 'Account'
	# this line might break some logic.
	# user = session['user']
	return render_template('account.html', title=title, user=user)

# This is to dynamically create pages/urls/views for each stock queried.
# Leaving it out for now, as it gets a little complicated with the db writes.
# @app.route('/stock/<symbol>')
# def stock(symbol):
# 	stock = Share(symbol)
# 	return render_template('stock.html', stock=stock, symbol=symbol)

@app.route('/stocks', methods=['GET', 'POST'])
def stocks():
	title = 'Stock lookup'	
	stock = None
	form = StockSearchForm(request.form)

	if request.method == 'POST':
		if form.validate():
			stock = Share(clean_stock_search(form.stocklookup.data))
			if stock.get_price() == None:
				flash("Couldn't find stock matching '"+form.stocklookup.data.upper()+"'. Try another symbol.")
				stock = None
				return redirect(url_for('stocks'))
			else:
				# Boolean value, sent to template for conditional css formatting.
				loss = set_color(float(stock.get_change()))
				# setting up the stock object for display and writing to db.
				stock = set_stock_data(stock)
				if stock.name != None:
					title = stock.symbol+" - "+stock.name
				else:
					title = stock.symbol+" - Unnamed company"
				# need to convert these into python datetime objects
				stock.ex_div = convert_yhoo_date(stock.ex_div)
				stock.div_pay = convert_yhoo_date(stock.div_pay)
				write_stock_to_db(stock)
				return render_template('stocks.html', form=form, stock=stock, title=title, loss=loss)
		else:
			flash("Please enter a stock.")
			return redirect(url_for('stocks'))	
		return render_template('stocks.html', form=form, stock=stock, title=title, loss=loss)
	elif request.method == 'GET':
		stocks = Stock.query.order_by(desc(Stock.view_count)).limit(10).all()
		return render_template('stocks.html', form=form, stock=stock, stocks=stocks, title=title)

if __name__ == '__main__':
	app.run()
