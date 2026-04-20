# backend/api/main.py

import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from backend.api.routers import health, models, threads
from backend.api.services.vllm_async import close_client
from backend.api.services.direct_runtime import unload_model as unload_direct_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    await close_client()
    await unload_direct_model()

app = FastAPI(
    title="VLM Gateway",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# CORS (geliştirme için geniş; prod'da host'u daralt)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip (1KB üstü yanıtları sıkıştırır; görünür davranış değişmez)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Basit global error handler (stacktrace yerine temiz JSON; davranışı bozmaz)
@app.exception_handler(Exception)
async def all_errors(request: Request, exc: Exception):
    # burada logging ekleyebilirsin (ör. print veya proper logger)
    return ORJSONResponse({"error": str(exc)}, status_code=500)

# Routerlar
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(threads.router, prefix="/threads", tags=["threads"])
