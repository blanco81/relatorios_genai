# app/core/deps.py
from contextvars import ContextVar
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session
from contextlib import asynccontextmanager

session_context_var: ContextVar[Optional[AsyncSession]] = ContextVar("_session", default=None)

@asynccontextmanager
async def set_db() -> AsyncGenerator[AsyncSession, None]:
    """Store db session and reset it"""
    async with async_session() as db:  # Use async with for async_session
        yield db  # Yield the database session for use
        # No need for manual close, as async_session will handle it

async def get_db():
    async with async_session() as session:
        yield session
