from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path
import logging

from src.api.jobs import router as jobs_router
from src.config import settings

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.server.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Diretórios
STATIC_DIR = Path("src/static")
TEMPLATES_DIR = Path("src/templates")

# Criar diretórios se não existirem
STATIC_DIR.mkdir(exist_ok=True, parents=True)
TEMPLATES_DIR.mkdir(exist_ok=True, parents=True)

# Criar app
app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description=settings.app.description,
    debug=settings.server.debug
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Configurar templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Adicionar rotas
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Renderizar página principal"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": settings.app.name,
            "version": settings.app.version
        }
    )

@app.get("/index.html")
async def redirect_index():
    """Redirecionar index.html para raiz"""
    return RedirectResponse("/")

@app.exception_handler(404)
async def not_found(request: Request, exc):
    """Tratar páginas não encontradas"""
    return RedirectResponse("/")

if __name__ == "__main__":
    logger.info(f"Starting {settings.app.name} v{settings.app.version}")
    logger.info(f"Server running on http://{settings.server.host}:{settings.server.port}")
    
    # Iniciar servidor
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug
    )
