from flask import Flask, render_template, redirect, url_for, request, session, flash, Markup
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cache import Cache
from flask.ext.mail import Mail, Message
# from celery import Celery
from sqlalchemy import desc
from yahoo_finance import Share
from forms import StockSearchForm, LoginForm, RegisterForm, PasswordReminderForm, PasswordResetForm, DeleteAccountForm, TradeForm, FullTradeForm
import datetime
import os
import config

# for plotting
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
import pandas as pd
from numpy import pi

# from helpers import get_datetime_today, pretty_numbers, pretty_ints, pretty_percent, pretty_leaders, get_leaderboard, get_user, get_account_details, clean_stock_search, get_Share, set_stock_data, write_stock_to_db, stock_lookup_and_write, search_company, convert_yhoo_date, trade

# --------------------------------------------------------------------
# Instatiate and configure app, db, cache, mail, celery, etc.:
app = Flask(__name__)

# app.config.from_object('config.DevConfig')
app.config.from_object(os.environ['APP_SETTINGS'])

cache = Cache(app)

mail = Mail(app)

# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)
 
db = SQLAlchemy(app)
# Import db models to be used, AFTER creating db or it fails!
from models import *

# ------------------------------------------------------------------
# helper functions to clean up app.py / view file

def get_datetime_today():
	now = datetime.datetime.now()
	today = datetime.date(now.year, now.month, now.day)
	return today

# Converts numbers to more readable financial formats
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
	portfolio.daily_gain = 0.000
	for p in positions:
		# stock_lookup_and_write(p.symbol) # unfactoring to use stock.stuff
		stock = set_stock_data(Share(p.symbol))
		write_stock_to_db(stock)
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
		p.daily_gain = float(stock.change)*p.sharecount
		p.prettydaily_gain = pretty_numbers(p.daily_gain) 
		if p.daily_gain <= 0.0000:
			p.daily_gain_loss = True
		portfolio.daily_gain += p.daily_gain
	portfolio.prettydaily_gain = pretty_numbers(portfolio.daily_gain)
	if portfolio.daily_gain <= 0.0000:
		portfolio.daily_gain_loss = True
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

def prepare_stock_graph(symbol, start, end):
	
	stock = Share(symbol)
	stringprices = list(pd.DataFrame(stock.get_historical(start,end))['Adj_Close'])
	stringdates = list(pd.DataFrame(stock.get_historical(start, end))['Date'])
	
	prices = [float(p) for p in stringprices]
	dates = []    
	
	for d in stringdates:
	    year, month, day = d.split('-')
	    d = datetime.date(int(year), int(month), int(day))
	    dates.append(d)

	return prices, dates

def build_portfolio_pie(portfolio, positions):
	percent_base = 0.00
	percents = [percent_base]
	for p in positions:
		p.position_value_percentage = float(p.value)/float(portfolio.value-portfolio.cash)
		percent_base = percent_base + float(p.position_value_percentage) 
		percents.append(percent_base)
	# percents.append(float(portfolio.cash)/float(portfolio.value))
	stocknames = [p.symbol for p in positions]
	# stocknames = stocknames.append('Cash')

	starts = [float(p)*2*pi for p in percents[:-1]]
	ends = [float(p)*2*pi for p in percents[1:]]
	# ends.append(starts[:-1])
	color_palette = ['aqua', 'aquamarine', 'cadetblue', 'chartreuse', 'cornflowerblue','darkslateblue', 'darkslategray', 'deepskyblue','dodgerblue','lawngreen', 'lightblue', 'lightcyan', 'lightseagreen', 'lightsteelblue', 'mediumaquamarine','mediumblue','mediumseagreen', 'blue', 'green', 'navy','indigo','purple','cyan','darkblue','darkcyan','darkseagreen', 'darkturquoise', 'forestgreen','mediumturquoise']
	colors = [color_palette[n] for n in range(0,len(percents))]

	p = figure(x_range=(-1.1,1.85), y_range=(-1,1), title='Stock positions', toolbar_location='below', tools='', width=420, plot_height=320)

	for n in range(0,len(positions)):
		p.wedge(x=0, y=0, radius=1, start_angle=starts[n], end_angle=ends[n], color=colors[n], legend=stocknames[n])

	p.xgrid.grid_line_color = None
	p.ygrid.grid_line_color = None
	p.xaxis.major_tick_line_color = None
	p.xaxis.minor_tick_line_color = None
	p.yaxis.major_tick_line_color = None
	p.yaxis.minor_tick_line_color = None
	p.outline_line_color = None

	script, div = components(p)
	return script, div, colors

