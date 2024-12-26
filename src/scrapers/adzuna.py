import aiohttp
import logging
import asyncio
from typing import List, Optional
from datetime import datetime
from ..models.job import Job
from ..config import settings

logger = logging.getLogger(__name__)

class AdzunaScraper:
    """Scraper para a API do Adzuna"""
    
    def __init__(self):
        self.base_url = "https://api.adzuna.com/v1/api/jobs"
        self.app_id = settings.api.adzuna_app_id
        self.api_key = settings.api.adzuna_api_key
        self.timeout = settings.scraper.timeout
        self.retry_attempts = settings.scraper.retry_attempts
        self.batch_size = settings.scraper.batch_size
    
    async def search_jobs(
        self,
        keywords: str,
        location: str,
        remote_only: bool = False,
        page: int = 1,
        results_per_page: int = 50
    ) -> List[Job]:
        """
        Buscar vagas no Adzuna
        
        Args:
            keywords: Palavras-chave para busca
            location: Localização
            remote_only: Se deve buscar apenas vagas remotas
            page: Página de resultados
            results_per_page: Resultados por página
            
        Returns:
            Lista de vagas encontradas
        """
        try:
            logger.info(f"Buscando vagas no Adzuna: {keywords} em {location}")
            
            # Construir URL
            url = f"{self.base_url}/us/search/{page}"
            
            # Parâmetros da busca
            params = {
                "app_id": self.app_id,
                "app_key": self.api_key,
                "what": keywords,
                "where": location,
                "results_per_page": min(results_per_page, self.batch_size),
                "content-type": "application/json"
            }
            
            if remote_only:
                params["category"] = "it-jobs"  # Categoria com mais vagas remotas
                params["title_only"] = "remote"
            
            # Fazer requisição com timeout e retry
            for attempt in range(self.retry_attempts):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, timeout=self.timeout) as response:
                            if response.status != 200:
                                logger.error(
                                    f"Erro ao buscar no Adzuna: {response.status} - {await response.text()}"
                                )
                                continue
                            
                            data = await response.json()
                            
                            if not data or "results" not in data:
                                logger.warning("Nenhuma vaga encontrada no Adzuna")
                                return []
                            
                            # Processar resultados
                            jobs = []
                            for result in data["results"]:
                                try:
                                    job = Job(
                                        title=result.get("title", ""),
                                        company=result.get("company", {}).get("display_name", ""),
                                        location=result.get("location", {}).get("display_name", ""),
                                        description=result.get("description", ""),
                                        url=result.get("redirect_url", ""),
                                        source="Adzuna",
                                        remote=remote_only,
                                        salary=result.get("salary_min"),
                                        posted_date=result.get("created"),
                                        job_type=result.get("contract_time", ""),
                                        requirements=result.get("description", "")
                                    )
                                    jobs.append(job)
                                except Exception as e:
                                    logger.error(f"Erro ao processar vaga do Adzuna: {str(e)}")
                                    continue
                            
                            logger.info(f"[Adzuna] Encontradas {len(jobs)} vagas")
                            return jobs
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout na tentativa {attempt + 1} de {self.retry_attempts}")
                    if attempt == self.retry_attempts - 1:
                        raise
                    continue
                    
        except Exception as e:
            logger.error(f"Erro ao buscar no Adzuna: {str(e)}")
            return []
