from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.usuario import get_user_by_email
from app.models.relatorio import Usuario
from app.core.deps import get_db
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception  

    try:
        payload = jwt.decode(token.split(" ")[1], settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_email: str = payload.get("sub") 
        
        if user_email is None:
            raise credentials_exception  

        user = await get_user_by_email(db, correio=user_email)
        if user is None:
            raise credentials_exception  #

    except JWTError:
        raise credentials_exception  

    return user  
