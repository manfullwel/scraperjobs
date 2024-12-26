import logging
import random
import time
from typing import Optional
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from selenium_stealth import stealth

from ..config import settings

logger = logging.getLogger(__name__)

class WebDriverManager:
    def __init__(self):
        self.user_agent = UserAgent()
    
    def get_webdriver(self) -> uc.Chrome:
        try:
            # Usar undetected-chromedriver como base
            options = uc.ChromeOptions()
            
            # User agent aleatório
            user_agent = self.user_agent.random
            options.add_argument(f'--user-agent={user_agent}')
            logger.info(f"Usando User-Agent: {user_agent}")
            
            # Configurações básicas
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-infobars')
            
            # Criar driver não detectável
            driver = uc.Chrome(options=options, use_subprocess=True)
            
            # Aplicar técnicas de stealth
            stealth(driver,
                languages=["pt-BR", "pt", "en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            # Configurar tamanho da janela
            driver.set_window_size(1920, 1080)
            
            # Limpar cookies e cache
            driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
            driver.execute_cdp_cmd('Network.clearBrowserCache', {})
            
            # Aguardar um pouco para garantir que tudo foi carregado
            time.sleep(2)
            
            # Configurar timeouts
            driver.set_page_load_timeout(settings.TIMEOUT)
            driver.implicitly_wait(settings.TIMEOUT)
            
            return driver
            
        except Exception as e:
            logger.error(f"Erro ao criar WebDriver: {str(e)}")
            raise
