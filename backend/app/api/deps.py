from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from app.db.supabase import get_supabase
from app.db.neo4j import get_neo4j_driver
from app.models.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_supabase_client():
    return get_supabase()

async def get_neo4j():
    return get_neo4j_driver()

async def verify_token(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    from app.config import settings
    if settings.APP_ENV == "development" and settings.DEV_AUTH_BYPASS_TOKEN and token == settings.DEV_AUTH_BYPASS_TOKEN:
        import logging
        logging.warning("\033[91m⚠️ [SECURITY WARNING] DEV BYPASS AUTHENTICATION ACTIVE — Mock analyst access granted! ⚠️\033[0m")
        return TokenPayload(
            sub="mock-user-id",
            exp=0,
            email="analyst@trustguardian-ai.com"
        )

    try:
        supabase = get_supabase()
        # Verify the token by calling Supabase get_user
        # The service role client can validate tokens this way
        auth_res = supabase.auth.get_user(token)
        
        if not auth_res or not auth_res.user:
            raise ValueError("Invalid token")
            
        user = auth_res.user
        
        return TokenPayload(
            sub=user.id,
            exp=0, # Supabase client handles expiry check
            email=user.email or ""
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_google_token(x_google_provider_token: Optional[str] = Header(None)) -> Optional[str]:
    return x_google_provider_token
