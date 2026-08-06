import os
from supabase import create_client, Client
from app.config import settings

supabase_client: Client = None

def init_supabase() -> None:
    global supabase_client
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_SERVICE_KEY
    supabase_client = create_client(url, key)

def get_supabase() -> Client:
    return supabase_client
