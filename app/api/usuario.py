from fastapi import APIRouter, Depends, File, Form, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.services.usuario import get_user, get_users, create_user, update_user, delete_user
from app.core.deps import get_db
from app.core.dependencies import get_current_user
from app.models.relatorio import Usuario


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")  

@router.get("/all", response_model=list[UsuarioResponse])
async def read_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role in ["Administrador"]:  
        users = await get_users(db)            
        if users is None:
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append(f"Crear Usuarios.")        
            return RedirectResponse(url="/users/create", status_code=status.HTTP_303_SEE_OTHER)
        else:
            return templates.TemplateResponse(
                "/user/user_list.html", 
                {
                    "request": request,
                    "users": users,
                    "current_user": current_user,
                }
            )
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append(f"Acesso limitado nesta página.")        
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/details/{user_id}", response_model=UsuarioResponse)
async def user_details(
    request: Request,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):    
    if current_user.role in ["Administrador", "Funcionario"]:          
        user = await get_user(db, user_id)
        if user is None:  
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append(f"Usuario não encontrado.")        
            return RedirectResponse(url="/users/all", status_code=status.HTTP_303_SEE_OTHER)       
        else:
            return user
    else:
        return JSONResponse(content={"status": "admin"})


@router.get("/create")
async def create_user_form(request: Request, current_user: Usuario = Depends(get_current_user)):
    if current_user.role in ["Administrador"]:  
        return templates.TemplateResponse("/user/create_user.html", {"request": request, "current_user":current_user})
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Acesso limitado nesta página.")        
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/create", response_model=UsuarioResponse)
async def criar_user(
    request: Request,
    nome_completo: str = Form(...), 
    correio: str = Form(...), 
    telefone: str = Form(None),  
    role: str = Form(...),
    especialidade: str = Form(None), 
    senha: str = Form(...),
    confirm_senha: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role not in ["Administrador"]:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    if senha != confirm_senha:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("As senhas não coincidem.")
        return RedirectResponse(url="/users/create", status_code=status.HTTP_303_SEE_OTHER)

    user_data = UsuarioCreate(
        nome_completo=nome_completo,
        correio=correio,
        telefone=telefone, 
        role=role,
        especialidade=especialidade, 
        senha=senha,
        deleted=False  
    )

    created_user = await create_user(db, user_data)

    if created_user:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Usuário criado com sucesso.")
        return RedirectResponse(url="/users/all", status_code=status.HTTP_303_SEE_OTHER)
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Erro ao criar o usuário.")
        return RedirectResponse(url="/users/all", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/edit/{user_id}")
async def edit_user(
    request: Request,
    user_id: str,      
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
    ):
    
    if current_user.role in ["Administrador"]:  
        user = await get_user(db, user_id)      
        if user is None:
            if "notifications" not in request.session:
                request.session["notifications"] = []
            request.session["notifications"].append("Usuario não encontrado.")        
            return RedirectResponse(url="/users/all", status_code=status.HTTP_303_SEE_OTHER) 
                 
        if user:
            return templates.TemplateResponse("/user/edit_user.html", {"request": request, "user": user, "current_user":current_user})
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append(f"Acesso limitado nesta página.")        
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER) 
    

@router.post("/edit/{user_id}")
async def editar_user(
    request: Request,
    user_id: str, 
    nome_completo: str = Form(...),  
    correio: str = Form(...),  
    telefone: str = Form(...),  
    role: str = Form(...),  
    especialidade: str = Form(None),  
    senha: str = Form(None),  
    confirm_senha: str = Form(None),  
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.role not in ["Administrador"]:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Acesso limitado nesta página.")
        return RedirectResponse(url="/core/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    if senha and senha != confirm_senha:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("As senhas não coincidem.")
        return RedirectResponse(url=f"/users/edit/{user_id}", status_code=status.HTTP_303_SEE_OTHER)

    user_data = UsuarioUpdate(
        nome_completo=nome_completo,
        correio=correio,
        telefone=telefone,
        role=role,
        especialidade=especialidade,
        senha=senha,  
    )

    user_updt = await update_user(db, user_id, user_data)
    if user_updt:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Usuário atualizado com sucesso.")
        return RedirectResponse(url="/users/all", status_code=status.HTTP_303_SEE_OTHER)
    else:
        if "notifications" not in request.session:
            request.session["notifications"] = []
        request.session["notifications"].append("Erro ao atualizar o usuário.")
        return RedirectResponse(url="/users/all", status_code=status.HTTP_303_SEE_OTHER)


@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_user(
    user_id: str, 
    db: AsyncSession = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
    ):           
    
    if current_user.role in ["Administrador"]:
        user_deleted = await delete_user(db, user_id)       
        if user_deleted:
            return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content={"status": "error"}, status_code=status.HTTP_404_NOT_FOUND)  
    else:
        return JSONResponse(content={"status": "admin"})  



@router.post("/clear-notifications")
async def clear_notifications(request: Request):
    request.session.pop("notifications", None)
    return {"status": "cleared"}