import datetime
import smtplib
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, EditForm
# from dotenv import load_dotenv
import os

MY_MAIL = os.getenv('MY_MAIL')
MY_MAIL_PASSWORD = os.getenv('MY_MAIL_PASSWORD')
MY_MAIL_SMTP = os.getenv('MY_MAIL_SMTP')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)
gravatar = Gravatar(app, size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# TODO: Configure Flask-Login
loginmanager = LoginManager()
loginmanager.init_app(app)


# tworze loginloadera aby zwracal current_user
@loginmanager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# robie dekorator ktory sprawdza czy zalogowane kotno to admin
def admin_only(funkcja):
    @wraps(funkcja)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return funkcja(*args, **kwargs)

    return decorated_function


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI',
                                                  "sqlite:///posts.db")  # pobiera mi pierw zmienna z .env jesli nie ma uzywa drugiego
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    author = relationship('User', back_populates='posts')
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    blog_comments = relationship('Comment', back_populates='post')


# TODO: Create a User table for all your registered users.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comment', back_populates='author')


class Comment(db.Model):
    __tablename__ = 'comments'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    author = relationship('User', back_populates='comments')
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    post = relationship('BlogPost', back_populates='blog_comments')
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('blog_posts.id'))


with app.app_context():
    db.create_all()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['POST', 'GET'])
def register():
    registerform = RegisterForm()
    if registerform.validate_on_submit():
        new_email = request.form['email']
        if not db.session.execute(db.select(User).where(User.email == new_email)).scalar():
            new_password = request.form['password']
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=8)
            new_name = request.form['name']
            new_user = User(email=new_email, password=hashed_password, name=new_name)

            db.session.add(new_user)
            db.session.commit()
            # flash('Zaloguj sie na nowo utworzone konto')

            # return redirect(url_for('login'))
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
        else:
            flash('Uzytkownik o takim email istnieje, sporobuj sie zalogowac')
            return redirect(url_for('login'))
    return render_template("register.html", form=registerform)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=['POST', 'GET'])
def login():
    loginform = LoginForm()
    if loginform.validate_on_submit():
        login_email = request.form['email']
        if db.session.execute(db.select(User).where(User.email == login_email)).scalar():
            login_password = request.form['password']
            user = db.session.execute(db.select(User).where(User.email == login_email)).scalar()
            if check_password_hash(user.password, login_password):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash('Niepoprawne haslo')
                return redirect(url_for('login'))
        else:
            flash('Nie ma uzytkownika o takim emailu, zarejestruj sie')
            return redirect(url_for('register'))
    return render_template("login.html", form=loginform)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=['POST', "GET"])
def show_post(post_id):
    editform = EditForm()
    requested_post = db.get_or_404(BlogPost, post_id)

    if editform.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Zanim dodasz post zaloguj sie')
            return redirect(url_for('login'))
        comment_text = request.form['text']
        new_comment = Comment(author_id=current_user.id, post_id=post_id, text=comment_text)
        db.session.add(new_comment)
        db.session.commit()

    return render_template("post.html", post=requested_post, form=editform, comments=requested_post.blog_comments)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        title = request.form['title']
        subtitle = request.form['subtitle']
        img_url = request.form['img_url']
        body = request.form['body']
        current_date = datetime.datetime.today().strftime('%Y-%m-%d')
        new_post = BlogPost(title=title, subtitle=subtitle, date=current_date, img_url=img_url, body=body,
                            author_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>",methods=['POST','GET'])
@admin_only
def delete_post(post_id):
    all_comments=db.session.execute(db.select(Comment).where(Comment.post_id==post_id)).scalars()
    post_to_delete = db.session.execute(db.select(BlogPost).where(BlogPost.id==post_id)).scalar()
    print(post_to_delete.title)
    for comment in all_comments:
        db.session.delete(comment)

    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=['POST', 'GET'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        message = request.form['message']
        email = request.form['email']
        phone = request.form['phone']
        with smtplib.SMTP(f'{MY_MAIL_SMTP}', port=587) as connection:
            connection.starttls()
            connection.login(user=MY_MAIL, password=MY_MAIL_PASSWORD)
            body = f'Subject: Witaj {name}\n\nDziekuje za wiadomosc:\n{message} \nOdezwe sie do Ciebie pod ten numer telefonu: {phone} albo email: {email}'
            connection.sendmail(from_addr=os.getenv('MY_MAIL'), to_addrs=email, msg=body)
            flash('Wiadomosc zostala wyslana :3')
            return redirect(url_for('contact'))

    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=False, port=5002)
