from datetime import datetime
import pytz
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from typing import List, Optional
from app.models.relatorio import Consulta
from app.services.CRUDBase import CRUDBase
from app.schemas.consulta import ConsultaCreate, ConsultaUpdate

class CRUDConsulta(CRUDBase[Consulta]):
    async def get_by_id(self, db: AsyncSession, consulta_id: str) -> Optional[Consulta]:
        result = await db.execute(
            select(Consulta)
            .where(Consulta.id == consulta_id, Consulta.deleted == False)
        )
        return result.scalars().first()

crud_consulta = CRUDConsulta(Consulta)


async def get_consulta(db: AsyncSession, consulta_id: str) -> Optional[Consulta]:
    result = await db.execute(
        select(Consulta)
        .options(
            selectinload(Consulta.paciente),
            selectinload(Consulta.usuario)
            )  # Carregar o paciente associado à consulta
        .where(Consulta.id == consulta_id, Consulta.deleted == False)
    )
    return result.scalars().first()


async def get_consultas(db: AsyncSession) -> List[Consulta]:
    result = await db.execute(
        select(Consulta)
        .options(
            selectinload(Consulta.paciente),
            selectinload(Consulta.usuario)
            )  # Carregar o paciente associado a cada consulta
        .where(Consulta.deleted == False)
    )
    return result.unique().scalars().all()


async def create_consulta(db: AsyncSession, consulta_data: ConsultaCreate) -> Consulta:
    consulta = Consulta(
        paciente_id=consulta_data.paciente_id,
        usuario_id=consulta_data.usuario_id,
        prescricoes=consulta_data.prescricoes,
        diagnostico=consulta_data.diagnostico,
        tipo=consulta_data.tipo,
        deleted=False,
        data_criacao=datetime.now(pytz.utc),
        data_atualizacao=datetime.now(pytz.utc)
    )

    db.add(consulta)
    await db.commit()
    await db.refresh(consulta)

    return consulta


async def update_consulta(
    db: AsyncSession, consulta_id: str, consulta_data: ConsultaUpdate
) -> Optional[Consulta]:
    consulta = await get_consulta(db, consulta_id)
    if not consulta:
        return None
    for field, value in consulta_data.dict(exclude_unset=True).items():
        setattr(consulta, field, value)

    await db.commit()
    await db.refresh(consulta)

    return consulta


async def delete_consulta(db: AsyncSession, consulta_id: str) -> Consulta:
    return await crud_consulta.delete(db, consulta_id)

