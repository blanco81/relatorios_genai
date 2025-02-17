from datetime import datetime
import pytz
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from typing import List, Optional
from app.models.relatorio import Paciente, Consulta
from app.services.CRUDBase import CRUDBase
from app.schemas.paciente import PacienteCreate, PacienteUpdate  

class CRUDPaciente(CRUDBase[Paciente]):
    async def get_by_name(self, db: AsyncSession, nome_completo: str) -> Optional[Paciente]:
        result = await db.execute(
            select(Paciente)
            .where(Paciente.nome_completo == nome_completo, Paciente.deleted == False)
        )
        return result.scalars().first()

crud_paciente = CRUDPaciente(Paciente)


async def get_paciente(db: AsyncSession, paciente_id: str) -> Optional[Paciente]:
    result = await db.execute(
        select(Paciente)
        .options(
            selectinload(Paciente.consultas),  # Carregar as consultas associadas ao paciente
        )
        .where(Paciente.id == paciente_id, Paciente.deleted == False)
    )
    return result.scalars().first()


async def get_pacientes(db: AsyncSession) -> List[Paciente]:
    result = await db.execute(
        select(Paciente)
        .options(
            selectinload(Paciente.consultas),  # Carregar as consultas associadas a cada paciente
        )
        .where(Paciente.deleted == False)
    )
    return result.unique().scalars().all()


async def create_paciente(db: AsyncSession, paciente_data: PacienteCreate) -> Paciente:
    # Criar o paciente
    paciente = Paciente(
        nome_completo=paciente_data.nome_completo,
        data_nascimento=paciente_data.data_nascimento,
        bi=paciente_data.bi,
        sexo=paciente_data.sexo,
        correio=paciente_data.correio,
        telefone=paciente_data.telefone,
        endereco=paciente_data.endereco,
        deleted=False,
        data_criacao=datetime.now(pytz.utc),
        data_atualizacao=datetime.now(pytz.utc)
    )
    
    # Guardar o paciente na base de dados
    db.add(paciente)
    await db.commit()
    await db.refresh(paciente)

    return paciente


async def update_paciente(
    db: AsyncSession, paciente_id: str, paciente_data: PacienteUpdate
) -> Optional[Paciente]:
    paciente = await get_paciente(db, paciente_id)
    if not paciente:
        return None
    for field, value in paciente_data.dict(exclude_unset=True).items():
        setattr(paciente, field, value)

    await db.commit()
    await db.refresh(paciente)

    return paciente


async def delete_paciente(db: AsyncSession, paciente_id: str) -> Paciente:
    return await crud_paciente.delete(db, paciente_id)