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
then = datetime.date(year, month, day)
now = datetime.datetime.now()

# insert data

db.session.add(User("admin", "admin@admin.com", "adminpw", now))
db.session.add(User("adam", "abmorton@gmail.com", "testpw", then))

db.session.add(Stock("XOMA", "XOMA Corporation", "NGM", "0.9929", None, None, None, "117.74M", 1))



# commit changes

db.session.commit()