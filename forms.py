from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, validators

class StockSearchForm(Form):
	stocklookup = TextField('stocklookup', [validators.Length(min=1, max=15)])

class LoginForm(Form):
	username = TextField('username')
	password = PasswordField('password')