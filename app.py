from flask import Flask, render_template, redirect, url_for, request, session, flash
from functools import wraps
from flask.ext.sqlalchemy import SQLAlchemy
from yahoo_finance import Share
from forms import StockSearchForm, LoginForm

app = Flask(__name__)


# config data, to be moved later
app.secret_key = 'myohmy'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///practice.db'
app.debug = False

# create sqlalchemy object 

db = SQLAlchemy(app)

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

# helper functions

# This is to output conditional formatting into the stocks.html template.
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

# views

@app.route('/')
# @login_required
def home():
	title = 'StockHawk'
	return render_template('index.html', title=title)

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	form = LoginForm(request.form)
	title = 'StockHawk - Login'

	if request.method == 'POST':
		# if (request.form['username'] != 'admin') or (request.form['password'] != 'admin'):
		if (form.username.data != 'admin') or (form.password.data != 'admin'):
			error = 'Invalid credentials. Please enter username and password.'
		else:
			session['logged_in'] = True
			flash('You were just logged in.')
			return redirect(url_for('user'))
	return render_template('login.html', form=form, error=error, title=title)

@app.route('/logout')
@login_required
def logout():
	session.pop('logged_in', None)
	flash('You were just logged out.')
	return redirect(url_for('home'))

@app.route('/welcome')
def welcome():
	title = 'StockHawk - Welcome'
	return render_template('welcome.html', title=title)

@app.route('/user')
@login_required
def user():
	title = 'StockHawk - Account'
	return render_template('account.html', title=title)

@app.route('/stocks', methods=['GET', 'POST'])
# @login_required
def stocks():

	title = 'StockHawk - Stock lookup'	
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
				change = float(stock.get_change())
				loss = set_color(change)
				stock = set_stock_data(stock)
				title = stock.symbol+" - StockHawk"

		else:
			flash("Please enter a stock.")
			return redirect(url_for('stocks'))
		
		return render_template('stocks.html', form=form, stock=stock, title=title, loss=loss)

	elif request.method == 'GET':
		return render_template('stocks.html', form=form, stock=stock, title=title)


if __name__ == '__main__':
	app.run()