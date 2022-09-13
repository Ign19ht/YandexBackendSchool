import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

db_host = os.environ.get('POSTGRES_HOST')
db_port = os.environ.get('POSTGRES_PORT') or 5432
db_name = os.environ.get('POSTGRES_DB')
db_user = os.environ.get('POSTGRES_USER')
db_pass = os.environ.get('POSTGRES_PASSWORD')

SQLALCHEMY_DATABASE_URL = \
    f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
DeclarativeBase = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db():
    DeclarativeBase.metadata.create_all(engine)


def get_db():
    return SessionLocal()
