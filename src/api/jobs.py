from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from ..models.job import Job, JobSearch
from ..services.job_service_async import AsyncJobService
from ..config import settings

# Configurar logging
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter()

# Instanciar serviço
job_service = AsyncJobService()

@router.post("/search")
async def search_jobs(
    keywords: str = Query(..., description="Palavras-chave para busca"),
    location: str = Query(..., description="Localização"),
    remote_only: bool = Query(False, description="Apenas vagas remotas"),
    user_id: str = Query("test_user", description="ID do usuário"),
    sources: List[str] = Query(None, description="Fontes de dados para busca")
) -> dict:
    """
    Buscar vagas com os parâmetros especificados
    """
    try:
        # Usar fontes padrão se não especificadas
        if not sources:
            sources = settings.default_sources
            
        # Criar objeto de busca
        search = JobSearch(
            keywords=keywords,
            location=location,
            remote_only=remote_only,
            sources=sources
        )
        
        # Buscar vagas
        logger.info(f"Iniciando busca: {keywords} em {location}")
        jobs = await job_service.search_jobs(search, user_id)
        logger.info(f"Busca finalizada. Encontradas {len(jobs)} vagas")
        
        return {
            "total": len(jobs),
            "jobs": jobs
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar vagas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar vagas: {str(e)}"
        )

@router.get("/usage")
async def get_api_usage(user_id: str = Query("test_user")) -> dict:
    """
    Obter informações de uso da API
    """
    try:
        usage = job_service.get_api_usage_info(user_id)
        return {
            "today_requests": usage["today"],
            "month_requests": usage["total"],
            "daily_limit": usage["limit"]
        }
    except Exception as e:
        logger.error(f"Erro ao obter uso da API: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter uso da API: {str(e)}"
        )
