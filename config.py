import os

class BaseConfig(object):
	DEBUG = False
	WTF_CSRF_ENABLED = True
	SECRET_KEY = 'Hvee95a202[a1d'

class DevConfig(BaseConfig):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'sqlite:///flaskpractice.db'
	# SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

# class ProductionConfig(BaseConfig):
# 	DEBUG = False
# 	SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']