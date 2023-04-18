from flask_wtf import FlaskForm
from data import db_session
from wtforms import StringField, TextAreaField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired
from data.bands import Bands


def possible_book():
    db_sess = db_session.create_session()
    return db_sess.query(Bands).order_by(Bands.name)


class SongForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    band = QuerySelectField('Исполнитель', query_factory=possible_book,
                            get_label='name', allow_blank=True)
    chords = TextAreaField('Аккорды')
    is_private = BooleanField("Не публиковать")
    submit = SubmitField('Сохранить')
