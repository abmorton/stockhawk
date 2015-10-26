from app import async, app, config, Message, mail

# emails
@async
def send_async_email(app, msg):
	with app.app_context():
		mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
	msg = Message(subject, sender=sender, recipients=recipients)
	msg.body = text_body
	msg.html = html_body
	send_async_email(app, msg)

def new_user_email(user):
	subject = "Welcome to StockHawk, {}!".format(user.name)
	sender=('StockHawk', config.BaseConfig.MAIL_USERNAME)
	recipients=[user.email]
	text_body = "Welcome to StockHawk. Log in and start trading!"
	html_body = "<h3>Hi %s,</h3><p>Thanks for registering an account with StockHawk. We've added $1,000,000 of play money to your account. <a href='http://stockhawk.herokuapp.com/login'>Sign in</a> and start trading!<br><br>Good luck!<br> - Adam</p>" % user.name
	send_email(subject, sender, recipients, text_body, html_body)

def password_reminder_email(user):
	subject = "Forgotten password"
	sender=('StockHawk', config.BaseConfig.MAIL_USERNAME)
	recipients=[user.email]	
	text_body = user.password
	html_body = "<h3>Hi %s,</h3><p>Your password is: <b>%s</b> </p><p>We suggest you <a href='http://stockhawk.herokuapp.com/login'>sign in</a> and change your password on the user settings page.</p><br>Happy trading!<br> - Adam</p>"%(user.name, user.password)
	send_email(subject, sender, recipients, text_body, html_body)
