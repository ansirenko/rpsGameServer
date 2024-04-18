from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__: str = 'users'
    user_id: int = Column(Integer, primary_key=True, autoincrement=True)
    nickname: str = Column(String(255), unique=True, nullable=False)
    password: str = Column(String(255), nullable=False)

    sessions_as_player1 = relationship('GameSession', foreign_keys='GameSession.player1_id')
    sessions_as_player2 = relationship('GameSession', foreign_keys='GameSession.player2_id')

    stats = relationship('GameStat', back_populates='user', uselist=False)


class GameSession(Base):
    __tablename__: str = 'game_sessions'
    session_id: int = Column(Integer, primary_key=True, autoincrement=True)
    player1_id: int = Column(Integer, ForeignKey('users.user_id'))
    player2_id: int = Column(Integer, ForeignKey('users.user_id'))
    player1_move: str = Column(Enum('rock', 'paper', 'scissors'))
    player2_move: str = Column(Enum('rock', 'paper', 'scissors'))
    status: str = Column(Enum('waiting', 'completed', 'timeout', name='game_statuses'), default='waiting')


class GameStat(Base):
    __tablename__: str = 'game_stats'
    user_id: int = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    wins: int = Column(Integer, default=0)
    losses: int = Column(Integer, default=0)
    draws: int = Column(Integer, default=0)
    last_game_session_id: int = Column(Integer, nullable=True)

    user = relationship('User', back_populates='stats')

