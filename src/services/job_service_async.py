import asyncio
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
from ..models.job import Job, JobSearch
from ..scrapers.adzuna import AdzunaScraper
from ..config import settings, is_termux
import os

logger = logging.getLogger(__name__)

class AsyncJobService:
    def __init__(self):
        """Inicializa o serviço de busca de empregos"""
        app_id, api_key, daily_limit = settings.api.get_credentials()
        self.scraper = AdzunaScraper(app_id, api_key)
        self.daily_limit = daily_limit
        self.usage_file = settings.api.api_usage_file
        self.load_usage()

    def load_usage(self):
        """Carrega informações de uso da API"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    self.usage = json.load(f)
            else:
                self.usage = {}
        except Exception as e:
            logger.error(f"Erro ao carregar uso da API: {e}")
            self.usage = {}

    def save_usage(self):
        """Salva informações de uso da API"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage, f)
        except Exception as e:
            logger.error(f"Erro ao salvar uso da API: {e}")

    def get_user_usage(self, user_id: str) -> Dict:
        """Obtém informações de uso para um usuário"""
        today = date.today().isoformat()
        if user_id not in self.usage:
            self.usage[user_id] = {"total": 0, "daily": {}}
        if today not in self.usage[user_id]["daily"]:
            self.usage[user_id]["daily"] = {today: 0}
        return {
            "today": self.usage[user_id]["daily"][today],
            "total": self.usage[user_id]["total"],
            "limit": self.daily_limit,
            "remaining": self.daily_limit - self.usage[user_id]["daily"][today]
        }

    def update_usage(self, user_id: str):
        """Atualiza contagem de uso para um usuário"""
        today = date.today().isoformat()
        if user_id not in self.usage:
            self.usage[user_id] = {"total": 0, "daily": {}}
        if today not in self.usage[user_id]["daily"]:
            self.usage[user_id]["daily"] = {today: 0}
        
        self.usage[user_id]["daily"][today] += 1
        self.usage[user_id]["total"] += 1
        self.save_usage()

    def can_make_request(self, user_id: str) -> bool:
        """Verifica se o usuário pode fazer mais requisições"""
        usage = self.get_user_usage(user_id)
        return usage["remaining"] > 0

    async def search_jobs(self, search: JobSearch, user_id: str) -> List[Job]:
        """
        Busca vagas de emprego usando os parâmetros fornecidos
        """
        if not self.can_make_request(user_id):
            raise Exception(
                f"Limite diário excedido. Limite: {self.daily_limit}"
                + (" (Modo Termux)" if is_termux() else "")
            )

        try:
            jobs = await self.scraper.search_jobs(
                keywords=search.keywords,
                location=search.location,
                remote_only=search.remote_only
            )
            
            self.update_usage(user_id)
            
            return jobs
        except Exception as e:
            logger.error(f"Erro ao buscar vagas: {e}")
            raise

    def get_api_usage_info(self, user_id: str) -> Dict:
        """Retorna informações de uso da API"""
        return self.get_user_usage(user_id)
