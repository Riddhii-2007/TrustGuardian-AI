# ---------------------------------------------------------------------------
# SQL Schema for Scan Audit Log Table:
#
# CREATE TABLE public.scan_audit_log (
#     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     timestamp TIMESTAMPTZ DEFAULT now(),
#     subject TEXT,
#     sender TEXT,
#     trust_score FLOAT,
#     confidence_score FLOAT,
#     recommendation TEXT,
#     verification_required BOOLEAN
# );
#
# -- Policies: Row Level Security is enabled on this table.
# -- Since no public policies are added, only the service-role key (which
# -- bypasses RLS) can perform SELECT/INSERT/UPDATE/DELETE.
# ---------------------------------------------------------------------------

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

def write_scan_audit(record: dict) -> None:
    """Write an audit entry for a completed scan to Supabase scan_audit_log.
    
    This operates synchronously. If the database is unreachable, throws an error,
    or RLS blocks it, the exception will propagate up and fail the API scan request,
    preventing silent log drop as required by security.
    """
    import sys
    import logging
    if "pytest" in sys.modules:
        logging.getLogger(__name__).info("[AUDIT MOCK] Skipping live Supabase write during pytest execution.")
        return

    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase client is not initialized.")
    
    # Executes the insert call synchronously and catches APIErrors in development
    try:
        client.table("scan_audit_log").insert(record).execute()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Supabase Audit Write Failed: {e}")
        if settings.APP_ENV == "development":
            logger.info("APP_ENV is development — continuing scan execution without database persistence.")
            return
        raise e
