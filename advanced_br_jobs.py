import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
import threading
import json
from urllib.parse import quote, urlencode, urlparse
import time
import random
import re
from datetime import datetime

class APIJobSearcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Origin': 'https://programathor.com.br',
            'Referer': 'https://programathor.com.br/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search_programathor(self, query, location, max_results=10):
        jobs = []
        try:
            # ProgramaThor API endpoint
            api_url = "https://api.programathor.com.br/v1/jobs"
            params = {
                'search': query,
                'city': location,
                'page': 1,
                'per_page': max_results
            }
            
            response = self.session.get(api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('jobs', []):
                    jobs.append({
                        'title': job.get('title'),
                        'company': job.get('company', {}).get('name'),
                        'location': f"{job.get('city', '')}, {job.get('state', '')}",
                        'salary': job.get('salary_range', 'Não informado'),
                        'remote': 'Remoto' if job.get('remote') else 'Presencial',
                        'url': f"https://programathor.com.br/jobs/{job.get('slug')}",
                        'skills': ', '.join(job.get('skills', [])),
                        'source': 'ProgramaThor'
                    })
        except Exception as e:
            print(f"Error in ProgramaThor search: {e}")
        return jobs

    def search_gupy(self, query, location, max_results=10):
        jobs = []
        try:
            # Gupy API endpoint
            api_url = "https://portal.api.gupy.io/api/v1/jobs"
            params = {
                'jobName': query,
                'city': location,
                'limit': max_results,
                'offset': 0
            }
            
            response = self.session.get(api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('data', []):
                    jobs.append({
                        'title': job.get('name'),
                        'company': job.get('company', {}).get('name'),
                        'location': f"{job.get('city', '')}, {job.get('state', '')}",
                        'remote': job.get('workplaceType', 'Não especificado'),
                        'url': f"https://portal.gupy.io/job/{job.get('id')}",
                        'skills': job.get('requirements', 'Não especificado'),
                        'source': 'Gupy'
                    })
        except Exception as e:
            print(f"Error in Gupy search: {e}")
        return jobs

    def search_custom_url(self, url, max_results=10):
        jobs = []
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try different common job listing selectors
                job_cards = []
                selectors = [
                    'div[class*="job"]', 'div[class*="vaga"]',
                    'article[class*="job"]', 'div[class*="card"]',
                    'li[class*="job"]', 'div[class*="opportunity"]'
                ]
                
                for selector in selectors:
                    job_cards = soup.select(selector)
                    if job_cards:
                        break
                
                for card in job_cards[:max_results]:
                    try:
                        # Try multiple possible selectors for each field
                        title = self._find_text(card, ['h1', 'h2', 'h3', 'a'], ['title', 'job', 'vaga'])
                        company = self._find_text(card, ['span', 'div', 'p'], ['company', 'empresa'])
                        location = self._find_text(card, ['span', 'div', 'p'], ['location', 'local'])
                        link = card.find('a', href=True)
                        
                        if title and link:
                            job_url = link['href'] if link['href'].startswith('http') else f"{urlparse(url).scheme}://{urlparse(url).netloc}{link['href']}"
                            jobs.append({
                                'title': title,
                                'company': company or 'Empresa não especificada',
                                'location': location or 'Local não especificado',
                                'url': job_url,
                                'source': 'Custom URL'
                            })
                    except Exception as e:
                        print(f"Error processing custom URL job card: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error in custom URL search: {e}")
        return jobs

    def _find_text(self, soup, tags, classes):
        for tag in tags:
            for class_pattern in classes:
                element = soup.find(tag, class_=re.compile(class_pattern, re.I))
                if element:
                    return element.get_text(strip=True)
        return None

class AdvancedJobTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador Avançado de Vagas no Brasil")
        self.root.geometry("1200x800")
        
        # Configure grid weight
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Search Frame
        self.create_search_frame()
        
        # Results Frame
        self.create_results_frame()
        
        self.job_searcher = APIJobSearcher()

    def create_search_frame(self):
        # Search Frame
        self.search_frame = ttk.LabelFrame(self.main_frame, text="Configurações de Busca", padding="5")
        self.search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Keywords and Location
        ttk.Label(self.search_frame, text="Palavras-chave:").grid(row=0, column=0, sticky=tk.W)
        self.keywords_entry = ttk.Entry(self.search_frame, width=40)
        self.keywords_entry.grid(row=0, column=1, padx=5, pady=5)
        self.keywords_entry.insert(0, "analista de segurança")
        
        ttk.Label(self.search_frame, text="Localização:").grid(row=0, column=2, sticky=tk.W)
        self.location_entry = ttk.Entry(self.search_frame, width=40)
        self.location_entry.grid(row=0, column=3, padx=5, pady=5)
        self.location_entry.insert(0, "São Paulo")
        
        # Custom URL
        ttk.Label(self.search_frame, text="URL Personalizada:").grid(row=1, column=0, sticky=tk.W)
        self.custom_url_entry = ttk.Entry(self.search_frame, width=85)
        self.custom_url_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5)
        
        # Results quantity
        ttk.Label(self.search_frame, text="Quantidade de resultados:").grid(row=2, column=0, sticky=tk.W)
        self.results_var = tk.StringVar(value="10")
        self.results_spinbox = ttk.Spinbox(self.search_frame, from_=1, to=50, width=5, textvariable=self.results_var)
        self.results_spinbox.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Source Selection
        self.sources_frame = ttk.LabelFrame(self.search_frame, text="Fontes de Busca", padding="5")
        self.sources_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        self.source_vars = {
            'ProgramaThor': tk.BooleanVar(value=True),
            'Gupy': tk.BooleanVar(value=True),
            'URL Personalizada': tk.BooleanVar(value=False)
        }
        
        for i, (source, var) in enumerate(self.source_vars.items()):
            ttk.Checkbutton(self.sources_frame, text=source, variable=var).grid(row=0, column=i, padx=5)
        
        # Search button and progress
        self.search_button = ttk.Button(self.search_frame, text="Buscar Vagas", command=self.search_jobs)
        self.search_button.grid(row=4, column=3, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.search_frame, length=400, mode='determinate', variable=self.progress_var)
        self.progress.grid(row=4, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        # Status
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self.search_frame, textvariable=self.status_var)
        self.status_label.grid(row=5, column=0, columnspan=4)

    def create_results_frame(self):
        # Results Frame with Treeview
        self.results_frame = ttk.Frame(self.main_frame)
        self.results_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure Treeview
        columns = ('source', 'title', 'company', 'location', 'remote', 'skills')
        self.tree = ttk.Treeview(self.results_frame, columns=columns, show='headings')
        
        # Define headings
        headings = {
            'source': 'Fonte',
            'title': 'Cargo',
            'company': 'Empresa',
            'location': 'Local',
            'remote': 'Remoto',
            'skills': 'Habilidades'
        }
        
        for col, heading in headings.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=150)
        
        # Add scrollbars
        ysb = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        xsb = ttk.Scrollbar(self.results_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ysb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        xsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        # Configure grid weights
        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click event
        self.tree.bind('<Double-1>', self.open_job_url)
        
        # Details text area
        self.details_text = scrolledtext.ScrolledText(self.results_frame, height=10)
        self.details_text.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def search_jobs(self):
        keywords = self.keywords_entry.get()
        location = self.location_entry.get()
        custom_url = self.custom_url_entry.get()
        max_results = int(self.results_var.get())
        
        if not any(var.get() for var in self.source_vars.values()):
            messagebox.showwarning("Aviso", "Selecione pelo menos uma fonte de busca")
            return
            
        if not keywords and not custom_url:
            messagebox.showwarning("Aviso", "Digite palavras-chave ou uma URL personalizada")
            return
        
        self.search_button.config(state='disabled')
        self.progress_var.set(0)
        self.tree.delete(*self.tree.get_children())
        self.details_text.delete('1.0', tk.END)
        
        def search_thread():
            all_jobs = []
            active_sources = [source for source, var in self.source_vars.items() if var.get()]
            progress_step = 100 / len(active_sources)
            
            try:
                for i, source in enumerate(active_sources):
                    self.status_var.set(f"Buscando em {source}...")
                    
                    if source == 'ProgramaThor':
                        jobs = self.job_searcher.search_programathor(keywords, location, max_results)
                    elif source == 'Gupy':
                        jobs = self.job_searcher.search_gupy(keywords, location, max_results)
                    elif source == 'URL Personalizada' and custom_url:
                        jobs = self.job_searcher.search_custom_url(custom_url, max_results)
                    
                    all_jobs.extend(jobs)
                    self.progress_var.set((i + 1) * progress_step)
                
                self.root.after(0, lambda: self.display_results(all_jobs))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_error(str(e)))
        
        threading.Thread(target=search_thread, daemon=True).start()

    def display_results(self, jobs):
        self.tree.delete(*self.tree.get_children())
        
        if not jobs:
            self.status_var.set("Nenhuma vaga encontrada")
            self.details_text.insert(tk.END, "Nenhuma vaga encontrada. Tente diferentes palavras-chave ou fontes de busca.")
        else:
            for job in jobs:
                self.tree.insert('', tk.END, values=(
                    job['source'],
                    job['title'],
                    job['company'],
                    job['location'],
                    job.get('remote', 'N/A'),
                    job.get('skills', 'N/A')
                ))
            
            self.status_var.set(f"Encontradas {len(jobs)} vagas")
        
        self.search_button.config(state='normal')
        self.progress_var.set(100)

    def open_job_url(self, event):
        item = self.tree.selection()[0]
        job_values = self.tree.item(item)['values']
        # Assuming URL is stored in the tree item
        if len(job_values) > 5:
            url = job_values[5]
            import webbrowser
            webbrowser.open(url)

    def handle_error(self, error_message):
        self.status_var.set("Erro durante a busca")
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert(tk.END, f"Erro: {error_message}")
        self.search_button.config(state='normal')
        self.progress_var.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedJobTracker(root)
    root.mainloop()
