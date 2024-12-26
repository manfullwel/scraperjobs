import logging
from typing import List, Optional
import requests
from urllib.parse import urljoin

from ..models.job import Job
from ..config import settings

logger = logging.getLogger(__name__)

class AdzunaClient:
    """Cliente para a API do Adzuna Jobs"""
    
    BASE_URL = "http://api.adzuna.com/v1/api/jobs"
    
    def __init__(self, app_id: str, api_key: str):
        self.app_id = app_id
        self.api_key = api_key
        self.session = requests.Session()
    
    def search_jobs(
        self, 
        what: str, 
        where: str, 
        country: str = "us",
        results_per_page: int = 50,
        page: int = 1,
        sort_by: str = "date",
    ) -> List[Job]:
        """
        Buscar vagas usando a API do Adzuna.
        
        Args:
            what: Palavras-chave para busca (ex: "python developer")
            where: Localização (ex: "New York")
            country: Código do país (ex: "us", "gb", "br")
            results_per_page: Número de resultados por página
            page: Número da página
            sort_by: Ordenação ("date", "salary", "relevance")
        """
        try:
            # Construir URL
            url = f"{self.BASE_URL}/{country}/search/{page}"
            
            # Parâmetros da busca
            params = {
                "app_id": self.app_id,
                "app_key": self.api_key,
                "what": what,
                "where": where,
                "results_per_page": results_per_page,
                "sort_by": sort_by,
                "content-type": "application/json",
            }
            
            # Fazer request
            logger.info(f"Buscando vagas no Adzuna - keywords: {what}, location: {where}")
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Erro na API do Adzuna: Status {response.status_code}")
                return []
            
            # Parse do JSON
            data = response.json()
            
            # Extrair vagas
            jobs = []
            for result in data.get("results", []):
                try:
                    job = Job(
                        title=result.get("title", "N/A"),
                        company=result.get("company", {}).get("display_name", "N/A"),
                        location=result.get("location", {}).get("display_name", "N/A"),
                        description=result.get("description", "N/A"),
                        url=result.get("redirect_url"),
                        source="Adzuna",
                        salary=result.get("salary_min"),
                        posted_date=result.get("created"),
                        remote=any(
                            term in result.get("description", "").lower()
                            for term in ["remote", "home office", "work from home"]
                        )
                    )
                    jobs.append(job)
                except Exception as e:
                    logger.error(f"Erro ao processar vaga do Adzuna: {str(e)}")
                    continue
            
            logger.info(f"[OK] Adzuna: Encontradas {len(jobs)} vagas")
            return jobs
            
        except Exception as e:
            logger.error(f"Erro ao buscar vagas no Adzuna: {str(e)}")
            return []
