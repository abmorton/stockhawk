import os

class BaseConfig(object):
	DEBUG = False
	WTF_CSRF_ENABLED = True
	SECRET_KEY = 'Hvee923sdf@#234argag~``gdgsa;5a202[a1d'
	CACHE_TYPE = 'simple'
	# Flask-Mail config:
	# MAIL_USE_SSL = True
	MAIL_PORT = 587
	MAIL_USE_TLS = True

class DevConfig(BaseConfig):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'sqlite:///flaskpractice.db'
	MAIL_SERVER = 'smtp.gmail.com'
	MAIL_USERNAME = os.environ['MAIL_USERNAME']
	MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
	MAIL_DEFAULT_SENDER = MAIL_USERNAME

class ProductionConfig(BaseConfig):
	DEBUG = False
	SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
	# MAIL_SERVER = os.environ['MAILGUN_SMTP_SERVER']
	# MAIL_USERNAME = os.environ['MAILGUN_SMTP_LOGIN']
	# MAIL_PASSWORD = os.environ['MAILGUN_SMTP_PASSWORD']
	# MAIL_DEFAULT_SENDER = MAIL_USERNAME




