import uvicorn
import argparse
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.api.jobs import router as jobs_router
from src.config import settings

# Configurar diretórios
STATIC_DIR = Path(__file__).parent / "src" / "static"
TEMPLATES_DIR = Path(__file__).parent / "src" / "templates"

# Criar diretórios se não existirem
STATIC_DIR.mkdir(exist_ok=True, parents=True)
TEMPLATES_DIR.mkdir(exist_ok=True, parents=True)

# Criar app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION
)

# Montar arquivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

# Configurar templates e arquivos estáticos
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
            "title": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    )

@app.get("/docs")
async def docs_redirect():
    """Redirecionar para documentação Swagger"""
    return RedirectResponse(url="/docs")

@app.get("/index.html")
async def redirect_index():
    """Redirecionar index.html para raiz"""
    return RedirectResponse("/")

@app.exception_handler(404)
async def not_found(request: Request, exc):
    """Tratar páginas não encontradas"""
    if request.url.path == "/favicon.ico":
        return RedirectResponse(url="https://fastapi.tiangolo.com/img/favicon.png")
    return RedirectResponse(url="/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor da API de vagas")
    parser.add_argument("--host", default=settings.HOST, help="Host")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Porta")
    parser.add_argument("--reload", action="store_true", help="Reload automático")
    
    args = parser.parse_args()
    
    # Iniciar servidor
    uvicorn.run(
        "test_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
