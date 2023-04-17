from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class SongForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    band = StringField('Исполнитель')
    chords = TextAreaField('Аккорды')
    is_private = BooleanField("Не публиковать")
    submit = SubmitField('Сохранить')
