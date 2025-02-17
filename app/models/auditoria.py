import pytz
from datetime import datetime
from nanoid import generate
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(String(40), primary_key=True, default=generate)
    acao = Column(String(200), nullable=False) 
    data_criacao = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(pytz.utc))  # Data de criação
    
    usuario_id = Column(String(40), ForeignKey("usuarios.id"))
    usuario = relationship("Usuario", back_populates="auditorias", lazy="selectin")
    
    
