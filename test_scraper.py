import asyncio
import logging
import sys
from typing import List
from bs4 import BeautifulSoup

from src.config import settings
from src.models.job import Job
from src.services.job_scraper import JobScraper

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def test_scraper(keywords: str, location: str, version: str = "v1") -> List[Job]:
    try:
        logger.info(f"Iniciando teste com keywords='{keywords}', location='{location}', version='{version}'")
        
        # Validar versão
        if version not in settings.SCRAPER_CONFIGS:
            raise ValueError(f"Versão inválida: {version}. Opções: {list(settings.SCRAPER_CONFIGS.keys())}")
        
        # Inicializar scraper
        scraper = JobScraper()
        all_jobs = []
        sources = settings.SCRAPER_CONFIGS[version]["sources"]
        
        logger.info(f"Usando fontes: {sources}")
        
        # Testar cada fonte
        for source in sources:
            if source not in settings.SITE_CONFIGS:
                logger.warning(f"Fonte não configurada: {source}")
                continue
                
            try:
                logger.info(f"Testando fonte: {source}")
                site_config = settings.SITE_CONFIGS[source]
                
                # Fazer scraping
                jobs = scraper.scrape_site(source, site_config, keywords, location)
                
                # Validar e processar resultados
                if jobs:
                    logger.info(f"[OK] {source}: Encontradas {len(jobs)} vagas")
                    for job in jobs:
                        logger.info(f"  - {job.title} @ {job.company}")
                        if job.salary:
                            logger.info(f"    Salário: {job.salary}")
                        if job.remote:
                            logger.info(f"    Remoto: Sim")
                        if job.posted_date:
                            logger.info(f"    Publicado: {job.posted_date}")
                    all_jobs.extend(jobs)
                else:
                    logger.warning(f"[X] {source}: Nenhuma vaga encontrada")
                    
                    # Analisar página para debug
                    if hasattr(scraper, 'last_page_source'):
                        soup = BeautifulSoup(scraper.last_page_source, 'lxml')
                        logger.debug(f"HTML da página: {soup.prettify()[:500]}...")
                        
                        # Tentar encontrar elementos
                        for selector_name, selector in site_config['selectors'].items():
                            elements = soup.select(selector)
                            logger.debug(f"Seletor '{selector_name}' ({selector}): {len(elements)} elementos encontrados")
                
            except Exception as e:
                logger.error(f"Erro ao processar {source}: {str(e)}", exc_info=True)
                continue
        
        return all_jobs
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {str(e)}")
        return []

def print_results(jobs: List[Job]):
    """Imprimir resultados formatados"""
    if not jobs:
        print("\n[X] Nenhuma vaga encontrada")
        return
        
    print(f"\n[OK] Encontradas {len(jobs)} vagas no total:\n")
    
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job.title}")
        print(f"   Empresa: {job.company}")
        print(f"   Local: {job.location}")
        if job.salary:
            print(f"   Salário: {job.salary}")
        if job.remote:
            print(f"   Remoto: Sim")
        if job.posted_date:
            print(f"   Publicado em: {job.posted_date}")
        print(f"   URL: {job.url}\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Testar Job Scraper')
    parser.add_argument('keywords', help='Palavras-chave para busca')
    parser.add_argument('location', help='Localização')
    parser.add_argument('--version', '-v', default='v1', help='Versão do scraper (v1, v2, v3)')
    
    args = parser.parse_args()
    
    # Executar teste
    jobs = asyncio.run(test_scraper(args.keywords, args.location, args.version))
    
    # Imprimir resultados
    print_results(jobs)
