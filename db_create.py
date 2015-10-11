from app import db
from models import User

# setting up SQLAlchemy db 


# create the db and tables

db.create_all()

# insert data

db.session.add(User("admin", "abmorton@gmail.com", "admin"))
db.session.add(User("adam", "abmorton@gmail.com", "testpw"))
db.session.add(User("thatguy", "that@guy.io", "thatpw"))


# commit changes

db.session.commit()