def build_stock_plot(symbol, dates, prices):
    average_price = float(sum(prices))/len(prices)
    average_dates = [0 for n in prices]
    first_price = prices[-1]

    p = figure(width=610, plot_height=300, tools='pan,box_zoom,reset', title='1 month period', x_axis_label=None, x_axis_type='datetime', y_axis_label='$ per share', toolbar_location='below')
    p.line(dates, prices, color='navy', alpha=0.9, line_width=2, legend=symbol.upper())
    p.line(dates, average_price, color='orange', legend='Average', alpha=0.4, line_width=1.5)
    # p.line(dates, first_price, color='red', legend='Starting', alpha=0.4, line_width=1.5)

    p.ygrid.minor_grid_line_color = 'navy'
    p.ygrid.minor_grid_line_alpha = 0.1
    p.legend.orientation = 'top_left'
    p.legend.label_text_font = 'Helvetica'

    script, div = components(p)
    return script, div

# === decorator and email imports ======
from decorators import *
from emails import send_async_email, send_email, new_user_email, password_reminder_email, password_reset_email
# Importing email functions here since they use the above decorator.

#=== views ====================
@app.errorhandler(404)
def not_found(e):
	flash('Resource not found.')
	user = get_user()
	return render_template('/404.html', loggedin_user=user)

@app.route('/about')
@login_reminder
def about():
	title = 'About StockHawk'
	user = get_user()
	return render_template('index.html', title=title, loggedin_user=user)

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
				port = Portfolio(user.id, 1000000, 1000000)
				db.session.add(port)
				db.session.commit()

				session['logged_in'] = True
				session['username'] = user.name
				flash('Thanks for registering!')
				flash('$1,000,000.00 was added to your account.')
				new_user_email(user)
				return redirect(url_for('user'))
			else:
				flash('That email is already registered with a user. Please log in or register another user.')
				return redirect(url_for('register'))
		else:
			flash('That user name already exists.')
			return redirect(url_for('register'))
	elif request.method == 'POST' and not form.validate():
		flash('Try again.')
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
				user.last_seen = datetime.datetime.now()
				db.session.commit()
				return redirect(url_for('user'))
			else:
				flash('Incorrect password for that user name, please try again.')
				return redirect(url_for('login'))
		else:
			# Allowing the user to sign in using email.
			user = User.query.filter_by(email=form.username.data).first()
			if user != None:

				userpw = user.password
				if userpw == form.password.data:
					session['logged_in'] = True
					session['username'] = user.name
					flash('You were just logged in.')			
					user.last_seen = datetime.datetime.now()
					db.session.commit()
					return redirect(url_for('user'))
			else:
				flash('That user name does not exist in our system. Please try again or sign up for a new account.')
				return redirect(url_for('login'))
		return render_template('login.html', form=form, error=error, title=title)
	elif request.method == 'POST' and not form.validate():
		flash('Invalid username or password. Try again or register a new account.')
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

@app.route('/password_reminder', methods=['GET', 'POST'])
def password_reminder():
	error = None
	form = PasswordReminderForm(request.form)
	title = "Forgot your password?"	

	if request.method == 'POST' and form.validate():
		user = User.query.filter_by(name=form.username.data).first()
		if user != None:
			password_reminder_email(user)
			flash("Sent reminder email to "+user.name+"'s email address. Please check your inbox and sign in. Check your spam folder if you don't see our email within a couple of minutes.")
			return redirect(url_for('login'))
		else:
			# Allowing the user to sign in using email.
			user = User.query.filter_by(email=form.username.data).first()
			if user != None:
				password_reminder_email(user)
				flash("Sent reminder email to "+user.email+". Please check your inbox and sign in. Check your spam folder if you don't see our email within a couple of minutes.")
				return redirect(url_for('login'))
			else:
				flash("We couldn't find any user with that username or email address. Please try a different name/address or register a new account.")

	elif request.method == 'POST' and not form.validate():
		flash('Invalid username or password. Try again or register a new account.')
		return redirect(url_for('password_reminder'))
	
	# elif request.method == 'GET':
	return render_template('password_reminder.html', form=form, title=title, error=error)

