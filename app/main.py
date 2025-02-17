from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.core.database import async_session
from app.api.auth import router as auth_router
from app.api.usuario import router as user_router
from app.api.core import router as dashboard_router
from app.api.paciente import router as paciente_router
from app.api.consulta import router as consulta_router
from app.api.relatorio import router as relatorio_router


from app.services.usuario import get_user_by_email, create_user, get_user_by_email
from app.schemas.usuario import UsuarioCreate
from app.core.config import settings

class AuthRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            if response.status_code == status.HTTP_401_UNAUTHORIZED:
                return RedirectResponse(url="/auth/login")  
            return response
        except HTTPException as ex:
            if ex.status_code == status.HTTP_401_UNAUTHORIZED:
                return RedirectResponse(url="/auth/login")  
            raise ex

class NotificationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if 'notification' in request.session:
            del request.session['notification']
        return response

def get_app() -> FastAPI:
    _app = FastAPI(
        title="Sistema de Gestão de Administração",
        docs_url='/documentacao',
        redoc_url=None,
    )
    
    @_app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/auth/login")
    
    _app.include_router(dashboard_router, prefix="/core", tags=["Dashboard"])
    _app.include_router(auth_router, prefix="/auth", tags=["Autenticação"])
    _app.include_router(user_router, prefix="/users", tags=["Usuários"])
    _app.include_router(paciente_router, prefix="/pacientes", tags=["Pacientes"])  
    _app.include_router(consulta_router, prefix="/consultas", tags=["Consultas"]) 
    _app.include_router(relatorio_router, prefix="/relatorios", tags=["Relatorios"])
    
    
    
    

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    _app.add_middleware(AuthRedirectMiddleware)
    
    _app.add_middleware(SessionMiddleware, secret_key=settings.DB_SECRET_KEY)

    _app.mount("/static", StaticFiles(directory="app/static"), name="static")

    return _app

app = get_app()


@app.on_event("startup")
async def on_startup():
    async with async_session() as db:
        admin_email = "admin@bot.com"
        if not await get_user_by_email(db, admin_email):
            admin_user = UsuarioCreate(
                nome_completo="administrador",
                correio=admin_email,
                senha="admin",
                role="Administrador"
            )
            await create_user(db, admin_user)  
             
    
            
@app.on_event("shutdown")
async def shutdown():
    await async_session.close_all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
