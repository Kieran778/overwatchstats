from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


#Creates an instance of the Flask class
app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DB'] = 'OverwatchStats'
app.config['MYSQL_PASSWORD'] = 'limccsel11!'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#Initializing MySQL
mysql = MySQL(app)

#Allows you to make changes and reload web page without having to restart the server
app.debug = True

#Makes the route the home page ('/')
@app.route('/')
def index():
    return render_template('home.html')

#About
@app.route('/about')
def about():
    return render_template('about.html')

#Articles
@app.route('/articles')
def articles():
    #Create DB Cursor
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles")

    #Returns all the rows in dictionary form
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        return render_template('articles.html', msg="No Articles Found")

    return render_template('articles.html')


#Single article
@app.route('/articles/<string:id>/')
def article(id):
    #Create DB Cursor
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    #Returns all the rows in dictionary form
    article = cur.fetchone()

    return render_template('article.html', article = article)

#Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

#User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data   
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to DB
        mysql.connection.commit()
        #Close Connection
        cur.close()

        flash('You are now registered and can log in.', category='alert-success')
        return redirect(url_for('login'))
    return render_template('register.html', form = form)    

#User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create Cursor
        cur = mysql.connection.cursor()

        #Check DB for entered username
        result = cur.execute('SELECT * FROM users WHERE username = %s', [username])
        if result > 0:
            #Get Stored Hash
            data = cur.fetchone()
            password = data['password']

            #Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', category='alert-success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            #Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

#Cbeck if User logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', category='alert-danger')
            return redirect(url_for('login'))
    return wrap

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create DB Cursor
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles")

    #Returns all the rows in dictionary form
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        return render_template('dashboard.html', msg="No Articles Found")

    return render_template('dashboard.html')



@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', category='alert-success')
    return redirect(url_for('index'))

#Register Article Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create Cursor
        cur = mysql.connection.cursor()

        #Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        #Commit to DB
        mysql.connection.commit()

        #Close DB
        cur.close()
        flash('Article Created', category='alert-success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

#Ensures this class is the class thats gets run (the main class)
if __name__ == '__main__':
    app.secret_key='secret123'
    app.run()

