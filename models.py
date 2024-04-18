from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    sessions_as_player1 = relationship('GameSession', foreign_keys='GameSession.player1_id')
    sessions_as_player2 = relationship('GameSession', foreign_keys='GameSession.player2_id')

    stats = relationship('GameStat', back_populates='user', uselist=False)


class GameSession(Base):
    __tablename__ = 'game_sessions'
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    player1_id = Column(Integer, ForeignKey('users.user_id'))
    player2_id = Column(Integer, ForeignKey('users.user_id'))
    player1_move = Column(Enum('rock', 'paper', 'scissors'))
    player2_move = Column(Enum('rock', 'paper', 'scissors'))
    status = Column(Enum('waiting', 'completed', 'timeout', name='game_statuses'), default='waiting')


class GameStat(Base):
    __tablename__: str = 'game_stats'
    user_id: int = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    wins: int = Column(Integer, default=0)
    losses: int = Column(Integer, default=0)
    draws: int = Column(Integer, default=0)
    last_game_session_id: int = Column(Integer, nullable=True)

    user = relationship('User', back_populates='stats')

