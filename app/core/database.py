import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

load_dotenv()

DATABASE_URL = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"


engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    future=True,
)

async_session = sessionmaker(
    engine,
    expire_on_commit=False, 
    class_=AsyncSession, 
    future=True
)

metadata = MetaData()
Base = declarative_base(metadata=metadata)


