import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import threading
import json
from urllib.parse import quote
import time

class BrazilianJobSearch:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
            'Accept': 'text/html,application/json,*/*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        self.session.headers.update(self.headers)

    def search_vagas_com_br(self, query, location):
        jobs = []
        try:
            # Usando a API real do Vagas.com.br
            api_url = f"https://www.vagas.com.br/pesquisa/{quote(query)}"
            params = {'onde': location}
            response = self.session.get(api_url, params=params)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.find_all('li', class_=['vaga', 'vaga-container'])
                
                for card in cards:
                    title_elem = card.find(['a', 'h2'], class_=['link-detalhes-vaga', 'cargo'])
                    company_elem = card.find(['span', 'div'], class_=['emprVaga', 'empresa'])
                    location_elem = card.find(['span', 'div'], class_=['local', 'localizacao'])
                    
                    if title_elem:
                        url = f"https://www.vagas.com.br{title_elem.get('href', '')}"
                        jobs.append({
                            'title': title_elem.text.strip(),
                            'company': company_elem.text.strip() if company_elem else 'Empresa Confidencial',
                            'location': location_elem.text.strip() if location_elem else location,
                            'url': url,
                            'source': 'Vagas.com.br'
                        })
        except Exception as e:
            print(f"Erro Vagas.com.br: {e}")
        return jobs

    def search_trabalhabrasil(self, query, location):
        jobs = []
        try:
            # URL otimizada do Trabalha Brasil
            url = f"https://www.trabalhabrasil.com.br/api/v1.0/job-search"
            params = {
                'q': query,
                'city': location,
                'page': 1,
                'perPage': 20
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('jobs', []):
                    jobs.append({
                        'title': job.get('title'),
                        'company': job.get('company'),
                        'location': f"{job.get('city')}, {job.get('state')}",
                        'url': f"https://www.trabalhabrasil.com.br/vaga/{job.get('slug')}",
                        'source': 'Trabalha Brasil'
                    })
        except Exception as e:
            print(f"Erro Trabalha Brasil: {e}")
        return jobs

    def search_indeed(self, query, location):
        jobs = []
        try:
            # Indeed Brasil API
            url = "https://br.indeed.com/jobs"
            params = {
                'q': query,
                'l': location,
                'sort': 'date',
                'fromage': 7
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.find_all('div', class_='job_seen_beacon')
                
                for card in cards:
                    title_elem = card.find(['h2', 'a'], class_=['jobTitle', 'title'])
                    company_elem = card.find(['span', 'div'], class_=['company', 'companyName'])
                    location_elem = card.find(['div'], class_=['companyLocation'])
                    
                    if title_elem:
                        job_id = card.get('data-jk', '')
                        url = f"https://br.indeed.com/viewjob?jk={job_id}"
                        jobs.append({
                            'title': title_elem.text.strip(),
                            'company': company_elem.text.strip() if company_elem else 'Empresa não informada',
                            'location': location_elem.text.strip() if location_elem else location,
                            'url': url,
                            'source': 'Indeed'
                        })
        except Exception as e:
            print(f"Erro Indeed: {e}")
        return jobs

class CompactJobTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de Vagas BR")
        
        # Configurações iniciais da janela
        self.window_width = 800
        self.window_height = 600
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        
        # Frame principal
        self.main_frame = ttk.Frame(root, padding="5")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Controles de busca
        self.create_search_controls()
        
        # Área de resultados
        self.create_results_area()
        
        # Configuração de redimensionamento
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        self.job_searcher = BrazilianJobSearch()

    def create_search_controls(self):
        # Frame de controles
        controls = ttk.LabelFrame(self.main_frame, text="Busca", padding="5")
        controls.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Palavras-chave
        ttk.Label(controls, text="Palavras-chave:").grid(row=0, column=0, sticky="w")
        self.keywords_entry = ttk.Entry(controls, width=30)
        self.keywords_entry.grid(row=0, column=1, padx=5, pady=2)
        self.keywords_entry.insert(0, "analista de segurança")
        
        # Localização
        ttk.Label(controls, text="Localização:").grid(row=0, column=2, sticky="w")
        self.location_entry = ttk.Entry(controls, width=30)
        self.location_entry.grid(row=0, column=3, padx=5, pady=2)
        self.location_entry.insert(0, "São Paulo")
        
        # Sites de busca
        sites_frame = ttk.Frame(controls)
        sites_frame.grid(row=1, column=0, columnspan=4, pady=5)
        
        self.sites_vars = {
            'Vagas.com.br': tk.BooleanVar(value=True),
            'Trabalha Brasil': tk.BooleanVar(value=True),
            'Indeed': tk.BooleanVar(value=True)
        }
        
        for i, (site, var) in enumerate(self.sites_vars.items()):
            ttk.Checkbutton(sites_frame, text=site, variable=var).grid(row=0, column=i, padx=5)
        
        # Botão de busca e progresso
        self.search_button = ttk.Button(controls, text="Buscar", command=self.search_jobs)
        self.search_button.grid(row=2, column=3, pady=5)
        
        self.progress = ttk.Progressbar(controls, mode='determinate', length=200)
        self.progress.grid(row=2, column=0, columnspan=3, pady=5, sticky="ew")
        
        # Controle de tamanho da janela
        size_frame = ttk.Frame(controls)
        size_frame.grid(row=3, column=0, columnspan=4, pady=5)
        
        ttk.Label(size_frame, text="Tamanho da Janela:").grid(row=0, column=0, padx=5)
        sizes = ['800x600', '1024x768', '1280x720']
        self.size_var = tk.StringVar(value=sizes[0])
        size_combo = ttk.Combobox(size_frame, textvariable=self.size_var, values=sizes, state='readonly', width=15)
        size_combo.grid(row=0, column=1, padx=5)
        size_combo.bind('<<ComboboxSelected>>', self.change_window_size)

    def create_results_area(self):
        # Frame de resultados
        results_frame = ttk.Frame(self.main_frame)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configurar TreeView
        columns = ('título', 'empresa', 'local', 'fonte')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        # Cabeçalhos
        for col in columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=int(self.window_width/len(columns)))
        
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
        
        # Status
        self.status_var = tk.StringVar()
        ttk.Label(results_frame, textvariable=self.status_var).grid(row=2, column=0, sticky="w")

    def change_window_size(self, event=None):
        size = self.size_var.get().split('x')
        self.window_width = int(size[0])
        self.window_height = int(size[1])
        self.root.geometry(f"{self.window_width}x{self.window_height}")

    def search_jobs(self):
        keywords = self.keywords_entry.get()
        location = self.location_entry.get()
        
        if not keywords or not location:
            messagebox.showwarning("Aviso", "Preencha palavras-chave e localização")
            return
        
        self.tree.delete(*self.tree.get_children())
        self.search_button.state(['disabled'])
        self.progress['value'] = 0
        
        def search_thread():
            all_jobs = []
            active_sites = [site for site, var in self.sites_vars.items() if var.get()]
            progress_step = 100 / len(active_sites)
            
            try:
                for i, site in enumerate(active_sites):
                    self.status_var.set(f"Buscando em {site}...")
                    
                    if site == 'Vagas.com.br':
                        jobs = self.job_searcher.search_vagas_com_br(keywords, location)
                    elif site == 'Trabalha Brasil':
                        jobs = self.job_searcher.search_trabalhabrasil(keywords, location)
                    elif site == 'Indeed':
                        jobs = self.job_searcher.search_indeed(keywords, location)
                    
                    all_jobs.extend(jobs)
                    self.progress['value'] = (i + 1) * progress_step
                    time.sleep(1)  # Evitar sobrecarga
                
                self.root.after(0, lambda: self.display_results(all_jobs))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_error(str(e)))
        
        threading.Thread(target=search_thread, daemon=True).start()

    def display_results(self, jobs):
        self.tree.delete(*self.tree.get_children())
        
        if not jobs:
            self.status_var.set("Nenhuma vaga encontrada")
        else:
            for job in jobs:
                self.tree.insert('', 'end', values=(
                    job['title'],
                    job['company'],
                    job['location'],
                    job['source']
                ), tags=(job['url'],))
            
            self.status_var.set(f"Encontradas {len(jobs)} vagas")
        
        self.search_button.state(['!disabled'])
        self.progress['value'] = 100

    def open_job_url(self, event):
        item = self.tree.selection()[0]
        url = self.tree.item(item)['tags'][0]
        import webbrowser
        webbrowser.open(url)

    def handle_error(self, error_message):
        self.status_var.set(f"Erro: {error_message}")
        self.search_button.state(['!disabled'])
        self.progress['value'] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = CompactJobTracker(root)
    root.mainloop()
