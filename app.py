# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from forms import PostForm, SignUpForm, LoginForm
import hashlib

def hash_passwd(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SECRET_KEY'] = 'simple_secret_key'
db = SQLAlchemy(app)

# Модель поста
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Поле для хранения роли пользователя

    def __repr__(self):
        return f'<User {self.email}>'

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    posts = Post.query.all()
    return render_template('dashboard.html', posts=posts)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form = PostForm()
    if form.validate_on_submit():
        new_post = Post(title=form.title.data, content=form.content.data)
        db.session.add(new_post)
        db.session.commit()
        flash('Пост успешно создан!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_post.html', form=form)

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)
    form = PostForm()

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Пост обновлен!', 'success')
        return redirect(url_for('dashboard'))

    form.title.data = post.title
    form.content.data = post.content
    return render_template('edit_post.html', form=form, post=post)

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Пост удален!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():

        email = form.email.data
        password = hash_passwd(form.password.data)
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с этим email уже существует.', category='error')
        else:
            new_user = User(email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Аккаунт успешно создан!', category='success')
            return redirect(url_for('login')) 
    return render_template('sign_up.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = hash_passwd(form.password.data)
        user = User.query.filter_by(email=email, password=password).first()
        
        if user:
            session['user_id'] = user.id
            flash('Успешный вход!', category='success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный email или пароль.', category='error')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы.', category='success')
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user.is_admin:  # Проверка, является ли пользователь администратором
        flash('У вас нет доступа к этой странице.', category='error')
        return redirect(url_for('dashboard'))

    users = User.query.all()  # Получение всех пользователей
    posts = Post.query.all()  # Получение всех постов
    return render_template('admin.html', users=users, posts=posts)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Добавление администратора, если он еще не существует
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            admin_user = User(email='admin@example.com', password=hash_passwd('admin'), is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)
