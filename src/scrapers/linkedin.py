import aiohttp
import logging
from typing import List, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from ..models.job import Job
from ..config import settings

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """Scraper para vagas do LinkedIn"""
    
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    async def search_jobs(
        self,
        keywords: str,
        location: str,
        remote_only: bool = False,
        page: int = 1,
        results_per_page: int = 25
    ) -> List[Job]:
        """
        Buscar vagas no LinkedIn
        
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
            # Construir URL
            params = {
                "keywords": keywords,
                "location": location,
                "start": (page - 1) * results_per_page,
                "pageSize": results_per_page,
                "f_WT": "2" if remote_only else "",  # Filtro de trabalho remoto
                "sortBy": "R"  # Ordenar por relevância
            }
            
            # Fazer requisição
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        logger.error(
                            f"Erro ao buscar no LinkedIn: {response.status}"
                        )
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Encontrar cards de vagas
                    job_cards = soup.find_all(
                        "div",
                        class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card"
                    )
                    
                    if not job_cards:
                        logger.warning("Nenhuma vaga encontrada no LinkedIn")
                        return []
                    
                    # Processar resultados
                    jobs = []
                    for card in job_cards:
                        try:
                            # Extrair dados básicos
                            title = card.find(
                                "h3",
                                class_="base-search-card__title"
                            )
                            company = card.find(
                                "h4",
                                class_="base-search-card__subtitle"
                            )
                            location = card.find(
                                "span",
                                class_="job-search-card__location"
                            )
                            link = card.find("a")
                            
                            if not all([title, company, location, link]):
                                continue
                            
                            # Criar objeto Job
                            job = Job(
                                title=title.text.strip(),
                                company=company.text.strip(),
                                location=location.text.strip(),
                                url=link["href"],
                                source="LinkedIn",
                                remote=remote_only,
                                posted_date=self._extract_date(card),
                                description=self._extract_description(card)
                            )
                            jobs.append(job)
                            
                        except Exception as e:
                            logger.error(
                                f"Erro ao processar vaga do LinkedIn: {str(e)}"
                            )
                            continue
                    
                    logger.info(f"[LinkedIn] Encontradas {len(jobs)} vagas")
                    return jobs
                    
        except Exception as e:
            logger.error(f"Erro ao buscar no LinkedIn: {str(e)}")
            return []
    
    def _extract_date(self, card) -> Optional[str]:
        """Extrair data de postagem"""
        try:
            date_elem = card.find(
                "time",
                class_="job-search-card__listdate"
            )
            if date_elem and date_elem.get("datetime"):
                return date_elem["datetime"]
        except:
            pass
        return None
    
    def _extract_description(self, card) -> str:
        """Extrair descrição da vaga"""
        try:
            desc = card.find(
                "div",
                class_="base-search-card__metadata"
            )
            if desc:
                return desc.text.strip()
        except:
            pass
        return ""
