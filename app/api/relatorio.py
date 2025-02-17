from openai import AsyncOpenAI  # Importar o cliente assíncrono da OpenAI
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from typing import List
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
from app.core.dependencies import get_current_user
from app.core.deps import get_db
from app.models.auditoria import Auditoria
from app.models.relatorio import Consulta, Usuario, Paciente, Relatorio
from app.schemas.relatorio import RelatorioOut
from app.services.paciente import get_pacientes
from app.services.consulta import get_consultas
from app.services.relatorio import get_relatorio, get_relatorios, delete_relatorio
from app.core.config import settings
from datetime import datetime
import pytz

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def gerar_relatorio_openai(
    diagnostico: str, 
    prescricoes: str, 
    especialidade: str, 
    paciente_nome: str, 
    paciente_sexo: str, 
    paciente_idade: int,
    medico_nome: str
) -> str:
    prompt = f"""
    Geração de um relatório médico detalhado para uma consulta de {especialidade}.

    **Dados do Paciente:**
    - Nome: {paciente_nome}
    - Sexo: {paciente_sexo}
    - Idade: {paciente_idade} anos

    **Diagnóstico:**
    {diagnostico}

    **Prescrições Médicas:**
    {prescricoes}

    **Médico Responsável:**
    {medico_nome}
    
   
    **Assinatura:** ____________________  
    **CRM:** [Número do registro do médico]

    **Elabore um relatório clínico detalhado com base nas informações acima, considerando os seguintes aspectos:**
    1️**Resumo Clínico**: Apresente uma introdução ao caso com base no diagnóstico e prescrição.  
    2️**Histórico Médico e Sintomas**: Explique a condição do paciente, sintomas relatados e fatores relevantes.  
    3️**Plano de Tratamento**: Sugira abordagens terapêuticas e recomendações baseadas no diagnóstico.  
    4️**Recomendações Médicas**: Indique cuidados necessários, mudanças no estilo de vida ou exames complementares.  
    5️**Prognóstico**: Informe as expectativas de evolução da condição do paciente.  
    """

    response = await client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": "Você é um assistente médico especializado na geração de relatórios clínicos completos."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800, 
        temperature=0.7,  
    )

    return response.choices[0].message.content.strip()



@router.get("/all", response_model=List[RelatorioOut])
async def read_relatorios(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        relatorios = await get_relatorios(db)
        
        return templates.TemplateResponse(
            "/relatorio/list_relatorio.html",
            {"request": request, "relatorios": relatorios, "current_user": current_user}
        )
    else:
        request.session.setdefault("notifications", []).append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    

    
@router.get("/create")
async def create_relatorio_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        consultas = await get_consultas(db)
        
        return templates.TemplateResponse(
            "/relatorio/create_relatorio.html", 
            {
                "request": request, 
                "consultas": consultas,
                "current_user": current_user
            }
        )
    else:
        request.session.setdefault("notifications", []).append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    
    
@router.get("/details/{relatorio_id}")
async def get_relatorio_details(
    request: Request,
    relatorio_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
    ):
    if current_user.role in ["Administrador", "Funcionario"]:
        result = await db.execute(
            select(Relatorio)
            .options(
                selectinload(Relatorio.consulta)
                .selectinload(Consulta.paciente), 
                selectinload(Relatorio.consulta)
                .selectinload(Consulta.usuario)  
            )
            .where(Relatorio.id == relatorio_id, Relatorio.deleted == False)
        )

        relatorio = result.scalars().first()

        if not relatorio:
            raise HTTPException(status_code=404, detail="Relatório não encontrado")

        return {
            "id": relatorio.id,
            "conteudo": relatorio.conteudo,
            "data_criacao": relatorio.data_criacao,
            "consulta": {
                "tipo": relatorio.consulta.tipo,
                "paciente": {
                    "nome_completo": relatorio.consulta.paciente.nome_completo,
                    "data_nascimento": relatorio.consulta.paciente.data_nascimento,
                    "sexo": relatorio.consulta.paciente.sexo,
                },
                "usuario": {
                    "nome_completo": relatorio.consulta.usuario.nome_completo,
                    "especialidade": relatorio.consulta.usuario.especialidade,
                },
            },
        }
    else:
        request.session.setdefault("notifications", []).append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/gerar-relatorio/{consulta_id}")
async def gerar_relatorio(
    request: Request,
    consulta_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
    ):
    
    if current_user.role in ["Administrador", "Funcionario"]:
        consulta = await db.execute(
            select(Consulta)
            .options(
                selectinload(Consulta.paciente),
                selectinload(Consulta.usuario)
            )
            .where(Consulta.id == consulta_id, Consulta.deleted == False)
        )
        consulta = consulta.scalars().first()
    
        if not consulta:
            raise HTTPException(status_code=404, detail="Consulta não encontrada")
        
        paciente = consulta.paciente
        usuario = consulta.usuario
        
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Médico não encontrado")
        
        idade_paciente = (datetime.now() - paciente.data_nascimento).days // 365
        
        relatorio_gerado = await gerar_relatorio_openai(
            diagnostico=consulta.diagnostico,
            prescricoes=consulta.prescricoes,
            especialidade=consulta.tipo,
            paciente_nome=paciente.nome_completo,
            paciente_sexo=paciente.sexo,
            paciente_idade=idade_paciente,
            medico_nome=usuario.nome_completo
        )
        
        relatorio = Relatorio(
            conteudo=relatorio_gerado, 
            consulta_id=consulta.id
        )
        
        db.add(relatorio)
        await db.commit()
        await db.refresh(relatorio)
        
        db_log = Auditoria(
                acao=f"Relatorio com data '{relatorio.data_criacao}', foi gerado.",
                data_criacao=datetime.now(pytz.utc),
                usuario_id=current_user.id
            )
        db.add(db_log)
        await db.commit()
        await db.refresh(db_log)

        return {
            "id": relatorio.id,
            "conteudo": relatorio.conteudo,
            "data_criacao": relatorio.data_criacao,
            "consulta": {
                "tipo": consulta.tipo,
                "diagnostico": consulta.diagnostico,
                "prescricoes": consulta.prescricoes,
                "paciente": {
                    "nome_completo": paciente.nome_completo,
                    "data_nascimento": paciente.data_nascimento,
                    "sexo": paciente.sexo,
                },
                "usuario": {
                    "nome_completo": usuario.nome_completo,
                    "especialidade": usuario.especialidade,
                },
            },
        }
    else:
        request.session.setdefault("notifications", []).append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/delete/{relatorio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_consulta(
    request: Request,
    relatorio_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        relatorio_deleted = await delete_relatorio(db, relatorio_id)
        
        if relatorio_deleted:
            db_log = Auditoria(
                acao=f"Relatorio com data '{relatorio_deleted.data_criacao}', foi eliminado.",
                data_criacao=datetime.now(pytz.utc),
                usuario_id=current_user.id
            )
            db.add(db_log)
            await db.commit()
            await db.refresh(db_log)
            
            return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content={"status": "error"}, status_code=status.HTTP_404_NOT_FOUND)
    else:
        return JSONResponse(content={"status": "admin"})

@router.post("/clear-notifications")
async def clear_notifications(request: Request):
    request.session.pop("notifications", None)
    return {"status": "cleared"}