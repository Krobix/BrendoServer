#You probably shouldnt modify these.

loginPage = '''
<h1 style="text-align:center;">Brendo Server Login</h1>
<form action="/login" method="post">
	Username<input name="username" type="text" /><br />
	Password<input name="password" type="password" /><br />
	<input value="Submit" type="submit" />
</form>
<a href="/signup">Create Account</a>
'''

loginFailed = '''<p style="text-align:center;">Login failed. Please make sure your credentials are correct.</p>'''

signupFailed = '''<b style="text-align:center;">Sign Up Failed: a user with that name already exists.
</b><br />'''

installSignUp = '''
<b>Brendo Server Setup</b><br />
Please set up the owner\'s account.<br />
<form action="/install" method="post">
	Username (make it memorable): <input name="username" type="text" /><br />
	Password (also remember this): <input name="password" type="password" /><br />
	<input value="Submit" type="submit" />
</form>
'''

signUpPage = '''
<h1 style="text-align:center;">Sign Up</h1><br />
<form action="/signup/p" method="post">
	Username<input name="username" type="text" /><br />
	Password<input name="password" type="password" /><br />
	<input value="Sign Up" type="Submit" />
</form>
'''

installComplete = '''<b>Base installation finished. You may now <a href="/">go back to the home page</a>.</b>'''

reinstallPage = '''<b style="text-align:center;">run the server with the argument as "reinstall" to 
reinstall. NOTE: This will also erase extensions!</b>'''

homePage = '''<p style="text-align:center;">Welcome back, {}!<br /><a href="/userlist/0">View User List</a>
<br/><a href="/upload">Upload file</a></p>'''

redirectToLoginPage = '''<a href="/" style="text-align:center;">Click here to go to login page!</a>'''

redirectToHomePage = '''<a href="/home" style="text-align:center;">Click here to go to home page!</a>'''

userPage = '''<p style="text-align:center;">Username: %s <br /> User Group: %s <br /></p>'''

uploadPage= '''<h2 style="text-align:center;">Upload a File</h2>
<form action="/upload/p" method="post" enctype="multipart/form-data">
Select File to Upload: <input type="file" name="file" /><br />
Enter Directory Id (Leave at default for root directory): <input type="text" name="directory" value="-1" />
<br/>Is public? <input type="checkbox" name="public" value="1" />
<br/><input type="submit" value="upload" />
<form/>'''

debugPage = '''<a href="/debug/vars">vars</a><br/><a href="/debug/pages">pages</a>'''
