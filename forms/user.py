from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class UserForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    adress = StringField('Введите адрес, чтобы узнать расположение\nближайшего музыкального магазина')
    submit = SubmitField('Сохранить')
