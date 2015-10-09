from flask.ext.wtf import Form
from wtforms import StringField, validators

class StockSearchForm(Form):
	stocklookup = StringField('stocklookup', [validators.Required()])

class LoginForm(Form):
	username = StringField('username')
	password = StringField('password')