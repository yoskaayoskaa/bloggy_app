from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired()])
    about_me = TextAreaField('Обо мне', validators=[Length(min=0, max=140)])
    submit = SubmitField('Изменить')

    def __init__(self, original_username):
        super().__init__()
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user:
                raise ValidationError('Пользователь с таким именем уже зарегистрирован')


class EmptyForm(FlaskForm):
    submit = SubmitField('Подтвердить')


class PostForm(FlaskForm):
    post = TextAreaField('Напишите классный пост:', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class MessageForm(FlaskForm):
    message = TextAreaField('Текст сообщения', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Отправить')
