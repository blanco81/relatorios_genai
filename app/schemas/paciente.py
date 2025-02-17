from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime

class PacienteBase(BaseModel):
    nome_completo: str = Field(..., max_length=200)
    data_nascimento: date = Field(...)
    bi: str = Field(..., max_length=20)
    sexo: str = Field(..., max_length=20)
    correio: Optional[EmailStr] = Field(...)
    telefone: str = Field(..., max_length=20)
    endereco: str = Field(...)
    deleted: bool = Field(default=False)

class PacienteCreate(PacienteBase):
    pass

class PacienteUpdate(BaseModel):
    nome_completo: Optional[str] = Field(None, max_length=200)
    data_nascimento: Optional[date] = Field(None)
    bi: Optional[str] = Field(None, max_length=20)
    sexo: Optional[str] = Field(None, max_length=20)
    correio: Optional[EmailStr] = Field(...)
    telefone: Optional[str] = Field(None, max_length=20)
    endereco: Optional[str] = Field(None)
    deleted: Optional[bool] = Field(None)

class PacienteResponse(PacienteBase):
    id: str
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        orm_mode = True