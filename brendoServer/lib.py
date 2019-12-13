"""This module for functions that dont directly return any pages / Dynamic page generation.
Public vars in this module:
debugMode: bool, if True prints debug info. Retreived from config table in database.
sessionStore: sqlite3 connection to storage/tmp/sessionStore.db"""
import sqlite3, os, uuid, pickle
from shutil import rmtree


def serverStart():
	global sessionStore, debugMode
	"""Function that calls at server start. Creates the tmp db sessionStore and connects and returns 
	storage/brendoServer.db . also defines all global variables."""
	if not os.path.exists(f"{os.getcwd()}/storage"):
		db = setupStorage()
	else:
		db = sqlite3.connect("storage/brendoServer.db")
	try:
		rmtree("storage/tmp")
	except:
		pass
	c = db.cursor()
	c.execute("SELECT * FROM config WHERE setting='debugMode'")
	debugMode = c.fetchone()[1]
	os.mkdir("storage/tmp")
	sessionStore = sqlite3.connect("storage/tmp/sessionStore.db")
	sessionStore.cursor().execute("""CREATE TABLE sessions 
	(sessionId text, userId int)""")
	sessionStore.commit()
	return db

def setupStorage():
	"""
	Sets up the storage folder and DB on first run. returns slite3 connection object.
	"""
	os.mkdir("storage")
	os.mkdir("storage/ext") #Extensions folder
	os.mkdir("storage/media") #Where all of the uploaded files go
	os.mkdir("storage/tmp") #sessionStore and others stored here
	db = sqlite3.connect("storage/brendoServer.db")
	tempC = db.cursor()
	tempC.execute("""CREATE TABLE config
	(setting text, value int) """)
	tempC.execute("""INSERT INTO config VALUES ('setup', 0), ('loadExtensions', 1),
	('debugMode', 1), ('signupAllowed', 1)""")
	tempC.execute("""CREATE TABLE files
	(uploaderId int, fileId int, pathId int, fakeFileName text, trueFileName text, public bool)""")
	tempC.execute("""CREATE TABLE directories
	(dirId int, parentId int, ownerId int, name text, public bool)""")
	tempC.execute("INSERT INTO directories VALUES (-1, NULL, 0, 'root', 1)")
	db.commit()
	dirinfo = []
	return db

def login(username, password, cursor):
	"""Returns a tuple, first element is True if successful; False if not.
	Second is the sequence that represents the user if the login was successful or 1 if password is incorrect 
	or 2 if user doesnt exist."""
	c = cursor
	try:
		c.execute("SELECT * FROM users WHERE username=?", (username,))
		user = c.fetchone()
		if not user == None and password == user[2]:
			return (True, user)
		else:
			return (False, 1)
	except sqlite3.Error as e:
		return (False, 2, e)
	
def signup(username, password, cursor, userGroup="member"):
	"""Works just like login, except creates a new account.
	Also checks to see if a user with that name already exists."""
	c = cursor
	c.execute("SELECT EXISTS(SELECT * FROM users WHERE username=?)", (username,))
	userExists = c.fetchone()
	if debugMode:
		print(userExists)
	if userExists[0] == 0:
		c.execute("SELECT * FROM users WHERE userId = (SELECT MAX(userId) FROM users)")
		lastId = int(c.fetchone()[0])
		c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (lastId + 1, username, password, userGroup))
		c.connection.commit()
		if debugMode:
			print(login(username, password, c))
		return login(username, password, c)
	else:
		return (False, 3)

def getUserFromSession(sessionId, cu):
	"""Sessions keep the login info temporarily.
	This function returns a login function call if it gets session info. otherwise it returns none.
	All sessions stored in the tmp db sessionStore. cu should be a cursor for 
	storage/brendoServer.db and returns a login() call to validate the user info."""
	c = sessionStore.cursor()
	c.execute("SELECT * FROM sessions WHERE sessionId=?", (sessionId,))
	fetchedSession = c.fetchone()
	if fetchedSession == None:
		return None
	else:
		cu.execute("SELECT * FROM users WHERE userId=?", (fetchedSession[1],))
		user = cu.fetchone()
		return login(user[1], user[2], cu)
	
def createSession(username, password, cursor):	
		"""Creates a session. cursor should be a connection to storage/brendoServer.db
		returns (False, <errcode>) if unsuccessful and the session ID along with the user if successful"""
		user = login(username, password, cursor)
		if debugMode:
			print(user)
		if not user[0]:
			return (False, user[1])
		else:
			c = sessionStore.cursor()
			sessionId = uuid.uuid4().hex
			if debugMode:
				print(sessionId)
			c.execute("INSERT INTO sessions VALUES (?, ?)", (sessionId, user[1][0]))	
			sessionStore.commit()
			return (sessionId, user[1])
			
def delInactiveSessions(sessionId, c):
	"""This function checks to remove any unused sessions. Always returns None. c should be the cursor object 
	and sessionId should be the sessionId currently in use by the client."""
	c2 = sessionStore.cursor()
	c2.execute("SELECT * FROM sessions WHERE sessionId=?", (sessionId,))
	usr = getUserFromSession(sessionId, c)
	
			
def getUserFromId(id, c):
	"""Gets a user by their id and returns a call to login() or (False, None) if the user does not exist. id 
	should be the user ID and c should be the cursor for brendoServer.db ."""
	c.execute("SELECT * FROM users WHERE userId=?", (id,))
	user = c.fetchone()
	if user == None:
		return (False, None)
	else:
		return login(user[1], user[2], c)
		
def generateUserLinkPage(c, pagenumber=0):
	"""Generates a html page that links to 50 user's pages. Generates the links only seperated by <br />.
	returns the page. c should be the brendoServer.db cursor object. pagenumber is which 50 would be shown 
	(i.e. if pagenumber were 1, then it would show the second group of fifty users.) if pagenumber is invalid 
	then None is returned."""
	currentId = pagenumber * 50
	resultPage = ""
	pageButtons = f"<br /><a href='/userlist/{pagenumber-1}'>Previous</a>|<a href='/userlist/{pagenumber+1}'>Next</a>"
	if getUserFromId(currentId, c)[0] == False:
		return None
	else:
		lastId = currentId + 50
		while currentId < lastId:
			user = getUserFromId(currentId, c)
			if user[0] == False:
				return resultPage + pageButtons
			else:
				username = user[1][1]
				resultPage += f"<a href='/user/{currentId}'>{username}</a><br />"
			currentId += 1
		return resultPage + pageButtons
		
def uploadFile(file, isPublic, userId, cu, dirId=-1, fcontents=""):
	"""Takes a bottle FileUpload instance as an argument and adds it to storage/media as well as adds its 
	info to the database. cu should be the db cursor. isPublic should be a bool. userId should be the 
	uploaders id. dirId is the directory ID and defaults to -1. fcontents should be the file's contents."""
	fakeName = file.filename
	extension = os.path.splitext(file.filename)[1]
	cu.execute("SELECT * FROM files WHERE fileId=(SELECT MAX(fileId) FROM files)")
	newId = cu.fetchone()
	if newId==None:
		newId = 0
	else:
		newId = newId[1]	
	fileName = f"userfile-{newId}-{userId}.{extension}"
	with open("storage/media/" + fileName, "wb") as fw:
		fw.write(fcontents)
	cu.execute("INSERT INTO files VALUES (?, ?, ?, ?, ?, ?)",
	(userId, newId, dirId, fakeName, fileName, isPublic))
	cu.connection.commit()
