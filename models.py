from app import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Stock(db.Model):
	
	__tablename__ = 'stocks'

	id = db.Column(db.Integer, primary_key=True)
	symbol = db.Column(db.String(4), index=True, unique=True)
	name = db.Column(db.String(30), index=True, unique=True)
	exchange = db.Column(db.String(5), index=True, unique=False)
	volume = db.Column(db.Integer)
	price = db.Column(db.Numeric)
	openprice = db.Column(db.Numeric)
	percentagechange = db.Column(db.Numeric)
	dayvolume = db.Column(db.Integer)
	averagevolume = db.Column(db.Integer)
	dividendyeild = db.Column(db.Numeric)
	dividendshare = db.Column(db.Numeric)
	marketcap = db.Column(db.String)
	peratio = db.Column(db.Numeric)

	def __init__(self, symbol, name, exchange, volume, price, openprice, percentagechange, dayvolume, averagevolume, dividendyeild, dividendshare, marketcap, peratio):
		self.symbol = symbol
		self.name = name
		self.exchange = exchange
		self.volume = volume
		self.price = price
		self.openprice = openprice
		self.percentagechange = percentagechange
		self.dayvolume = dayvolume
		self.averagevolume = averagevolume
		self.dividendyeild = dividendyeild
		self.dividendshare = dividendshare
		self.marketcap = marketcap
		self.peratio = peratio

	def __repr__(self):
		return '<Stock %r>' % (self.symbol)


class User(db.Model):

	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, nullable=False)
	email = db.Column(db.String, nullable=False)
	password = db.Column(db.String, nullable=False)
	stocks = relationship("Stock", backref="owners")

	def __init__(self, name, email, password):
		self.name = name
		self.email = email
		self.password = password

	def __repr__(self):
		return '{}'.format(self.name)