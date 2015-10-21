import os

class BaseConfig(object):
	DEBUG = False
	WTF_CSRF_ENABLED = True
	SECRET_KEY = 'Hvee923sdf@#234argag~``gdgsa;5a202[a1d'
	CACHE_TYPE = 'simple'

class DevConfig(BaseConfig):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'sqlite:///flaskpractice.db'

class ProductionConfig(BaseConfig):
	DEBUG = False
	SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

# Flask-Mail config:

# MAIL_SERVER = 'smtp.gmail.com'
# MAIL_PORT = 465
# MAIL_USE_TLS = False
# MAIL_USE_SSL = True
# MAIL_USERNAME = os.environ['MAIL_USERNAME']
# MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
# MAIL_DEFAULT_SENDER = MAIL_USERNAME
