import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import threading
import json
from urllib.parse import quote, urlencode
import time
import random

class BrazilianJobSearcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search_vagas(self, query, location):
        """Search jobs on Vagas.com.br"""
        jobs = []
        try:
            # Vagas.com.br search URL
            url = f"https://www.vagas.com.br/vagas-de-{quote(query.replace(' ', '-'))}?onde={quote(location)}"
            response = self.session.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('li', class_='vaga')
                
                for card in job_cards[:10]:
                    try:
                        title = card.find('a', class_='link-detalhes-vaga')
                        company = card.find('span', class_='emprVaga')
                        location = card.find('span', class_='local')
                        
                        if title and company:
                            job_url = f"https://www.vagas.com.br{title['href']}"
                            jobs.append({
                                'title': title.get_text(strip=True),
                                'company': company.get_text(strip=True),
                                'location': location.get_text(strip=True) if location else '',
                                'url': job_url,
                                'source': 'Vagas.com.br'
                            })
                    except Exception as e:
                        print(f"Error processing Vagas.com.br job: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error searching Vagas.com.br: {e}")
        return jobs

    def search_infojobs(self, query, location):
        """Search jobs on InfoJobs"""
        jobs = []
        try:
            # InfoJobs search URL
            url = f"https://www.infojobs.com.br/empregos.aspx?palabra={quote(query)}&ubicacion={quote(location)}"
            response = self.session.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='vaga')
                
                for card in job_cards[:10]:
                    try:
                        title = card.find('h2', class_='vaga-title')
                        company = card.find('span', class_='company-name')
                        location = card.find('span', class_='location')
                        link = card.find('a', class_='vaga-link')
                        
                        if title and company and link:
                            job_url = f"https://www.infojobs.com.br{link['href']}"
                            jobs.append({
                                'title': title.get_text(strip=True),
                                'company': company.get_text(strip=True),
                                'location': location.get_text(strip=True) if location else '',
                                'url': job_url,
                                'source': 'InfoJobs'
                            })
                    except Exception as e:
                        print(f"Error processing InfoJobs job: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error searching InfoJobs: {e}")
        return jobs

    def search_catho(self, query, location):
        """Search jobs on Catho"""
        jobs = []
        try:
            # Catho search URL
            url = f"https://www.catho.com.br/vagas/{quote(query)}/{quote(location)}/"
            response = self.session.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='job-card')
                
                for card in job_cards[:10]:
                    try:
                        title = card.find('h2', class_='job-title')
                        company = card.find('div', class_='company-name')
                        location = card.find('div', class_='location')
                        link = card.find('a', class_='job-link')
                        
                        if title and link:
                            job_url = f"https://www.catho.com.br{link['href']}"
                            jobs.append({
                                'title': title.get_text(strip=True),
                                'company': company.get_text(strip=True) if company else 'Empresa Confidencial',
                                'location': location.get_text(strip=True) if location else '',
                                'url': job_url,
                                'source': 'Catho'
                            })
                    except Exception as e:
                        print(f"Error processing Catho job: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error searching Catho: {e}")
        return jobs

class BrazilianJobTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de Vagas no Brasil")
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Search Frame
        self.search_frame = ttk.LabelFrame(self.main_frame, text="Buscar Vagas", padding="5")
        self.search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Job Source Selection
        ttk.Label(self.search_frame, text="Sites de Busca:").grid(row=0, column=0, sticky=tk.W)
        self.sources_frame = ttk.Frame(self.search_frame)
        self.sources_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        
        self.source_vars = {
            'Vagas.com.br': tk.BooleanVar(value=True),
            'InfoJobs': tk.BooleanVar(value=True),
            'Catho': tk.BooleanVar(value=True)
        }
        
        for i, (source, var) in enumerate(self.source_vars.items()):
            ttk.Checkbutton(self.sources_frame, text=source, variable=var).grid(row=0, column=i, padx=5)
        
        # Keywords field
        ttk.Label(self.search_frame, text="Palavras-chave:").grid(row=1, column=0, sticky=tk.W)
        self.keywords_entry = ttk.Entry(self.search_frame, width=40)
        self.keywords_entry.grid(row=1, column=1, padx=5, pady=5)
        self.keywords_entry.insert(0, "analista de segurança")
        
        # Location field
        ttk.Label(self.search_frame, text="Localização:").grid(row=2, column=0, sticky=tk.W)
        self.location_entry = ttk.Entry(self.search_frame, width=40)
        self.location_entry.grid(row=2, column=1, padx=5, pady=5)
        self.location_entry.insert(0, "São Paulo")
        
        # Search button
        self.search_button = ttk.Button(self.search_frame, text="Buscar", command=self.search_jobs)
        self.search_button.grid(row=3, column=1, pady=10)
        
        # Status label
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self.search_frame, textvariable=self.status_var)
        self.status_label.grid(row=4, column=0, columnspan=2)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.search_frame, length=300, mode='determinate', variable=self.progress_var)
        self.progress.grid(row=5, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Results area
        self.results_text = tk.Text(self.main_frame, width=80, height=20)
        self.results_text.grid(row=6, column=0, columnspan=2, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.results_text.yview)
        scrollbar.grid(row=6, column=2, sticky="ns")
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.job_searcher = BrazilianJobSearcher()

    def search_jobs(self):
        keywords = self.keywords_entry.get()
        location = self.location_entry.get()
        
        if not keywords or not location:
            messagebox.showwarning("Campos Obrigatórios", "Por favor, preencha as palavras-chave e a localização")
            return
        
        self.search_button.config(state='disabled')
        self.progress_var.set(0)
        self.results_text.delete("1.0", tk.END)
        
        def search_thread():
            all_jobs = []
            active_sources = [source for source, var in self.source_vars.items() if var.get()]
            progress_step = 100 / len(active_sources)
            
            try:
                for i, source in enumerate(active_sources):
                    self.status_var.set(f"Buscando em {source}...")
                    
                    if source == 'Vagas.com.br':
                        jobs = self.job_searcher.search_vagas(keywords, location)
                    elif source == 'InfoJobs':
                        jobs = self.job_searcher.search_infojobs(keywords, location)
                    elif source == 'Catho':
                        jobs = self.job_searcher.search_catho(keywords, location)
                    
                    all_jobs.extend(jobs)
                    self.progress_var.set((i + 1) * progress_step)
                    time.sleep(1)  # Prevent overwhelming the sites
                
                self.root.after(0, lambda: self.display_results(all_jobs))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_error(str(e)))
        
        threading.Thread(target=search_thread, daemon=True).start()

    def display_results(self, jobs):
        self.results_text.delete("1.0", tk.END)
        
        if not jobs:
            self.results_text.insert(tk.END, "Nenhuma vaga encontrada. Tente diferentes palavras-chave ou localização.\n")
        else:
            for job in jobs:
                job_info = f"""
Fonte: {job['source']}
Cargo: {job['title']}
Empresa: {job['company']}
Local: {job['location']}
URL: {job['url']}
------------------------
"""
                self.results_text.insert(tk.END, job_info)
        
        self.status_var.set(f"Encontradas {len(jobs)} vagas")
        self.search_button.config(state='normal')
        self.progress_var.set(100)

    def handle_error(self, error_message):
        self.status_var.set("Erro durante a busca")
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, f"Erro: {error_message}\n")
        self.search_button.config(state='normal')
        self.progress_var.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = BrazilianJobTracker(root)
    root.mainloop()