from functools import wraps

# decorators

def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('You need to log in first.')
			return redirect(url_for('login'))
	return wrap

def login_reminder(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			message = Markup("<a href='/login'>Sign in</a> or <a href='/register'>register</a> to play.")
			flash(message)
			return f(*args, **kwargs)	
	return wrap

# This decorator is to perform asynchronous tasks (such as sending emails)
def async(f):
	def wrapper(*args, **kwargs):
		thr = Thread(target=f, args=args, kwargs=kwargs)
		thr.start()
	return wrapper

# Started, but not finished this decorator. I need to think about if it makes sense to implement this. There might be use cases for a similar decorator to limit trading times/days, but again, that might not serve a purpose.

# def after_hours_mode(f):
# 	@wraps(f)
# 	def wrap(*args, **kwargs):
# 		now = datetime.datetime.utcnow()
# 		if now.weekday() >= 5:
# 			#don't allow queries UNLESS the stock is NOT in db
# 			pass
# 		else:
# 			return f(*args, **kwargs)
# 	return wrap


# If there's no connectivity to yahoo-finance api, bypass and query db instead, but also indicate this to user
# def db_if_yahoo_fail(f):
# 	@wraps(f)
# 	def wrap(*args, **kwargs):
# 		try:
# 			f(*args, **kwargs)
# 			return flash('hi')
# 		except:
# 			flash("Couldn't connect to yahoo-finance API, getting quotes from database.")
# 			# return search_company(*args)
# 			return redirect(url_for('news'))
# 	return wrap

# -------------------------------------------------------
