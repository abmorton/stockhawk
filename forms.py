from flask.ext.wtf import Form
from wtforms import TextField, IntegerField, BooleanField, PasswordField, RadioField, validators
from wtforms.validators import Length, EqualTo, Email, NumberRange, Required

# from wtforms import TextField, PasswordField, BooleanField, validators


class StockSearchForm(Form):
	stocklookup = TextField('stocklookup', [validators.Length(min=1, max=18)])

class LoginForm(Form):
	username = TextField('username', [validators.Length(min=2, max=30)])
	password = PasswordField('password', [validators.Length(min=5, max=30)])

class PasswordReminderForm(Form):
	username = TextField('username', [validators.Length(min=2, max=30)])

class RegisterForm(Form):
	username = TextField('Username', validators=[Length(min=2, max=25, message='Username must be between 2 and 25 characters.')])
	email =  TextField('Email address', validators=[Length(min=6, max=50), Email(message='Please enter a valid email address.')])
	password = PasswordField('Password', validators=[Length(min=6, max=30, message='Password must be between 6 and 30 characters.')])
	confirm = PasswordField('Confirm password', validators=[EqualTo('password', message='Passwords must match.')])
	accept_tos = BooleanField('I accept the Terms of Service (required)', validators=[Required(message='You must accept the Terms of Service to register and account.')])

class TradeForm(Form):
	amount = IntegerField('Shares', [validators.NumberRange(min=1, max=9999999999999, message="Invalid share quantity. Please try again.")])
	buy_or_sell = RadioField('Buy or Sell', choices=[('buy','Buy'), ('sell','Sell')])

class FullTradeForm(Form):
	symbol = TextField('Stock symbol', [validators.Length(min=1, max=10)])
	share_amount = IntegerField('Shares', validators=[NumberRange(min=1, max=999999999999, message="Invalid share quantity. Please try again.")])
	buy_or_sell = RadioField('Buy or Sell', choices=[('buy','Buy'), ('sell','Sell')])
