import pytz
from datetime import datetime
from nanoid import generate
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Float, Time
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings

key = settings.DB_SECRET_KEY

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(String(40), primary_key=True, default=generate)
    nome_completo = Column(StringEncryptedType(String(200), key), nullable=False)
    correio = Column(StringEncryptedType(String(200), key), unique=True, index=True, nullable=False)
    senha = Column(StringEncryptedType(String(200), key), nullable=False)
    telefone = Column(StringEncryptedType(String(200), key), nullable=True)
    role = Column(String(100), nullable=False) #"funcionario", "administrador"
    especialidade = Column(StringEncryptedType(String(100), key), nullable=True) 
    deleted = Column(Boolean, default=False)
    data_criacao = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.utc))
    data_atualizacao = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))
       
    auditorias = relationship("Auditoria", back_populates="usuario")
    consultas = relationship("Consulta", back_populates="usuario")
    
class Paciente(Base):
    __tablename__ = 'pacientes'
    
    id = Column(String(40), primary_key=True, default=generate)
    nome_completo = Column(StringEncryptedType(String(200), key), nullable=False)
    data_nascimento = Column(DateTime, nullable=False)
    bi = Column(StringEncryptedType(String(200), key), unique=True, nullable=False)
    sexo = Column(StringEncryptedType(String(200), key), unique=True, nullable=False)
    correio = Column(StringEncryptedType(String(200), key), unique=True, index=True, nullable=True)
    telefone = Column(StringEncryptedType(String(200), key), nullable=False)
    endereco = Column(StringEncryptedType(Text, key), nullable=False)
    deleted = Column(Boolean, default=False)
    data_criacao = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.utc))
    data_atualizacao = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))

    consultas = relationship("Consulta", back_populates="paciente")
    
class Relatorio(Base):
    __tablename__ = 'relatorios'
    
    id = Column(String(40), primary_key=True, default=generate)
    conteudo = Column(StringEncryptedType(Text, key), nullable=False)  # Relatório gerado pelo modelo de IA
    deleted = Column(Boolean, default=False)
    data_criacao = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.utc))
    data_atualizacao = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))

    consulta_id = Column(String(40), ForeignKey("consultas.id"), nullable=True)
    consulta = relationship("Consulta", back_populates="relatorios")
    
class Consulta(Base):
    __tablename__ = 'consultas'
    
    id = Column(String(40), primary_key=True, default=generate)
    diagnostico = Column(StringEncryptedType(Text, key), nullable=True)
    prescricoes = Column(StringEncryptedType(Text, key), nullable=True)
    tipo = Column(StringEncryptedType(String(100), key), nullable=False)  # Tipo da consulta (Ex: "Cardiologia", "Pediatria") -> especialidade do Usuario
    deleted = Column(Boolean, default=False)
    data_criacao = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.utc))
    data_atualizacao = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))
    
    paciente_id = Column(String(40), ForeignKey("pacientes.id"), nullable=True)
    paciente = relationship("Paciente", back_populates="consultas")
    
    usuario_id = Column(String(40), ForeignKey("usuarios.id"), nullable=True)
    usuario = relationship("Usuario", back_populates="consultas")

    
    relatorios = relationship("Relatorio", back_populates="consulta")


    
