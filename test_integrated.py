import logging
import argparse
from src.services.job_service import JobService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_integrated_search(keywords: str, location: str, user_id: str = "test_user"):
    """Testar busca integrada de vagas"""
    
    # Credenciais Adzuna
    ADZUNA_APP_ID = "94530663"
    ADZUNA_API_KEY = "d440851cb8c728f93ebe9a7252f7643e"
    
    # Inicializar serviço
    service = JobService(ADZUNA_APP_ID, ADZUNA_API_KEY)
    
    # Verificar uso da API
    usage_info = service.get_api_usage_info(user_id)
    print("\nInformações de uso da API:")
    print(f"Adzuna - Chamadas restantes hoje: {usage_info['adzuna']['remaining_calls']}")
    print(f"Adzuna - Limite diário: {usage_info['adzuna']['daily_limit']}\n")
    
    # Buscar vagas
    print(f"Buscando vagas para '{keywords}' em '{location}'...")
    jobs = service.search_jobs(keywords, location, user_id)
    
    # Imprimir resultados
    print(f"\n[OK] Encontradas {len(jobs)} vagas no total:\n")
    
    # Agrupar por fonte
    jobs_by_source = {}
    for job in jobs:
        if job.source not in jobs_by_source:
            jobs_by_source[job.source] = []
        jobs_by_source[job.source].append(job)
    
    # Imprimir vagas por fonte
    for source, source_jobs in jobs_by_source.items():
        print(f"\n=== Vagas do {source} ({len(source_jobs)}) ===\n")
        
        for i, job in enumerate(source_jobs, 1):
            print(f"{i}. {job.title}")
            print(f"   Empresa: {job.company}")
            print(f"   Local: {job.location}")
            if job.salary:
                print(f"   Salário: ${job.salary:,.2f}" if isinstance(job.salary, (int, float))
                      else f"   Salário: {job.salary}")
            if job.posted_date:
                print(f"   Postada em: {job.posted_date}")
            print(f"   URL: {job.url}\n")
    
    # Atualizar informações de uso
    usage_info = service.get_api_usage_info(user_id)
    print("\nUso atualizado da API:")
    print(f"Adzuna - Chamadas restantes hoje: {usage_info['adzuna']['remaining_calls']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teste do serviço integrado de vagas")
    parser.add_argument("keywords", help="Palavras-chave para busca")
    parser.add_argument("location", help="Local da vaga")
    parser.add_argument("--user", help="ID do usuário", default="test_user")
    
    args = parser.parse_args()
    test_integrated_search(args.keywords, args.location, args.user)
