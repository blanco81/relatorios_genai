from datetime import datetime
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from app.models.auditoria import Auditoria
from app.models.relatorio import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from typing import List


async def get_user(db: AsyncSession, usuario_id: str) -> Usuario:    
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id, Usuario.deleted == False))
    usuario = result.scalars().first()      
    return usuario

async def get_user_by_email(db: AsyncSession, correio: str) -> Usuario:
    result = await db.execute(select(Usuario).where(Usuario.correio == correio, Usuario.deleted == False))
    usuario = result.scalars().first()        
    return usuario

async def get_users(db: AsyncSession) -> List[Usuario]:
    
    query = (select(Usuario)
            .options(
                selectinload(Usuario.auditorias)
                )
            .where(Usuario.deleted == False)
    )
    result = await db.execute(query)        
    usuarios = result.unique().scalars().all()    
    return usuarios 

async def get_users_by_role(db: AsyncSession) -> List[Usuario]:
    query = (
    select(Usuario)
    .where(
        Usuario.deleted == False,
        Usuario.role.in_(["Administrador", "Funcionario"])
    )
)
    result = await db.execute(query)        
    usuarios = result.scalars().all()  
    return usuarios  

async def create_user(db: AsyncSession, usuario: UsuarioCreate) -> Usuario:     
    user_data = usuario.dict(exclude_unset=True)
    db_usuario = Usuario(**user_data)      
    db.add(db_usuario)
    await db.commit()
    await db.refresh(db_usuario)
    
    db_log = Auditoria(
        acao=f"Usuario '{db_usuario.nome_completo}'  foi criado.",
        data_criacao=datetime.now(pytz.utc),
        usuario_id=db_usuario.id
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    
    return db_usuario

async def update_user(db: AsyncSession, usuario_id: str, usuario_data: UsuarioUpdate):
    usuario = await get_user(db, usuario_id)
    if usuario:
        for field, value in usuario_data.dict(exclude_unset=True).items():
            if value is not None:  # Atualiza apenas campos com valores não nulos
                setattr(usuario, field, value)       
        await db.commit() 
        await db.refresh(usuario) 
        
    db_log = Auditoria(
        acao=f"Usuario '{usuario.nome_completo}'  foi atualizado.",
        data_criacao=datetime.now(pytz.utc),
        usuario_id=usuario.id
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
        
    return usuario

async def delete_user(db: AsyncSession, usuario_id: str) -> bool:
    db_usuario = await get_user(db, usuario_id)
    if not db_usuario:
        return False  
    db_usuario.deleted = True  
    await db.commit()
    
    db_log = Auditoria(
        acao=f"Usuario '{db_usuario.nome_completo}' foi eliminado.",
        data_criacao=datetime.now(pytz.utc),
        usuario_id=db_usuario.id
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
        
    return True 


async def search_users(db: AsyncSession, query: str) -> List[Usuario]:
    result = await db.execute(select(Usuario).where(Usuario.deleted == True))
    all_usuarios = result.scalars().all()    
    filtered_usuarios = [
        usuario for usuario in all_usuarios 
        if query.lower() in Usuario.nome.lower()        
    ]
    return filtered_usuarios