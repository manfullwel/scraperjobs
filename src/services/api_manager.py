import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class APIUsageManager:
    """Gerenciador de uso de APIs com limites"""
    
    def __init__(self, storage_path: str = "api_usage.json"):
        self.storage_path = Path(storage_path)
        self.usage_data = self._load_usage_data()
        
    def _load_usage_data(self) -> Dict:
        """Carregar dados de uso do arquivo"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar dados de uso: {e}")
                return {}
        return {}
    
    def _save_usage_data(self):
        """Salvar dados de uso no arquivo"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar dados de uso: {e}")
    
    def can_use_api(self, api_name: str, user_id: str, daily_limit: int) -> bool:
        """Verificar se pode usar a API baseado nos limites"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Inicializar dados se necessário
        if api_name not in self.usage_data:
            self.usage_data[api_name] = {}
        if user_id not in self.usage_data[api_name]:
            self.usage_data[api_name][user_id] = {}
        
        # Limpar dados antigos
        self._cleanup_old_data(api_name, user_id)
        
        # Verificar uso do dia
        daily_usage = self.usage_data[api_name][user_id].get(today, 0)
        return daily_usage < daily_limit
    
    def record_api_use(self, api_name: str, user_id: str, count: int = 1):
        """Registrar uso da API"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if api_name not in self.usage_data:
            self.usage_data[api_name] = {}
        if user_id not in self.usage_data[api_name]:
            self.usage_data[api_name][user_id] = {}
        
        current_usage = self.usage_data[api_name][user_id].get(today, 0)
        self.usage_data[api_name][user_id][today] = current_usage + count
        
        self._save_usage_data()
    
    def get_remaining_calls(self, api_name: str, user_id: str, daily_limit: int) -> int:
        """Obter número de chamadas restantes para hoje"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_usage = self.usage_data.get(api_name, {}).get(user_id, {}).get(today, 0)
        return max(0, daily_limit - current_usage)
    
    def _cleanup_old_data(self, api_name: str, user_id: str):
        """Limpar dados mais antigos que 30 dias"""
        if api_name in self.usage_data and user_id in self.usage_data[api_name]:
            today = datetime.now()
            user_data = self.usage_data[api_name][user_id]
            
            # Remover datas antigas
            old_dates = []
            for date_str in user_data:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if (today - date) > timedelta(days=30):
                    old_dates.append(date_str)
            
            for date_str in old_dates:
                del user_data[date_str]
            
            self._save_usage_data()
