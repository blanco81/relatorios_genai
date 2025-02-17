from fastapi import APIRouter, Depends, status, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.usuario import get_user_by_email
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("/core/login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
    correio: str = Form(...),
    senha: str = Form(...)
):
    db_user = await get_user_by_email(db, correio)      
    if not db_user:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append(f"O utilizador {correio} não existe.")
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)   
    
    if db_user and senha != db_user.senha:  
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append(f"A senha inserida não corresponde com o utilizador {db_user.correio}.")
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)   
    
    if db_user and senha == db_user.senha:   
        access_token = create_access_token(data={"sub": db_user.correio, "role": str(db_user.role)})
        response = RedirectResponse(url="/core/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
        return response       
    else:       
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Erro nos dados. Consultar ao Administrador.")
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
       

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response
