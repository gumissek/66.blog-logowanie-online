from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.simple import EmailField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Dodaj post")


# TODO: Create a RegisterForm to register new users

class RegisterForm(FlaskForm):
    email = EmailField(label='Podaj email',validators=[DataRequired()])
    password = PasswordField(label='Podaj haslo',validators=[DataRequired()])
    name = StringField(label='Podaj imie', validators=[DataRequired()])
    submit = SubmitField(label='Zarejestruj sie')
# TODO: Create a LoginForm to login existing users

class LoginForm(FlaskForm):
    email = EmailField(label='Email',validators=[DataRequired()])
    password = PasswordField(label='Haslo',validators=[DataRequired()])
    submit = SubmitField('Zaloguj')
# TODO: Create a CommentForm so users can leave comments below posts

class EditForm(FlaskForm):
    text = CKEditorField(label='Komentarz:',validators=[DataRequired()])
    submit = SubmitField(label='Dodaj komentarz')