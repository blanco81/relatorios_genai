# app/routers/dashboard.py
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func, extract
from sqlalchemy.future import select
from collections import defaultdict
from app.core.deps import get_db
from app.core.dependencies import get_current_user
from app.models.relatorio import Usuario, Paciente
from app.models.auditoria import Auditoria
from app.schemas.auditoria import AuditoriaResponse
from decimal import Decimal



router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

    
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador", "Funcionario"]:
        
        

        return templates.TemplateResponse(
            "core/dashboard.html",
            {
                "request": request,
                "current_user": current_user
            }
        )
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append(f"Acesso negado ao sistema.")
        return RedirectResponse(
            url="/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )
    
    
@router.get("/auditoria", response_model=list[AuditoriaResponse])
async def list_auditoria(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador"]:
        query = (
            select(Auditoria)
            .options(
                joinedload(Auditoria.usuario)
            )
        )
        result = await db.execute(query)
        auditorias = result.unique().scalars().all()

        
        return templates.TemplateResponse(
            "/core/list_auditoria.html",
            {
                "request": request,
                "auditorias": auditorias,
                "current_user": current_user,
            },
        )
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append(f"Acesso limitado nesta página.")
        return RedirectResponse(
            url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER
        )


@router.post("/clear-notifications")
async def clear_notifications(request: Request):
    request.session.pop("notifications", None)
    return {"status": "cleared"}