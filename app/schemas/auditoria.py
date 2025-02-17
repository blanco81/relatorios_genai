from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class AuditoriaBase(BaseModel):
    acao: str
    data_criacao: Optional[datetime] = None


class AuditoriaCreate(AuditoriaBase):
    pass


class AuditoriaUpdate(AuditoriaBase):
    acao: Optional[str]
    data_criacao: Optional[datetime]


class AuditoriaResponse(AuditoriaBase):
    id: str
    usuario_id: str

    class Config:
        orm_mode = True