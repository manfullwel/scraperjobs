import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp
import asyncio

from ..models.job import Job, JobSearch
from ..scrapers.adzuna import AdzunaScraper
from ..config import settings

logger = logging.getLogger(__name__)

class AsyncJobService:
    """Serviço assíncrono para busca de vagas"""
    
    def __init__(self):
        """Inicializar scrapers e cache"""
        self.adzuna_scraper = AdzunaScraper()
        self.api_usage_file = settings.api.api_usage_file
        self.cache_enabled = settings.cache.enabled
        self.cache_ttl = settings.cache.ttl
        self.max_cache_size = settings.cache.max_size
        self.api_daily_limit = settings.api.daily_limit
        
        # Cache em memória
        self._cache = {}
        self._api_usage = self._load_api_usage()
    
    def _load_api_usage(self) -> Dict:
        """Carregar informações de uso da API"""
        try:
            with open(self.api_usage_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            logger.error(f"Erro ao carregar uso da API: {str(e)}")
            return {}
    
    def _save_api_usage(self):
        """Salvar informações de uso da API"""
        try:
            with open(self.api_usage_file, "w") as f:
                json.dump(self._api_usage, f)
        except Exception as e:
            logger.error(f"Erro ao salvar uso da API: {str(e)}")
    
    def _update_api_usage(self, user_id: str):
        """Atualizar contagem de uso da API"""
        today = datetime.now().strftime("%Y-%m-%d")
        if user_id not in self._api_usage:
            self._api_usage[user_id] = {}
        if today not in self._api_usage[user_id]:
            self._api_usage[user_id][today] = 0
        self._api_usage[user_id][today] += 1
        self._save_api_usage()
    
    def get_api_usage_info(self, user_id: str) -> Dict:
        """Obter informações de uso da API"""
        if user_id not in self._api_usage:
            return {"total": 0, "today": 0, "limit": self.api_daily_limit}
        
        today = datetime.now().strftime("%Y-%m-%d")
        total = sum(count for day, count in self._api_usage[user_id].items())
        today_count = self._api_usage[user_id].get(today, 0)
        
        return {
            "total": total,
            "today": today_count,
            "limit": self.api_daily_limit
        }
    
    def _get_cache_key(self, search: JobSearch) -> str:
        """Gerar chave de cache para uma busca"""
        return f"{search.keywords}:{search.location}:{search.remote_only}"
    
    def _get_from_cache(self, key: str) -> Optional[List[Job]]:
        """Buscar resultados no cache"""
        if not self.cache_enabled:
            return None
            
        if key in self._cache:
            data = self._cache[key]
            age = (datetime.now() - data["timestamp"]).seconds
            if age < self.cache_ttl:
                logger.info(f"Cache hit para {key}")
                return data["jobs"]
            else:
                del self._cache[key]
        return None
    
    def _save_to_cache(self, key: str, jobs: List[Job]):
        """Salvar resultados no cache"""
        if not self.cache_enabled:
            return
            
        # Limpar cache se necessário
        if len(self._cache) >= self.max_cache_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]
        
        self._cache[key] = {
            "jobs": jobs,
            "timestamp": datetime.now()
        }
        logger.info(f"Resultados salvos no cache para {key}")
    
    async def search_jobs(
        self,
        search: JobSearch,
        user_id: str,
        use_cache: bool = True
    ) -> List[Job]:
        """
        Buscar vagas em todas as fontes configuradas
        
        Args:
            search: Parâmetros da busca
            user_id: ID do usuário
            use_cache: Se deve usar cache
            
        Returns:
            Lista de vagas encontradas
        """
        # Verificar limite diário
        usage = self.get_api_usage_info(user_id)
        if usage["today"] >= self.api_daily_limit:
            logger.warning(f"Limite diário excedido para usuário {user_id}")
            return []
        
        # Verificar cache
        cache_key = self._get_cache_key(search)
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        try:
            # Buscar em todas as fontes
            all_jobs = []
            tasks = []
            
            if "adzuna" in search.sources:
                tasks.append(
                    self.adzuna_scraper.search_jobs(
                        search.keywords,
                        search.location,
                        search.remote_only
                    )
                )
            
            # Executar buscas em paralelo
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processar resultados
            for jobs in results:
                if isinstance(jobs, list):
                    all_jobs.extend(jobs)
                else:
                    logger.error(f"Erro em uma das fontes: {str(jobs)}")
            
            # Atualizar uso da API
            self._update_api_usage(user_id)
            
            # Salvar no cache
            if use_cache:
                self._save_to_cache(cache_key, all_jobs)
            
            return all_jobs
            
        except Exception as e:
            logger.error(f"Erro ao buscar vagas: {str(e)}")
            return []
