import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Bands(SqlAlchemyBase):
    __tablename__ = 'bands'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    biography = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    photo = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    user = orm.relationship('User')
    songs = orm.relationship("Songs", back_populates='band')
