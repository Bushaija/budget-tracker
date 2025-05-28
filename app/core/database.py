from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
from typing import Generator

# create engine
engine = create_engine(
	settings.DATABASE_URL,
	echo=settings.DEBUG,
	pool_pre_ping=True,
	pool_recycle=300,
)

# create session maker
SessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=engine,
	class_=Session
)

def create_db_and_table():
	"""create database tables"""
	SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
	"""Dependency to get database session"""
	with SessionLocal() as session:
		yield session
