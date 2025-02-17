from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

class UsuarioBase(BaseModel):
    nome_completo: str = Field(..., max_length=200)
    role: str = Field(..., max_length=100)
    telefone: Optional[str] = Field(None, max_length=200)
    especialidade: str = Field(..., max_length=100)

class UsuarioCreate(UsuarioBase):
    correio: EmailStr = Field(...)    
    senha: str = Field(..., max_length=200)

class UsuarioUpdate(BaseModel):
    nome_completo: Optional[str] = Field(None, max_length=200)
    correio: Optional[EmailStr] = Field(None)
    senha: Optional[str] = Field(None, max_length=200)
    telefone: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, max_length=100)
    especialidade: Optional[str] = Field(..., max_length=100)

class UsuarioResponse(UsuarioBase):
    id: str
    correio: EmailStr
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        orm_mode = True