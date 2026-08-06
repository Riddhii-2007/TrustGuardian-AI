from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.db.supabase import init_supabase
from app.db.neo4j import init_neo4j, close_neo4j
from app.api import auth, dashboard, requests, graph, sandbox, replay

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_supabase()
    init_neo4j()
    yield
    # Shutdown
    close_neo4j()

app = FastAPI(
    title="TrustGuardian AI",
    description="Enterprise Trust Intelligence Platform Backend",
    version="1.0.0",
    lifespan=lifespan
)

origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(requests.router, prefix="/api/requests", tags=["requests"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(sandbox.router, prefix="/api/sandbox", tags=["sandbox"])
app.include_router(replay.router, prefix="/api/replay", tags=["replay"])

@app.get("/api/health", tags=["health"])
async def health_check():
    return {"status": "ok", "environment": settings.APP_ENV}
