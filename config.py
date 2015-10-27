import os

class BaseConfig(object):
	DEBUG = False
	
	WTF_CSRF_ENABLED = True
	SECRET_KEY = os.environ['SECRET_KEY']
	
	CACHE_TYPE = 'simple'
	
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	MAIL_SERVER = os.environ['MAIL_SERVER']
	MAIL_USERNAME = os.environ['MAIL_USERNAME']
	MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
	MAIL_DEFAULT_SENDER = MAIL_USERNAME

class DevConfig(BaseConfig):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'sqlite:///flaskpractice.db'
	
	# MAIL_SERVER = 'smtp.gmail.com'
	# MAIL_USERNAME = 
	# MAIL_PASSWORD = 

	# CELERY_BROKER_URL = 'redis://localhost:6379/0'
	# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

class ProductionConfig(BaseConfig):
	DEBUG = False
	SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']