@app.route('/db_view')
@login_reminder
# @cache.cached(timeout=40)
# unless I figure out a better way, I can't cache user pages. Two concurrent users are able to see the other's page if it's in cache!
def db_view():
	title = "Under the hood"
	user = get_user()
	stocks = Stock.query.all()
	users = User.query.all()
	trades = Trade.query.all()
	portfolios = Portfolio.query.all()
	positions = Position.query.all()
	return render_template("db_view.html", title=title, stocks=stocks, users=users, trades=trades, positions=positions, portfolios=portfolios, loggedin_user=user)

@app.route('/aboutadam')
def aboutadam():
	return render_template('aboutadam.html')

@app.route('/tos')
def tos():
	return render_template('tos.html')

@app.route('/news')
@login_reminder
def news():
	title = 'Release log'
	user = get_user()
	return render_template('news.html', title=title, loggedin_user=user)

@app.route('/leaderboard')
@login_reminder
def leaderboard():
	title = "Leaderboard"
	flash("This page is under development. It will look nicer soon!")
	loggedin_user = get_user()
	user, allplayers, leaders = get_leaderboard(loggedin_user)

	return render_template('leaderboard.html', title=title, leaders=allplayers, loggedin_user=loggedin_user)

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user():
	today = get_datetime_today()
	form = FullTradeForm(request.form)
	loggedin_user = get_user() 
	user = User.query.filter_by(name=session['username']).first()
	title = user.name+"'s account summary"
	portfolio = user.portfolio
	positions = portfolio.positions.all()
	for p in positions:
		p.prettysharecount = pretty_ints(p.sharecount)

	if request.method == 'GET':
		# refresh current stock prices and therefore account value
		portfolio, positions = get_account_details(portfolio, positions)


		script, div, colors = build_portfolio_pie(portfolio, positions)

		return render_template('account.html', title=title, user=user, portfolio=portfolio, form=form, loggedin_user=loggedin_user, positions=positions, script=script, div=div, colors=colors)
	elif request.method == 'POST' and form.validate():
		stock = get_Share(form.symbol.data)
		# stock = Share(clean_stock_search(form.symbol.data))
		share_amount = form.share_amount.data
		buy_or_sell = form.buy_or_sell.data
		if stock.get_price() == None:
			# If it's POST and valid, but there's no such stock
			flash("Couldn't find stock matching "+form.symbol.data.upper()+". Try another symbol.")
			return redirect(url_for('user'))
		else:
			# if it's POSTed, validated, and there actually is a real stock
			trade(stock, share_amount, buy_or_sell, user, portfolio, positions)
			return redirect(url_for('user'))
	elif request.method == 'POST' and not form.validate():
		flash('Invalid values. Please try again.')
		return redirect(url_for('user'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
	loggedin_user = get_user()
	user, allplayers, leaders = get_leaderboard(loggedin_user)
	form = PasswordResetForm(request.form)
	deleteform = DeleteAccountForm(request.form)
	title = "{}'s account settings".format(user.name)

	if request.method == 'POST' and form.validate():
		if form.old_password.data == user.password:
			flash("Your password has been reset.")
			user.password = form.new_password.data
			db.session.commit()
			password_reset_email(user)
			return redirect(url_for('user'))
		else:
			flash("Your old password was incorrect. Please try again.")
			return redirect(url_for('settings'))

	elif request.method == 'POST' and not form.validate():
		flash("Something went wrong; please try again.")
		return redirect(url_for('settings'))

	else:
		return render_template('settings.html', title=title, loggedin_user=loggedin_user, user=user, form=form, deleteform=deleteform)

@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
	deleteform = DeleteAccountForm(request.form)
	loggedin_user = get_user()
	user, allplayers, leaders = get_leaderboard(loggedin_user)

	if request.method == 'POST' and deleteform.validate():
		if deleteform.confirm.data.upper() == 'DELETE':
			db.session.delete(user)
			db.session.commit()
			flash("Your account has been deleted.")
			return redirect(url_for('logout'))
		else:
			flash('Type "DELETE" in the field below if you are sure you want to delete your account; this cannot be undone.')
			return redirect(url_for('settings'))
	elif request.method == 'POST' and not deleteform.validate():
		flash('Type "DELETE" in the field below if you are sure you want to delete your account; this cannot be undone.')
		return redirect(url_for('settings'))

@app.route('/', methods=['GET', 'POST'])
@login_reminder
def stocks():
	title = 'StockHawk'	
	stock = None
	loggedin_user = get_user()
	user, allplayers, leaders = get_leaderboard(loggedin_user)
	form = StockSearchForm(request.form)
	tradeform = TradeForm(request.form)	
	stocks = Stock.query.order_by(desc(Stock.view_count)).limit(10).all()
	if request.method == 'POST':
		if form.validate():
			stock = get_Share(form.stocklookup.data)
			# stock = Share(clean_stock_search(form.stocklookup.data))
			if stock.data_set['Open'] == None:
			# company lookup goes here
				company_results = search_company(form.stocklookup.data)
				stock = None
				if len(company_results) == 0:
					flash("Couldn't find symbol or company matching "+form.stocklookup.data.upper()+". Try searching for something else.")
				else:
					flash("Didn't find that symbol, but found " + str(len(company_results)) +" matching company names:")

				return render_template('stocks.html', stock=stock, form=form, stocks=stocks, leaders=leaders, user=user, loggedin_user=loggedin_user, results=company_results)
			else:
				# There is a stock with this symbol, serve the dynamic page
				stock = set_stock_data(stock)
				# Some stocks appear to not have company names
				if stock.name != None:
					title = stock.symbol+" - "+stock.name
				else:
					title = stock.symbol+" - Unnamed company"
				write_stock_to_db(stock)
				return redirect(url_for('stock', symbol=stock.symbol))
		elif not form.validate():
			flash("Please enter a stock.")
			return redirect(url_for('stocks'))
		return render_template('stocks.html', form=form, tradeform=tradeform, stock=stock, leaders=leaders, title=title, user=user, loggedin_user=loggedin_user)
	elif request.method == 'GET':
		for s in stocks:
			s.prettyprice = pretty_numbers(s.price)
		return render_template('stocks.html', form=form, tradeform=tradeform, stock=stock, stocks=stocks, leaders=leaders, title=title, user=user, loggedin_user=loggedin_user)

@app.route('/<symbol>', methods=['GET', 'POST'])
def stock(symbol):
	stock = get_Share(symbol)
	if stock.data_set['Open'] == None:
		# flash("Couldn't find that stock. Try another symbol.")
		stock = None
		return redirect(url_for('stocks'))
	else:
		# you wrote a function for these two lines, replace here!
		stock = set_stock_data(Share(symbol))
		write_stock_to_db(stock)
		### ^^
	title = stock.name
	loggedin_user = get_user()
	user, allplayers, leaders = get_leaderboard(loggedin_user)
	
	form = StockSearchForm(request.form)
	tradeform = TradeForm(request.form)	
	stocks = Stock.query.order_by(desc(Stock.view_count)).limit(10).all()

	if user != None:
		portfolio = user.portfolio
		portfolio.prettycash = pretty_numbers(portfolio.cash)
		# This is to show many shares much of that particular stock a user has in his/her position.
		positions = portfolio.positions
		position = portfolio.positions.filter_by(symbol=symbol).first()
		if position:
			position.prettysharecount = pretty_ints(position.sharecount)
	else:
		portfolio = None
		position = None
		positions = None

	if request.method == 'POST' and tradeform.validate():
		share_amount = tradeform.amount.data
		buy_or_sell = tradeform.buy_or_sell.data
		if stock.get_price() == None:
			# If it's POST and valid, but there's no such stock
			flash("Couldn't find stock matching "+symbol.upper()+". Try another symbol.")
			return redirect(url_for('stocks'))
		else:
			# if it's POSTed, validated, and there is a real stock
			trade(stock, share_amount, buy_or_sell, user, portfolio, positions)
			return redirect(url_for('user'))

	elif request.method == 'POST' and not tradeform.validate():
		flash("Invalid share amount; please try again.")
		return redirect(url_for('stocks'))

	if request.method == 'GET':
		start = '2015-09-30'
		end = '2015-10-31'
		prices, dates = prepare_stock_graph(symbol, start, end)
		script, div = build_stock_plot(symbol, dates, prices)

	return render_template('stock.html', form=form, tradeform=tradeform, stock=stock, stocks=stocks, leaders=leaders, title=title, user=user, loggedin_user=loggedin_user, position=position, script=script, div=div)

if __name__ == '__main__':
	app.run()
