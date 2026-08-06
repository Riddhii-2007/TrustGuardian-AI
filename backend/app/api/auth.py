from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import verify_token, get_supabase_client
from app.models.auth import TokenPayload, UserProfile
from app.models.common import APIResponse

router = APIRouter()

@router.post("/verify", response_model=APIResponse[UserProfile])
async def verify_auth_token(token_payload: TokenPayload = Depends(verify_token)):
    # Since deps.py already verified the token via Supabase get_user,
    # we know the user is authenticated. 
    # In a real app, we would fetch the user's role/profile from our Postgres tables here.
    
    user_profile = UserProfile(
        id=token_payload.sub,
        email=token_payload.email or "",
        full_name="Supabase User", # This would be fetched from DB
        role="analyst"
    )
    return APIResponse(success=True, data=user_profile, message="Token verified")
