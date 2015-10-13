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
		return '<Stock : %r>' % (self.symbol)


class User(db.Model):

	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, nullable=False, unique=True)
	email = db.Column(db.String, nullable=False, unique=True)
	password = db.Column(db.String, nullable=False)
	last_seen = db.Column(db.Date, nullable=False)
	# stocks = relationship("Stock", backref="owners")


	# maybe add number of logins, etc.
	# also need to add portfolio, etc.

	def __init__(self, name, email, password, last_seen):
		self.name = name
		self.email = email
		self.password = password
		self.last_seen = last_seen

	def __repr__(self):
		return 'id: {}, name: {}'.format(self.id, self.name)


