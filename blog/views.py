from flask import Flask,render_template, request,flash, redirect, url_for,session, abort
from models import User, todays_recent_posts
app = Flask(__name__)
app.secret_key = 'sugarsugar'

@app.route('/')
def index():
	posts = todays_recent_posts(3)
	return render_template("index.html", posts=posts)

@app.route('/about/<smthng>')
def about(smthng):
    return "This page is about {}".format(smthng)

@app.route("/register", methods = ["GET","POST"])
def register():
	if request.method == "POST":
		username = request.form['username']
		password = request.form['password']

		user = User(username)
		if not user.register(password): 
			flash('A user with that username already exists.')
		else: 
			flash('Successfully registered')
			return redirect(url_for('login'))
	return render_template("register.html")

@app.route("/login", methods = ["GET","POST"])
def login():
	if request.method == "POST":
		username = request.form['username']
		password = request.form['password']

		user = User(username)

		if not user.verify_pass(password):
			flash('Invalid login')
		else:
			flash('Successfully logged in')
			session["username"] = user.username
			return redirect(url_for("index"))
	return render_template('login.html')

@app.route("/add_post", methods = ["POST"])
def add_post():
	title = request.form["title"]
	tags = request.form["tags"]
	text = request.form["text"]

	if not title:
		abort(400, 'You must give your post a title.')
	if not tags:
		abort(400,'You must give your post at least one tag')
	if not text:
		abort(400,'You must give your post a text body')
	User(session['username']).add_post(title, tags,text)
	return redirect(url_for('index'))

@app.route("/like_post/<post_id>")
def like(post_id):
	username = session.get("username")
	if not username:
		flash("You must be logged in")
		return redirect(url_for("login"))

	user = User(username)
	user.like(post_id)
	flash("Liked post")
	return redirect(request.referrer)

@app.route("/profile/<username>")
def profile(username):
	user1 = User(session.get("username"))
	user2 = User(username)
	posts = user1.my_own_posts(3)
	similar = []
	common = {}
	if user1.username == user2.username:
		similar = user1.similar_users(3)
	else: common = user1.commonality(user2)
	return render_template("profile.html",username=username,posts=posts, similar=similar, common=common)

@app.route("/logout")
def logout():
	session.pop('username', None)
	flash("Logged out")
	return redirect(url_for('index'))
