from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@db/rock_paper_scissors"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    isolation_level="READ UNCOMMITTED",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
