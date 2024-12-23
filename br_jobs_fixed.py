import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import threading
import json
from urllib.parse import quote, urlencode
import time

class JobSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        self.session.headers.update(self.headers)

    def search_linkedin(self, query, location):
        jobs = []
        try:
            # LinkedIn search URL
            base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            params = {
                'keywords': query,
                'location': location,
                'geoId': '',
                'trk': 'public_jobs_jobs-search-bar_search-submit',
                'start': 0
            }
            
            response = self.session.get(base_url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='base-card')
                
                for card in job_cards:
                    try:
                        title = card.find('h3', class_='base-search-card__title')
                        company = card.find('h4', class_='base-search-card__subtitle')
                        location = card.find('span', class_='job-search-card__location')
                        link = card.find('a', class_='base-card__full-link')
                        
                        if title and link:
                            jobs.append({
                                'title': title.get_text(strip=True),
                                'company': company.get_text(strip=True) if company else 'Empresa não informada',
                                'location': location.get_text(strip=True) if location else '',
                                'url': link['href'].split('?')[0],
                                'source': 'LinkedIn'
                            })
                    except Exception as e:
                        print(f"Erro processando vaga LinkedIn: {e}")
                        continue
                        
        except Exception as e:
            print(f"Erro na busca LinkedIn: {e}")
        return jobs

    def search_gupy(self, query, location):
        jobs = []
        try:
            # Gupy API endpoint
            url = "https://portal.api.gupy.io/api/job"
            params = {
                'jobName': query,
                'cityName': location,
                'limit': 20,
                'offset': 0
            }
            
            headers = {
                **self.headers,
                'Origin': 'https://portal.gupy.io',
                'Referer': 'https://portal.gupy.io/'
            }
            
            response = self.session.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('data', []):
                    jobs.append({
                        'title': job.get('name', ''),
                        'company': job.get('company', {}).get('name', 'Empresa não informada'),
                        'location': f"{job.get('city', '')}, {job.get('state', '')}",
                        'url': f"https://portal.gupy.io/job/{job.get('id')}",
                        'source': 'Gupy'
                    })
        except Exception as e:
            print(f"Erro na busca Gupy: {e}")
        return jobs

    def search_vagas(self, query, location):
        jobs = []
        try:
            # Vagas.com.br search
            url = f"https://www.vagas.com.br/vagas-de-{quote(query.replace(' ', '-'))}"
            params = {'onde': location}
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all(['li', 'div'], class_=['vaga', 'vaga-container'])
                
                for card in job_cards:
                    try:
                        title_elem = card.find(['a', 'h2'], class_=['link-detalhes-vaga', 'cargo'])
                        company_elem = card.find(['span', 'div'], class_=['emprVaga', 'empresa'])
                        location_elem = card.find(['span', 'div'], class_='local')
                        
                        if title_elem:
                            url = f"https://www.vagas.com.br{title_elem.get('href', '')}"
                            jobs.append({
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else 'Empresa Confidencial',
                                'location': location_elem.get_text(strip=True) if location_elem else location,
                                'url': url,
                                'source': 'Vagas.com.br'
                            })
                    except Exception as e:
                        print(f"Erro processando vaga Vagas.com.br: {e}")
                        continue
                        
        except Exception as e:
            print(f"Erro na busca Vagas.com.br: {e}")
        return jobs

class JobTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de Vagas")
        self.root.geometry("900x600")
        
        # Frame principal
        self.main_frame = ttk.Frame(root, padding="5")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Área de busca
        self.create_search_area()
        
        # Área de resultados
        self.create_results_area()
        
        # Configuração de redimensionamento
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        self.job_searcher = JobSearcher()

    def create_search_area(self):
        search_frame = ttk.LabelFrame(self.main_frame, text="Busca", padding="5")
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Palavras-chave
        ttk.Label(search_frame, text="Palavras-chave:").grid(row=0, column=0, sticky="w")
        self.keywords_entry = ttk.Entry(search_frame, width=30)
        self.keywords_entry.grid(row=0, column=1, padx=5, pady=2)
        self.keywords_entry.insert(0, "analista de segurança")
        
        # Localização
        ttk.Label(search_frame, text="Localização:").grid(row=0, column=2, sticky="w")
        self.location_entry = ttk.Entry(search_frame, width=30)
        self.location_entry.grid(row=0, column=3, padx=5, pady=2)
        self.location_entry.insert(0, "São Paulo")
        
        # Sites de busca
        self.sites_vars = {
            'LinkedIn': tk.BooleanVar(value=True),
            'Gupy': tk.BooleanVar(value=True),
            'Vagas.com.br': tk.BooleanVar(value=True)
        }
        
        sites_frame = ttk.Frame(search_frame)
        sites_frame.grid(row=1, column=0, columnspan=4, pady=5)
        
        for i, (site, var) in enumerate(self.sites_vars.items()):
            ttk.Checkbutton(sites_frame, text=site, variable=var).grid(row=0, column=i, padx=5)
        
        # Botão de busca e progresso
        self.search_button = ttk.Button(search_frame, text="Buscar Vagas", command=self.search_jobs)
        self.search_button.grid(row=2, column=3, pady=5)
        
        self.progress = ttk.Progressbar(search_frame, mode='determinate', length=200)
        self.progress.grid(row=2, column=0, columnspan=3, pady=5, sticky="ew")
        
        # Status
        self.status_var = tk.StringVar()
        ttk.Label(search_frame, textvariable=self.status_var).grid(row=3, column=0, columnspan=4)

    def create_results_area(self):
        # Frame de resultados
        results_frame = ttk.Frame(self.main_frame)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configurar TreeView
        columns = ('título', 'empresa', 'local', 'fonte')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings')
        
        # Cabeçalhos
        for col in columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=200)
        
        # Scrollbars
        ysb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        
        # Grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        
        # Configurar redimensionamento
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Bind para abrir URL
        self.tree.bind('<Double-1>', self.open_job_url)

    def search_jobs(self):
        keywords = self.keywords_entry.get()
        location = self.location_entry.get()
        
        if not keywords or not location:
            messagebox.showwarning("Aviso", "Preencha palavras-chave e localização")
            return
        
        self.tree.delete(*self.tree.get_children())
        self.search_button.state(['disabled'])
        self.progress['value'] = 0
        self.status_var.set("Iniciando busca...")
        
        def search_thread():
            all_jobs = []
            active_sites = [site for site, var in self.sites_vars.items() if var.get()]
            progress_step = 100 / len(active_sites)
            
            try:
                for i, site in enumerate(active_sites):
                    self.status_var.set(f"Buscando em {site}...")
                    print(f"Buscando em {site}...")  # Debug
                    
                    if site == 'LinkedIn':
                        jobs = self.job_searcher.search_linkedin(keywords, location)
                    elif site == 'Gupy':
                        jobs = self.job_searcher.search_gupy(keywords, location)
                    elif site == 'Vagas.com.br':
                        jobs = self.job_searcher.search_vagas(keywords, location)
                    
                    print(f"Encontradas {len(jobs)} vagas em {site}")  # Debug
                    all_jobs.extend(jobs)
                    self.progress['value'] = (i + 1) * progress_step
                    time.sleep(1)  # Prevenir sobrecarga
                
                self.root.after(0, lambda: self.display_results(all_jobs))
                
            except Exception as e:
                print(f"Erro na thread de busca: {e}")  # Debug
                self.root.after(0, lambda: self.handle_error(str(e)))
        
        threading.Thread(target=search_thread, daemon=True).start()

    def display_results(self, jobs):
        self.tree.delete(*self.tree.get_children())
        
        if not jobs:
            self.status_var.set("Nenhuma vaga encontrada")
            print("Nenhuma vaga encontrada")  # Debug
        else:
            for job in jobs:
                self.tree.insert('', 'end', values=(
                    job['title'],
                    job['company'],
                    job['location'],
                    job['source']
                ), tags=(job['url'],))
            
            self.status_var.set(f"Encontradas {len(jobs)} vagas")
            print(f"Total de vagas encontradas: {len(jobs)}")  # Debug
        
        self.search_button.state(['!disabled'])
        self.progress['value'] = 100

    def open_job_url(self, event):
        item = self.tree.selection()[0]
        url = self.tree.item(item)['tags'][0]
        import webbrowser
        webbrowser.open(url)

    def handle_error(self, error_message):
        self.status_var.set(f"Erro: {error_message}")
        print(f"Erro: {error_message}")  # Debug
        self.search_button.state(['!disabled'])
        self.progress['value'] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = JobTracker(root)
    root.mainloop()
