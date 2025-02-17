from pydantic import BaseModel
from datetime import datetime

class RelatorioOut(BaseModel):
    id: str
    conteudo: str
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        orm_mode = True
