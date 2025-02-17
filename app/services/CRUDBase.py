from typing import Optional, TypeVar, Generic, Type, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from app.core.database import Base

# Tipo genérico para os modelos
T = TypeVar('T', bound='Base')

class CRUDBase(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def create(self, db: AsyncSession, obj_in: dict) -> T:
        """
        Cria um novo registro no banco de dados de forma assíncrona.
        """
        db_obj = self.model(**obj_in)  # Cria uma instância do modelo com os dados fornecidos
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: str) -> T:
        """
        Retorna um registro pelo ID de forma assíncrona.
        """
        result = await db.execute(select(self.model).where(self.model.id == id, self.model.deleted == False))
        return result.scalars().first()
    

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        load_relationships: Optional[List[str]] = None,
        relationship_style: str = "selectin"
    ) -> List[T]:
        """
        Retorna uma lista de registros com paginação de forma assíncrona.
        
        :param db: Sesión asíncrona de SQLAlchemy.
        :param skip: Número de registros a omitir (paginación).
        :param limit: Número máximo de registros a retornar.
        :param load_relationships: Lista de nombres de relaciones a cargar.
        :param relationship_style: Estilo de carga de relaciones ("selectin" o "joined").
        :return: Lista de registros del modelo.
        """
        # Construir la consulta base
        stmt = select(self.model).where(self.model.deleted == False)
        
        # Cargar relaciones si se especifican
        if load_relationships:
            for rel in load_relationships:
                if relationship_style == "selectin":
                    stmt = stmt.options(selectinload(getattr(self.model, rel)))
                elif relationship_style == "joined":
                    stmt = stmt.options(joinedload(getattr(self.model, rel)))
                else:
                    raise ValueError("relationship_style debe ser 'selectin' o 'joined'")
        
        # Aplicar paginación
        stmt = stmt.offset(skip).limit(limit)
        
        # Ejecutar la consulta
        result = await db.execute(stmt)
        
        # Retornar los resultados
        return result.unique().scalars().all()

    async def update(self, db: AsyncSession, id: str, obj_in: dict) -> T:
        """
        Atualiza um registro existente de forma assíncrona.
        """
        result = await db.execute(select(self.model).where(self.model.id == id, self.model.deleted == False))
        db_obj = result.scalars().first()
        if db_obj:
            for key, value in obj_in.items():
                setattr(db_obj, key, value)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: str) -> T:
        """
        Remove soft de um registro do banco de dados de forma assíncrona.
        """
        result = await db.execute(select(self.model).where(self.model.id == id, self.model.deleted == False))
        db_obj = result.scalars().first()
        if db_obj:      
            db_obj.deleted = True
        await db.commit()
        return db_obj