import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Songs(SqlAlchemyBase):
    __tablename__ = 'songs'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    chords = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    band_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("bands.id"))
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    count_likes = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    band = orm.relationship('Bands')
    user = orm.relationship('User')
