from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.auditoria import Auditoria
from app.schemas.paciente import PacienteCreate, PacienteResponse, PacienteUpdate
from app.services.paciente import get_paciente, get_pacientes, create_paciente, update_paciente, delete_paciente
from app.services.usuario import get_users
from app.core.deps import get_db
from app.core.dependencies import get_current_user
from app.models.relatorio import Usuario

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/all", response_model=List[PacienteResponse])
async def read_pacientes(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        pacientes = await get_pacientes(db)
        if not pacientes:
            request.session.setdefault("notifications", []).append("Criar Pacientes.")
            return RedirectResponse(url="/pacientes/create", status_code=status.HTTP_303_SEE_OTHER)
        else:
            return templates.TemplateResponse(
                "/paciente/list_paciente.html",
                {"request": request, "pacientes": pacientes, "current_user": current_user}
            )
    else:
        request.session.setdefault("notifications", []).append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/details/{paciente_id}")
async def paciente_details(
    paciente_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        paciente = await get_paciente(db, paciente_id)
        
        if not paciente:
            return JSONResponse(content={"status": "error", "message": "Paciente não encontrado."}, status_code=404)
        
        consultas_associadas = [
            {
                "id": consulta.id, 
                "data_consulta": consulta.data_criacao, 
                "diagnostico": consulta.diagnostico,
                "prescricoes": consulta.prescricoes
            } 
            for consulta in paciente.consultas
            ]
        
        return {
            "nome_completo": paciente.nome_completo,
            "data_nascimento": paciente.data_nascimento,
            "bi": paciente.bi,
            "sexo": paciente.sexo,
            "correio": paciente.correio,
            "telefone": paciente.telefone,
            "endereco": paciente.endereco,
            "data_criacao": paciente.data_criacao,
            "consultas": consultas_associadas
        }
    else:
        return JSONResponse(content={"status": "admin"})

@router.get("/create")
async def create_paciente_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        usuarios = await get_users(db)
        return templates.TemplateResponse("/paciente/create_paciente.html", {"request": request, "usuarios": usuarios, "current_user": current_user})
    else:
        request.session.setdefault("notifications", []).append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/create", response_model=PacienteResponse)
async def criar_paciente(
    request: Request,
    nome_completo: str = Form(...),
    data_nascimento: date = Form(...),
    bi: str = Form(...),
    sexo: str = Form(...),
    correio: Optional[str] = Form(None),
    telefone: str = Form(...),
    endereco: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        paciente_data = PacienteCreate(
            nome_completo=nome_completo,
            data_nascimento=data_nascimento,
            bi=bi,
            sexo=sexo,
            correio=correio,
            telefone=telefone,
            endereco=endereco
        )
        created_paciente = await create_paciente(db, paciente_data)
        if created_paciente:
            db_log = Auditoria(
                acao=f"Paciente '{created_paciente.nome_completo}' foi registrado.",
                data_criacao=datetime.now(pytz.utc),
                usuario_id=current_user.id
            )
            db.add(db_log)
            await db.commit()
            await db.refresh(db_log)
            
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Paciente criado com sucesso.")
            return RedirectResponse(url="/pacientes/all", status_code=status.HTTP_303_SEE_OTHER)
        else:
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Erro ao criar o paciente.")
            return RedirectResponse(url="/pacientes/all", status_code=status.HTTP_303_SEE_OTHER)
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/edit/{paciente_id}")
async def edit_paciente(
    paciente_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        paciente = await get_paciente(db, paciente_id)
        
        if paciente is None:
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Paciente não encontrado.")
            return RedirectResponse(url="/pacientes/all", status_code=status.HTTP_303_SEE_OTHER)
        
        if paciente:
            return templates.TemplateResponse(
                "/paciente/edit_paciente.html",
                {
                    "request": request,
                    "paciente": paciente,
                    "current_user": current_user
                }
            )
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/edit/{paciente_id}", response_model=PacienteResponse)
async def editing_paciente(
    request: Request,
    paciente_id: str,
    nome_completo: str = Form(...),
    data_nascimento: date = Form(...),
    bi: str = Form(...),
    sexo: str = Form(...),
    correio: Optional[str] = Form(None),
    telefone: str = Form(...),
    endereco: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        paciente_data = PacienteUpdate(
            nome_completo=nome_completo,
            data_nascimento=data_nascimento,
            bi=bi,
            sexo=sexo,
            correio=correio,
            telefone=telefone,
            endereco=endereco
        )
        updated_paciente = await update_paciente(db, paciente_id, paciente_data)
        
        if updated_paciente:
            db_log = Auditoria(
                acao=f"Paciente '{updated_paciente.nome_completo}' foi atualizado.",
                data_criacao=datetime.now(pytz.utc),
                usuario_id=current_user.id
            )
            db.add(db_log)
            await db.commit()
            await db.refresh(db_log)
            
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Paciente atualizado.")
            return RedirectResponse(url="/pacientes/all", status_code=status.HTTP_303_SEE_OTHER)
        else:
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Erro ao atualizar o Paciente.")
            return RedirectResponse(url="/pacientes/all", status_code=status.HTTP_303_SEE_OTHER)
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/delete/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_paciente(
    request: Request,
    paciente_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador"]:
        paciente_deleted = await delete_paciente(db, paciente_id)
        
        if paciente_deleted:
            db_log = Auditoria(
                acao=f"Paciente '{paciente_deleted.nome_completo}' foi eliminado.",
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