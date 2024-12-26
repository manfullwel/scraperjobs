import logging
import time
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from ..models.job import Job
from ..config import settings

logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.user_agent = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        })
        self.last_page_source = None
    
    def _add_linkedin_params(self, url: str) -> str:
        """Adicionar parâmetros específicos do LinkedIn"""
        params = {
            'geoId': settings.SITE_CONFIGS['LinkedIn']['geo_ids'].get('Estados Unidos', '103644278'),
            'position': '1',
            'pageNum': '0',
            'f_WT': '2',  # Remote
            'f_TPR': 'r2592000'  # Last 30 days
        }
        
        # Adicionar parâmetros à URL
        for key, value in params.items():
            if '?' in url:
                url += f'&{key}={value}'
            else:
                url += f'?{key}={value}'
        
        return url
    
    def _extract_job_data(self, card: BeautifulSoup, selectors: Dict[str, str], source: str, base_url: str) -> Job:
        """Extrair dados de um card de emprego com tratamento robusto de erros"""
        try:
            # Extrair dados básicos
            title_elem = card.select_one(selectors['title'])
            company_elem = card.select_one(selectors['company'])
            location_elem = card.select_one(selectors['location'])
            description_elem = card.select_one(selectors['description'])
            job_link_elem = card.select_one(selectors['job_link'])
            salary_elem = card.select_one(selectors['salary'])
            posted_time_elem = card.select_one(selectors['posted_time'])
            remote_badge_elem = card.select_one(selectors['remote_badge'])
            
            # Extrair texto com tratamento de erros
            title = title_elem.get_text(strip=True) if title_elem else 'N/A'
            company = company_elem.get_text(strip=True) if company_elem else 'N/A'
            location = location_elem.get_text(strip=True) if location_elem else 'N/A'
            description = description_elem.get_text(strip=True) if description_elem else 'N/A'
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            posted_time = posted_time_elem.get_text(strip=True) if posted_time_elem else None
            remote_badge = remote_badge_elem.get_text(strip=True) if remote_badge_elem else None
            
            # Construir URL completa
            job_url = None
            if job_link_elem and job_link_elem.get('href'):
                job_url = urljoin(base_url, job_link_elem['href'])
            
            # Criar objeto Job
            job = Job(
                title=title,
                company=company,
                location=location,
                description=description,
                url=job_url,
                source=source,
                salary=salary,
                posted_time=posted_time,
                remote=bool(remote_badge)
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados do card: {str(e)}")
            return None
    
    def _extract_jobs_from_html(self, html: str, site_name: str, site_config: dict) -> List[Job]:
        """Extrair vagas do HTML usando BeautifulSoup"""
        try:
            # Parse HTML
            soup = BeautifulSoup(html, 'lxml')
            
            # Encontrar cards
            cards = soup.select(site_config['selectors']['job_cards'])
            if not cards:
                logger.warning(f"[X] {site_name}: Nenhuma vaga encontrada")
                return []
            
            # Extrair dados de cada card
            jobs = []
            for card in cards:
                job = self._extract_job_data(
                    card, 
                    site_config['selectors'],
                    site_name,
                    site_config['base_url']
                )
                if job:
                    jobs.append(job)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Erro ao extrair vagas do HTML: {str(e)}")
            return []
    
    def scrape_site(self, site_name: str, site_config: dict, keywords: str, location: str) -> List[Job]:
        """Fazer scraping de um site específico"""
        logger.info(f"Iniciando scraping de {site_name} - keywords: {keywords}, location: {location}")
        
        try:
            # Construir URL base
            url = site_config['base_url'].format(
                quote_plus(keywords),
                quote_plus(location)
            )
            
            # Adicionar parâmetros extras
            if site_name == 'LinkedIn':
                url = self._add_linkedin_params(url)
            
            # Acessar URL com requests
            logger.info(f"Acessando URL: {url}")
            response = self.session.get(url)
            
            # Verificar status
            if response.status_code != 200:
                logger.error(f"Erro ao acessar {site_name}: Status {response.status_code}")
                return []
            
            # Extrair vagas do HTML
            jobs = self._extract_jobs_from_html(response.text, site_name, site_config)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Erro ao processar {site_name}: {str(e)}")
            return []
