from app import db
from models import *
import datetime

# setting up SQLAlchemy db 


# create the db and tables

db.create_all()

# prepare data to insert

year = 1982
month = 4
day = 3
birthday = datetime.date(year, month, day)
now = datetime.datetime.now()
today = datetime.date(now.year, now.month, now.day)
yesterday = datetime.date(now.year, now.month, 13)

# insert data
adam = User("adam", "abmorton@gmail.com", "testpw", yesterday)
db.session.add(User("admin", "admin@admin.com", "adminpw", today))
# db.session.add(User(adam))

db.session.add(Stock("XOMA", "XOMA Corporation", "NGM", "0.9929", None, None, None, "117.74M", 1))
db.session.commit()
# prepare more data to insert, using ForeignKeys and relationship()

stock = Stock.query.get(1)

# make a Portfolio 

port = Portfolio(adam.id)
db.session.add(port)
db.session.commit()

# make some trades
db.session.add(Trade(stock.symbol, 1, 10, yesterday, None, None, None))
db.session.add(Trade(stock.symbol, 1.20, -5, today, None, None, None)) 


# make a Position

# pos = Position(port.id, )

# position = Position(1)

# insert the data requiring ForeignKeys & relationship()

# commit changes

db.session.commit()