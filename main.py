from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, abort, send_from_directory
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditor
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_ckeditor import CKEditor, CKEditorField
from functools import wraps
from flask_gravatar import Gravatar
from bleach import clean
from bleach.sanitizer import Cleaner
import html
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
# CREATE DATABASE
app = Flask(__name__)
ckeditor = CKEditor(app)
Bootstrap5(app)

load_dotenv()

# הגדרות Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail = Mail(app)  # אתחול Flask-Mail

allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'blockquote', 'code']
allowed_attrs = {'a': ['href', 'title', 'target']}
cleaner = Cleaner(tags=allowed_tags, attributes=allowed_attrs, strip=True)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    comments = relationship("Comment", back_populates="parent_post")


# Create a User table for all your registered users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    # This will act like a list of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog content",validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # ***************Child Relationship*************#
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text: Mapped[str] = mapped_column(Text, nullable=False)

gravatar = Gravatar(app,
                    size=40,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None,)

with app.app_context():
    db.create_all()
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        # Otherwise, continue with the route function
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def get_all_posts():
    # Query the database for all the posts. Convert the data to a python list.
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)

# Add the CommentForm to the route
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    # Add the CommentForm to the route
    comment_form = CommentForm()
    # Only allow logged-in users to comment on posts
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form)


# TODO: add_new_post() to create a new blog post
@app.route('/new-post', methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        cleaned_content = html.unescape(cleaner.clean(form.body.data))


        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=cleaned_content,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )

        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form)

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
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)

@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.query(Comment).filter(Comment.post_id == post_id).delete()

    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_mail import Mail, Message
from flask_login import login_required, current_user

# הגדרות Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # שרת SMTP של Gmail
app.config['MAIL_PORT'] = 587  # פורט SMTP מאובטח
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'nir41415@gmail.com'  # המייל שלך
app.config['MAIL_PASSWORD'] = 'your_app_password'  # הכנס את סיסמת האפליקציה שלך
app.config['MAIL_DEFAULT_SENDER'] = 'nir41415@gmail.com'  # כתובת השולח בפועל

mail = Mail(app)  # אתחול Flask-Mail

@app.route("/contact", methods=["GET", "POST"])
@login_required
def contact():
    if request.method == "POST":
        name = current_user.name
        email = current_user.email
        phone = request.form.get("phone")
        message = request.form.get("text")

        if not name or not email or not message:
            flash("Please fill out all required fields.", "danger")
            return redirect(url_for("contact"))

        msg = Message(
            subject=f"New Contact Form Submission from {name}",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=["nir4141511@gmail.com"],
            body=f"""
            Name: {name}
            Email: {email}
            Phone: {phone}
            Message: {message}
            """,
            reply_to=email
        )

        try:
            mail.send(msg)
            flash("Message sent successfully! ✅", "success")
        except Exception as e:
            flash(f"Error sending message: {str(e)}", "danger")

        return redirect(url_for("contact"))

    return render_template("contact.html")



@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        # Find user by email entered.
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        if not user:
            flash("The email does not exist,Please try again with diffrent email")
            return render_template("login.html",is_edit=True)
        elif not check_password_hash(user.password,password):
            flash("Password incorrect, Please try again")
            return render_template("login.html",is_edit=True)

        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template("login.html", current_user=current_user)



@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        result = db.session.execute(db.select(User).where(User.email == email))
        existing_user = result.first()

        if existing_user:
            flash("User already exists")
            return redirect(url_for("register"))
        else:
            new_user = User(
                email=request.form.get('email'),
                password=generate_password_hash(request.form.get('password'), method='pbkdf2:sha256', salt_length=8),
                name=request.form.get('name'),
            )

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for("get_all_posts"))

    return render_template("register.html",current_user=current_user)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

@app.route('/delete_all_users', methods=['GET', 'POST'])
@admin_only
def delete_all_users():
    try:
        db.session.query(User).delete()
        db.session.commit()
        return jsonify({'message': 'All users deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == "__main__":
    app.run(debug=True, port=5003)