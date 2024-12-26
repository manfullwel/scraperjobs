import logging
import argparse
from src.services.adzuna_client import AdzunaClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_adzuna(keywords: str, location: str):
    """Testar busca de vagas usando API do Adzuna"""
    
    # Credenciais da API
    APP_ID = "94530663"
    API_KEY = "d440851cb8c728f93ebe9a7252f7643e"
    
    # Inicializar cliente
    client = AdzunaClient(APP_ID, API_KEY)
    
    # Buscar vagas
    jobs = client.search_jobs(
        what=keywords,
        where=location,
        country="us",  # Buscar nos EUA
        results_per_page=10
    )
    
    # Imprimir resultados
    print(f"\n[OK] Encontradas {len(jobs)} vagas no total:\n")
    
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job.title}")
        print(f"   Empresa: {job.company}")
        print(f"   Local: {job.location}")
        if job.salary:
            print(f"   Salário: ${job.salary:,.2f}")
        if job.posted_date:
            print(f"   Postada em: {job.posted_date}")
        print(f"   URL: {job.url}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teste da API do Adzuna")
    parser.add_argument("keywords", help="Palavras-chave para busca")
    parser.add_argument("location", help="Local da vaga")
    
    args = parser.parse_args()
    test_adzuna(args.keywords, args.location)
