from app import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Stock(db.Model):
	__tablename__ = 'stocks'

	id = db.Column(db.Integer, primary_key=True)
	symbol = db.Column(db.String(5), index=True, unique=True)
	name = db.Column(db.String(35), index=True, unique=True)
	exchange = db.Column(db.String(5), index=True)
	price = db.Column(db.Numeric)
	div_yield = db.Column(db.Numeric)
	ex_div = db.Column(db.Date)
	div_pay = db.Column(db.Date)
	market_cap = db.Column(db.String)
	view_count = db.Column(db.Integer)
	trades = db.relationship('Trade', backref='stock', lazy='dynamic')

	def __init__(self, symbol, name, exchange, price, div_yield, ex_div, div_pay, market_cap, view_count):
		self.symbol = symbol
		self.name = name
		self.exchange = exchange
		self.price = price
		self.div_yield = div_yield
		self.ex_div = ex_div
		self.div_pay = div_pay
		self.market_cap = market_cap
		self.view_count = view_count

	def __repr__(self):
		return '<id: {}, symbol: {}, exchange: {}>'.format(self.id, self.symbol, self.exchange)


class User(db.Model):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, nullable=False, unique=True)
	email = db.Column(db.String, nullable=False, unique=True)
	password = db.Column(db.String, nullable=False)
	last_seen = db.Column(db.Date, nullable=False)
	#this is a 1:1 relationship with Portfolio
	portfolio = db.relationship('Portfolio', uselist=False, backref='owner')

	def __init__(self, name, email, password, last_seen):
		self.name = name
		self.email = email
		self.password = password
		self.last_seen = last_seen

	def __repr__(self):
		return 'id: {}, name: {}'.format(self.id, self.name)


class Portfolio(db.Model):
	__tablename__ = 'portfolios'

	id = db.Column(db.Integer, primary_key=True)
	# 1:1 relationship set up on users side
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	cash = db.Column(db.Numeric)
	value = db.Column(db.Numeric)
	positions = db.relationship('Position', backref='portfolios', lazy='dynamic')
	trades = db.relationship('Trade', backref='portfolios', lazy='dynamic')

	def __init__(self, user_id, cash, value):
		self.user_id = user_id
		self.cash = cash
		self.value = value

	def __repr__(self):
		return 'id: {}, user_id: {}, cash: {}, value: {}'.format(self.id, self.user_id, self.cash, self.value)

class Position(db.Model):
	__tablename__ = 'positions'

	id = db.Column(db.Integer, primary_key=True)
	portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'))
	symbol = db.Column(db.String)
	cost = db.Column(db.Numeric)
	value = db.Column(db.Numeric)
	sharecount = db.Column(db.Integer)
	div_eligible_sharecount = db.Column(db.Integer)
	# taking out cascade="all, delete-orphan" from trades
	trades = db.relationship('Trade', backref='position', lazy='dynamic')

	def __init__(self, portfolio_id, symbol, cost, value, sharecount, div_eligible_sharecount):
		self.portfolio_id = portfolio_id
		self.symbol = symbol
		self.cost = cost
		self.value = value
		self.sharecount = sharecount
		self.div_eligible_sharecount = div_eligible_sharecount
		# self.trades = trades

	def __repr__(self):
		return 'id: {}, portfolio_id: {}, symbol: {}, cost: {}, value: {} sharecount: {}'.format(self.id, self.portfolio_id, self.symbol, self.cost, self.value, self.sharecount)


class Trade(db.Model):
	__tablename__ = 'trades'

	id = db.Column(db.Integer, primary_key=True)
	symbol_id = db.Column(db.String, db.ForeignKey('stocks.symbol'), nullable=False, index=True)
	position_id = db.Column(db.Integer, db.ForeignKey('positions.id'))
	portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'))
	price = db.Column(db.Numeric, nullable=False)
	quantity = db.Column(db.Integer, nullable=False)
	date = db.Column(db.Date, nullable=False)
	div_yield = db.Column(db.Numeric, nullable=True)
	ex_div = db.Column(db.Date, nullable=True)
	div_pay = db.Column(db.Date, nullable=True)

	def __init__(self, symbol_id, position_id, portfolio_id, price, quantity, date, div_yield, ex_div, div_pay):
		self.symbol_id = symbol_id
		self.position_id = position_id
		self.portfolio_id = portfolio_id
		self.price = price
		self.quantity = quantity
		self.date = date
		self.div_yield = div_yield
		self.ex_div = ex_div
		self.div_pay = div_pay

	def __repr__(self):
		return 'id: {}, symbol_id: {}, position_id: {}, portfolio_id {}'.format(self.id, self.symbol_id, self.position_id, self.portfolio_id)



