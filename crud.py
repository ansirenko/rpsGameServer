import bcrypt
from sqlalchemy.orm import Session
import schemas
import models


def get_user_by_nickname(db: Session, nickname: str):
    return db.query(models.User).filter(models.User.nickname == nickname).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    db_user = models.User(nickname=user.nickname, password=hashed_password.decode('utf-8'))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    initial_stats = models.GameStat(user_id=db_user.user_id, wins=0, losses=0, draws=0)
    db.add(initial_stats)
    db.commit()

    return db_user


def check_password(user_password, stored_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), stored_password.encode('utf-8'))


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def get_user_stats(db: Session, user_id: int):
    return db.query(models.GameStat).filter(models.GameStat.user_id == user_id).first()
