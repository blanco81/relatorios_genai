from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.auditoria import Auditoria
from app.schemas.consulta import ConsultaCreate, ConsultaUpdate, ConsultaResponse
from app.services.consulta import get_consulta, get_consultas, create_consulta, update_consulta, delete_consulta
from app.services.usuario import get_users, get_user
from app.services.paciente import get_pacientes
from app.core.deps import get_db
from app.core.dependencies import get_current_user
from app.models.relatorio import Usuario

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/all", response_model=List[ConsultaResponse])
async def read_consultas(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        consultas = await get_consultas(db)
        if not consultas:
            request.session.setdefault("notifications", []).append("Criar Consultas.")
            return RedirectResponse(url="/consultas/create", status_code=status.HTTP_303_SEE_OTHER)
        else:
            return templates.TemplateResponse(
                "/consulta/list_consulta.html",
                {"request": request, "consultas": consultas, "current_user": current_user}
            )
    else:
        request.session.setdefault("notifications", []).append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/details/{consulta_id}")
async def consulta_details(
    consulta_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        consulta = await get_consulta(db, consulta_id)
        
        if not consulta:
            return JSONResponse(content={"status": "error", "message": "Consulta não encontrada."}, status_code=404)        
       
        
        return {
            "tipo": consulta.tipo,
            "data_criacao": consulta.data_criacao,
            "diagnostico": consulta.diagnostico,
            "prescricoes": consulta.prescricoes,
            "paciente": {
                "nome_completo": consulta.paciente.nome_completo,
                "data_nascimento": consulta.paciente.data_nascimento,
                "bi": consulta.paciente.bi,
                "sexo": consulta.paciente.sexo,
                "correio": consulta.paciente.correio,
                "telefone": consulta.paciente.telefone,
                "endereco": consulta.paciente.endereco,
            }
        }
    else:
        return JSONResponse(content={"status": "admin"})

@router.get("/create")
async def create_consulta_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        pacientes = await get_pacientes(db)
        return templates.TemplateResponse("/consulta/create_consulta.html", {"request": request, "pacientes": pacientes, "current_user": current_user})
    else:
        request.session.setdefault("notifications", []).append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/create", response_model=ConsultaResponse)
async def criar_consulta(
    request: Request,
    paciente_id: str = Form(...),
    diagnostico: str = Form(...),
    prescricoes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        
        usuario_especialidade = await get_user(db, current_user.id)
        
        consulta_data = ConsultaCreate(
            tipo=usuario_especialidade.especialidade,
            paciente_id=paciente_id,
            usuario_id=current_user.id,
            diagnostico=diagnostico,
            prescricoes=prescricoes
        )
        created_consulta = await create_consulta(db, consulta_data)
        if created_consulta:
            db_log = Auditoria(
                acao=f"Consulta de '{created_consulta.tipo}' foi registrada.",
                data_criacao=datetime.now(pytz.utc),
                usuario_id=current_user.id
            )
            db.add(db_log)
            await db.commit()
            await db.refresh(db_log)
            
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Consulta criada com sucesso.")
            return RedirectResponse(url="/consultas/all", status_code=status.HTTP_303_SEE_OTHER)
        else:
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Erro ao criar consulta.")
            return RedirectResponse(url="/consultas/all", status_code=status.HTTP_303_SEE_OTHER)
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/edit/{consulta_id}")
async def edit_consulta(
    consulta_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        consulta = await get_consulta(db, consulta_id)
        
        if consulta is None:
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Consulta não encontrada.")
            return RedirectResponse(url="/consultas/all", status_code=status.HTTP_303_SEE_OTHER)
        
        if consulta:
            return templates.TemplateResponse(
                "/consulta/edit_consulta.html",
                {
                    "request": request,
                    "consulta": consulta,
                    "current_user": current_user
                }
            )
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/edit/{consulta_id}", response_model=ConsultaResponse)
async def editing_consulta(
    request: Request,
    consulta_id: str,
    paciente_id: str = Form(...),
    diagnostico: str = Form(...),
    prescricoes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        
        usuario_especialidade = await get_user(db, current_user.id)
        
        consulta_data = ConsultaUpdate(
            tipo=usuario_especialidade.especialidade,
            paciente_id=paciente_id,
            usuario_id=current_user.id,
            diagnostico=diagnostico,
            prescricoes=prescricoes
        )
        updated_consulta = await update_consulta(db, consulta_id, consulta_data)
        
        if updated_consulta:
            db_log = Auditoria(
                acao=f"Consulta de '{updated_consulta.tipo}' foi atualizada.",
                data_criacao=datetime.now(pytz.utc),
                usuario_id=current_user.id
            )
            db.add(db_log)
            await db.commit()
            await db.refresh(db_log)
            
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Consulta atualizada.")
            return RedirectResponse(url="/consultas/all", status_code=status.HTTP_303_SEE_OTHER)
        else:
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Erro ao atualizar consulta.")
            return RedirectResponse(url="/consultas/all", status_code=status.HTTP_303_SEE_OTHER)
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/delete/{consulta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_consulta(
    request: Request,
    consulta_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador"]:
        consulta_deleted = await delete_consulta(db, consulta_id)
        
        if consulta_deleted:
            db_log = Auditoria(
                acao=f"Consulta de '{consulta_deleted.tipo}' foi eliminada.",
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
