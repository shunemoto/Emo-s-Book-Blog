from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user
import pytz
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
import os

app = Flask(__name__)

db = SQLAlchemy()
DB_INFO = {
    'user': 'postgres',
    'password': '',
    'host': 'localhost',
    'name': 'postgres'
}

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg://{user}:{password}@{host}/{name}'.format(**DB_INFO)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

app.config["SECRET_KEY"] = os.urandom(24)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

db.init_app(app)

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

migrate = Migrate(app,db)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(850), nullable=False)
    body = db.Column(db.String(300), nullable=False)
    tokyo_timzone = pytz.timezone('Asia/Tokyo')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(tokyo_timzone))
    img_name = db.Column(db.String(300), nullable=True)
    
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(200), unique=False, nullable=False)
    
@login_manager.user_loader 
def load_user(user_id): 
    return User.query.get(int(user_id))

@app.route("/")
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    posts = [
        {
            'id': post.id,
            'title': post.title,
            'body': post.body,
            'img_name': post.img_name,
            'created_at': post.created_at.date(),
        }
        for post in posts
    ]
    return render_template("index.html", posts=posts)
    
@app.route("/<int:post_id>/readmore")
def readmore(post_id):
    post = Post.query.get(post_id)
    post = {
        'id': post.id,
        'title': post.title,
        'body': post.body,
        'img_name': post.img_name,
        'created_at': post.created_at.date(),
    }
    return render_template('readmore.html', post=post)
    
@app.route("/admin")
@login_required
def admin():
    posts = Post.query.all()
    posts = [
        {
            'id': post.id,
            'title': post.title,
            'body': post.body,
            'img_name': post.img_name,
            'created_at': post.created_at.date(),
        }
        for post in posts
    ]
    return render_template("admin.html", posts=posts)

# アップロードが許可される拡張子
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# アップロードされたファイルが許可される拡張子か判別
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/create", methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        return render_template('create.html')
    elif request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')
        created_at = datetime.now(pytz.timezone('Asia/Tokyo'))
        file = request.files['img']
        filename = file.filename
        if not allowed_file(filename):
            return "File extension not allowed", 400
        img_name = os.path.join(app.static_folder, 'img', filename)
        file.save(img_name)
        post = Post(title=title, body=body, img_name=filename, created_at=created_at)
        db.session.add(post)
        db.session.commit()
        return redirect('/admin')
    
@app.route("/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update(post_id):
    post = Post.query.get(post_id)
    if request.method == 'GET':
        return render_template('update.html', post=post)
    elif request.method == 'POST':
        post.title = request.form.get('title')
        post.body = request.form.get('body')
        db.session.commit()
        return redirect('/admin')
    
@app.route("/<int:post_id>/delete")
@login_required
def delete(post_id):
    post = Post.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect('/admin')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pass = generate_password_hash(password, method='pbkdf2:sha256')
        post = User(username=username, password=hashed_pass)
        db.session.add(post)
        db.session.commit()
        return redirect('/login')
    
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password=password):
            login_user(user)
            return redirect('/admin')
        else:
            return redirect('/login', msg='ユーザ名/パスワードが違います')
    else:
        return render_template('login.html', msg='')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')