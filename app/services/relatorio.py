import openai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.relatorio import Consulta, Paciente, Relatorio, Usuario
from app.core.config import settings

openai.api_key = settings.OPENAI_API_KEY


async def get_relatorio(db: AsyncSession, relatorio_id: str) -> Optional[Relatorio]:
    result = await db.execute(
        select(Relatorio)
        .options(
            selectinload(Relatorio.consulta)  # Carregar a consulta associada ao relatório
        )
        .where(Relatorio.id == relatorio_id, Relatorio.deleted == False)
    )
    return result.scalars().first()

async def get_relatorios(db: AsyncSession) -> List[Relatorio]:
    result = await db.execute(
        select(Relatorio)
        .options(
            selectinload(Relatorio.consulta)  # Carregar a consulta associada ao relatório
            .selectinload(Consulta.usuario),  # Carregar o usuário (médico) da consulta
            selectinload(Relatorio.consulta)
            .selectinload(Consulta.paciente)  # Carregar o paciente da consulta
        )
        .where(Relatorio.deleted == False)
    )
    return result.unique().scalars().all()


async def delete_relatorio(db: AsyncSession, relatorio_id: str) -> Relatorio:
        result = await db.execute(select(Relatorio).where(Relatorio.id == relatorio_id, Relatorio.deleted == False))
        db_obj = result.scalars().first()
        if db_obj:      
            db_obj.deleted = True
        await db.commit()
        return db_obj