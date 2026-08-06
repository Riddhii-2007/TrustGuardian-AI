from pydantic import BaseModel
from typing import Optional

class UserProfile(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    role: str = "user"

class TokenPayload(BaseModel):
    sub: str
    exp: int
    email: Optional[str] = None
