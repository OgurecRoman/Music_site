from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class BandForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    biography = TextAreaField('Биография')
    is_private = BooleanField("Не публиковать")
    submit = SubmitField('Сохранить')
