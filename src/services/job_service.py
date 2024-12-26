import logging
import time
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.job import Job
from .job_scraper import JobScraper
from .adzuna_client import AdzunaClient
from .api_manager import APIUsageManager

logger = logging.getLogger(__name__)

class JobService:
    """Serviço integrado de busca de vagas"""
    
    def __init__(self, adzuna_app_id: str, adzuna_api_key: str):
        self.job_scraper = JobScraper()
        self.adzuna_client = AdzunaClient(adzuna_app_id, adzuna_api_key)
        self.api_manager = APIUsageManager()
        
        # Configurações
        self.ADZUNA_DAILY_LIMIT = 100  # Ajuste conforme seu plano
        self.MAX_WORKERS = 2  # Número de threads para busca paralela
    
    def search_jobs(
        self,
        keywords: str,
        location: str,
        user_id: str,
        prefer_adzuna: bool = True
    ) -> List[Job]:
        """
        Buscar vagas em todas as fontes disponíveis.
        
        Args:
            keywords: Palavras-chave para busca
            location: Local desejado
            user_id: ID do usuário para controle de uso da API
            prefer_adzuna: Se True, tenta Adzuna primeiro se disponível
        """
        jobs = []
        errors = []
        
        # Verificar disponibilidade do Adzuna
        can_use_adzuna = self.api_manager.can_use_api(
            "adzuna", user_id, self.ADZUNA_DAILY_LIMIT
        )
        
        # Definir ordem das fontes
        sources = []
        if prefer_adzuna and can_use_adzuna:
            sources = ["adzuna", "linkedin"]
        else:
            sources = ["linkedin", "adzuna"]
        
        # Buscar em paralelo
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            future_to_source = {
                executor.submit(
                    self._search_source,
                    source,
                    keywords,
                    location,
                    user_id
                ): source
                for source in sources
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    source_jobs = future.result()
                    if source_jobs:
                        jobs.extend(source_jobs)
                except Exception as e:
                    errors.append(f"Erro em {source}: {str(e)}")
                    logger.error(f"Erro ao buscar em {source}: {str(e)}")
        
        # Log de resultados
        for source in sources:
            source_jobs = [j for j in jobs if j.source.lower() == source]
            logger.info(f"[{source.upper()}] Encontradas {len(source_jobs)} vagas")
        
        if errors:
            logger.warning("Erros durante a busca:")
            for error in errors:
                logger.warning(f"  - {error}")
        
        return jobs
    
    def _search_source(
        self,
        source: str,
        keywords: str,
        location: str,
        user_id: str
    ) -> List[Job]:
        """Buscar vagas em uma fonte específica"""
        try:
            if source == "adzuna":
                # Verificar limite diário
                if not self.api_manager.can_use_api(
                    "adzuna", user_id, self.ADZUNA_DAILY_LIMIT
                ):
                    logger.warning("Limite diário do Adzuna atingido")
                    return []
                
                # Buscar no Adzuna
                jobs = self.adzuna_client.search_jobs(
                    what=keywords,
                    where=location,
                    country="us"
                )
                
                # Registrar uso
                if jobs:
                    self.api_manager.record_api_use("adzuna", user_id)
                
                return jobs
                
            elif source == "linkedin":
                # Buscar no LinkedIn
                return self.job_scraper.scrape_site(
                    "LinkedIn",
                    settings.SITE_CONFIGS["LinkedIn"],
                    keywords,
                    location
                )
            
            else:
                logger.error(f"Fonte desconhecida: {source}")
                return []
                
        except Exception as e:
            logger.error(f"Erro ao buscar em {source}: {str(e)}")
            return []
    
    def get_api_usage_info(self, user_id: str) -> dict:
        """Obter informações de uso da API"""
        return {
            "adzuna": {
                "remaining_calls": self.api_manager.get_remaining_calls(
                    "adzuna", user_id, self.ADZUNA_DAILY_LIMIT
                ),
                "daily_limit": self.ADZUNA_DAILY_LIMIT
            }
        }
