import pageTemplates as pages
import lib
import bottle
import sqlite3 as sql
import os
from sys import argv
import pprint

#getArg = bottle.request.forms.get
#session = bottle.request.cookies.get("sessionId")
#For copy/paste purposes

db = lib.serverStart()

@bottle.get('/<filename:re:.*\.css>')
def stylesheets(filename):
	return bottle.static_file(filename, root='static/')

@bottle.route("/")
def start():
	c = db.cursor()
	c.execute("SELECT * FROM config WHERE setting='setup'")
	isSetup = c.fetchone()[1]
	c.close()
	print(isSetup)
	if not isSetup:
		return pages.installSignUp
	else:
		return pages.loginPage
		
		
@bottle.route("/install", method="POST")
def installPage():
	getArg = bottle.request.forms.get
	c = db.cursor()
	c.execute("SELECT * FROM config WHERE setting='setup'")
	isSetup = c.fetchone()[1]
	if not isSetup:
		c.execute("""CREATE TABLE users
		(userId int, username text, password text, userGroup text)""")
		c.execute("""INSERT INTO users VALUES (0, ?, ?, 'admin')""", (getArg("username"), getArg("password")))
		c.execute("UPDATE config SET value=1 WHERE setting='setup'")
		db.commit()
		return pages.installComplete
	elif not getArg("username")==None and lib.login(getArg("username"), getArg("password"), c)[1][3] != "admin":
		return bottle.abort(401, pages.errPage(8))
	else:
		return pages.reinstallPage 
		
@bottle.route("/login", method="POST")
def loginPage():
	getArg = bottle.request.forms.get
	username = getArg("username")
	if lib.debugMode:
		print(username)
	password = getArg("password")
	if username==None:
		return pages.loginFailed % (7,) + pages.loginPage
	ses = lib.createSession(username, password, db.cursor())
	if lib.debugMode:
		print(ses)
	if ses[0]==False:
		return pages.loginFailed % ses[1] + pages.loginPage
	else:
		if lib.debugMode:
			print(ses)
		bottle.response.set_cookie("session_id", ses[0])
		if lib.debugMode:
			print(bottle.request.get_cookie("session_id"))
		return pages.redirectToHomePage
		
@bottle.route("/home")
def homePage():
	sessionId = bottle.request.get_cookie("session_id")
	if lib.debugMode:
		print(sessionId)
	if sessionId == None:
		bottle.abort(401, pages.errPage(6))
	session = lib.getUserFromSession(sessionId, db.cursor())
	if not session:
		bottle.abort(401, pages.errPage(6))
	else:
		return pages.homePage.format(session[1][1])
		
@bottle.route("/signup")
def signupPage():
	c = db.cursor()
	try:
		signUpFailed = bottle.request.query.failed
		if int(signUpFailed):
			return pages.signupFailed % (3,) + pages.signUpPage
	except:
		pass
	c.execute("SELECT * FROM config WHERE setting='signupAllowed'")
	signupsAllowed = c.fetchone()
	if signupsAllowed:
		return pages.signUpPage
	else:
		bottle.abort(401, pages.errPage(5))
		
@bottle.route("/signup/p", method="POST")
def signupProcessing():
	getArg = bottle.request.forms.get
	username = getArg("username")
	password = getArg("password")
	if username == None or password == None:
		bottle.abort(400, pages.errPage(7))
	else:
		newUser = lib.signup(username, password, db.cursor())
		if newUser[0]==False:
			 bottle.redirect("/signup?failed=1")
		else:
			return pages.redirectToLoginPage
			
@bottle.route("/user/<id:int>")
def userPage(id):
	sessionId = bottle.request.get_cookie("session_id")
	if lib.getUserFromSession(sessionId, db.cursor()) == None:
		bottle.abort(401, pages.errPage(6))
	else:
		user = lib.getUserFromId(id, db.cursor())
		if user[0] == False:
			bottle.abort(404, pages.errPage(4))
		else:
			return pages.userPage % (user[1][1], user[1][3])
			
@bottle.route("/userlist/<page:int>")
def userListPage(page):
	sessionId = bottle.request.get_cookie("session_id")
	if lib.getUserFromSession(sessionId, db.cursor()) == None:
		bottle.abort(401, pages.errPage(6))
	else:
		p = lib.generateUserLinkPage(db.cursor(), pagenumber=page)
		if p == None:
			bottle.abort(404, pages.errPage(4))
		else:
			return p
			
@bottle.route("/upload")
def uploadPage():
	sessionId = bottle.request.get_cookie("session_id")
	user = lib.getUserFromSession(sessionId, db.cursor())
	if user[0]==True:
		return pages.uploadPage
	else:
		bottle.abort(401, pages.errPage(4))

@bottle.route("/upload/p", method="POST")
def uploadProcessingPage():
	sessionId = bottle.request.get_cookie("session_id")
	user = lib.getUserFromSession(sessionId, db.cursor())
	if user[0]==True:	
		file = bottle.request.files.get("file")
		ispublic = bottle.request.forms.get("public")
		lib.uploadFile(file, ispublic, user[1][0], db.cursor())
		return 
		
@bottle.route("/debug")
def debugPage():
	if not lib.debugMode:
		bottle.abort(500, pages.errPage(5))
	else:
		return pages.debugPage
		
@bottle.route("/debug/<action>")
def debugPageAction(action):
	if not lib.debugMode:
		bottle.abort(500, pages.errPage(5))
	else:
		if action == "vars":
			sessionId = bottle.request.cookies.get("session_id")
			user = lib.getUserFromSession(sessionId, db.cursor())
			return f'''<b>globals</b><br/>{pprint.pformat(globals(), indent=2)}<br/><br/>
			<b>locals</b><br/>{pprint.pformat(locals(), indent=2)}<br/><br/>'''.replace("\n", "<br/>")
		elif action == "pages":
			retstr = ""
			pagesVars = vars(pages)
			for x in pagesVars:
				retstr += f"<br/><h1>{x}</h1>{pagesVars[x]}<br/><br/>"
			return retstr 

if __name__ == "__main__":		
	bottle.run(host=argv[1], port=argv[2], debug=True)
