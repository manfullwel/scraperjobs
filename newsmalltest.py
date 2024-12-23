import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import webbrowser
from bs4 import BeautifulSoup
import json
import threading
import re
from urllib.parse import urljoin, urlparse, quote_plus
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class JobScraper:
    def __init__(self):
        self.db_path = 'jobs.db'
        self.setup_database()
        self.job_sites = {
            'LinkedIn': {
                'base_url': 'https://www.linkedin.com/jobs/search/?keywords={}&location={}',
                'selectors': {
                    'job_cards': '.jobs-search__results-list > li',
                    'title': '.base-search-card__title',
                    'company': '.base-search-card__subtitle',
                    'location': '.job-search-card__location',
                    'description': '.base-card-body',
                    'posted_date': 'time',
                    'job_type': '[class*="job-type"]',
                    'salary': '[class*="salary"]'
                }
            },
            'Indeed': {
                'base_url': 'https://www.indeed.com/jobs?q={}&l={}',
                'selectors': {
                    'job_cards': '.jobsearch-SerpJobCard',
                    'title': '.title a',
                    'company': '.company',
                    'location': '.location',
                    'description': '.summary',
                    'posted_date': '.date',
                    'job_type': '.jobType',
                    'salary': '.salaryText'
                }
            },
            'Glassdoor': {
                'base_url': 'https://www.glassdoor.com/Job/jobs.htm?sc.keyword={}&locT=C&locId={}',
                'selectors': {
                    'job_cards': '.jl',
                    'title': '.jobLink',
                    'company': '.jobEmpolyerName',
                    'location': '.loc',
                    'description': '.jobDesc',
                    'posted_date': '.jobLabels .jobLabel',
                    'job_type': '.jobType',
                    'salary': '.salaryEstimate'
                }
            }
        }

    def setup_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    description TEXT,
                    url TEXT UNIQUE,
                    source TEXT,
                    date_added TIMESTAMP,
                    posted_date TEXT,
                    job_type TEXT,
                    salary TEXT,
                    requirements TEXT,
                    remote BOOLEAN,
                    UNIQUE(url, source)
                )
            ''')

    def scrape_jobs(self, keywords, location):
        all_jobs = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            for site_name, site_info in self.job_sites.items():
                try:
                    page = context.new_page()
                    jobs = self._scrape_site(page, site_name, site_info, keywords, location)
                    all_jobs.extend(jobs)
                    page.close()
                except Exception as e:
                    print(f"Error scraping {site_name}: {str(e)}")
                    continue
                
            browser.close()
        return all_jobs

    def _scrape_site(self, page, site_name, site_info, keywords, location):
        jobs = []
        try:
            # Format URL based on site
            if site_name in ['LinkedIn', 'Indeed']:
                url = site_info['base_url'].format(quote_plus(keywords), quote_plus(location))
            elif site_name == 'Glassdoor':
                url = site_info['base_url'].format(quote_plus(keywords), quote_plus(location))
            
            # Navigate to page
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for job cards to load
            page.wait_for_selector(site_info['selectors']['job_cards'], timeout=10000)
            
            # Scroll to load more jobs
            self._scroll_page(page)
            
            # Get page content and parse
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all job cards
            job_cards = soup.select(site_info['selectors']['job_cards'])
            
            for card in job_cards:
                job_data = self._extract_job_data(card, site_info['selectors'], site_name, url)
                if job_data:
                    jobs.append(job_data)
            
        except PlaywrightTimeoutError:
            print(f"Timeout while loading {site_name}")
        except Exception as e:
            print(f"Error scraping {site_name}: {str(e)}")
        
        return jobs

    def _scroll_page(self, page):
        try:
            # Scroll slowly to simulate human behavior and load dynamic content
            for _ in range(5):  # Scroll 5 times
                page.evaluate('window.scrollBy(0, window.innerHeight)')
                time.sleep(random.uniform(0.5, 1.0))  # Random delay between scrolls
                
            # Wait for any new content to load
            page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")

    def _extract_job_data(self, card, selectors, source, base_url):
        try:
            # Extract basic information
            title_elem = card.select_one(selectors['title'])
            company_elem = card.select_one(selectors['company'])
            location_elem = card.select_one(selectors['location'])
            description_elem = card.select_one(selectors['description'])
            posted_date_elem = card.select_one(selectors['posted_date'])
            job_type_elem = card.select_one(selectors['job_type'])
            salary_elem = card.select_one(selectors['salary'])

            # Get URL
            url = None
            if title_elem and title_elem.name == 'a':
                url = title_elem.get('href')
            else:
                url_elem = card.find('a')
                if url_elem:
                    url = url_elem.get('href')

            if url:
                url = urljoin(base_url, url)

            # Check if we have at least title and company
            if not (title_elem and company_elem):
                return None

            # Extract text content
            job_data = {
                'title': title_elem.get_text(strip=True) if title_elem else 'Não especificado',
                'company': company_elem.get_text(strip=True) if company_elem else 'Não especificado',
                'location': location_elem.get_text(strip=True) if location_elem else 'Não especificado',
                'description': description_elem.get_text(strip=True) if description_elem else '',
                'url': url,
                'source': source,
                'posted_date': posted_date_elem.get_text(strip=True) if posted_date_elem else 'Não especificado',
                'job_type': job_type_elem.get_text(strip=True) if job_type_elem else 'Não especificado',
                'salary': salary_elem.get_text(strip=True) if salary_elem else 'Não especificado',
                'remote': self._is_remote(location_elem, description_elem)
            }

            # Extract requirements from description
            job_data['requirements'] = self._extract_requirements(job_data['description'])

            return job_data
        except Exception as e:
            print(f"Error extracting job data: {str(e)}")
            return None

    def _is_remote(self, location_elem, description_elem):
        remote_keywords = ['remoto', 'remote', 'home office', 'trabalho remoto', 'híbrido', 'hybrid']
        text = ''
        if location_elem:
            text += location_elem.get_text(strip=True).lower()
        if description_elem:
            text += description_elem.get_text(strip=True).lower()
        return any(keyword in text for keyword in remote_keywords)

    def _extract_requirements(self, description):
        if not description:
            return ''
        
        # Common requirement indicators
        requirement_patterns = [
            r'requisitos:.*?(?=\n|$)',
            r'requirements:.*?(?=\n|$)',
            r'necessário:.*?(?=\n|$)',
            r'perfil:.*?(?=\n|$)',
            r'qualificações:.*?(?=\n|$)',
            r'experiência.*?(?=\n|$)'
        ]
        
        requirements = []
        for pattern in requirement_patterns:
            matches = re.finditer(pattern, description.lower(), re.IGNORECASE | re.MULTILINE)
            for match in matches:
                requirements.append(match.group(0))
        
        return ' | '.join(requirements) if requirements else ''

    def save_to_db(self, jobs):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for job in jobs:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO jobs 
                        (title, company, location, description, url, source, date_added, 
                         posted_date, job_type, salary, requirements, remote)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job['title'],
                        job['company'],
                        job['location'],
                        job.get('description', ''),
                        job['url'],
                        job['source'],
                        datetime.now().isoformat(),
                        job.get('posted_date', ''),
                        job.get('job_type', ''),
                        job.get('salary', ''),
                        job.get('requirements', ''),
                        job.get('remote', False)
                    ))
                except sqlite3.Error as e:
                    print(f"Database error: {e}")
            conn.commit()

    def scrape_custom_url(self, url):
        jobs = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Get page content and parse
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all job cards
                job_cards = soup.select('.jl')
                
                for card in job_cards:
                    job_data = self._extract_job_data(card, {
                        'title': '.jobLink',
                        'company': '.jobEmpolyerName',
                        'location': '.loc',
                        'description': '.jobDesc',
                        'posted_date': '.jobLabels .jobLabel',
                        'job_type': '.jobType',
                        'salary': '.salaryEstimate'
                    }, 'Glassdoor', url)
                    if job_data:
                        jobs.append(job_data)
            
            except PlaywrightTimeoutError:
                print(f"Timeout while loading custom URL")
            except Exception as e:
                print(f"Error scraping custom URL: {str(e)}")
            
            page.close()
            browser.close()
        
        return jobs

class JobSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador Avançado de Vagas")
        self.setup_ui()
        self.scraper = JobScraper()

    def setup_ui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Search frame
        search_frame = ttk.LabelFrame(self.main_frame, text="Busca", padding="5")
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Keywords
        ttk.Label(search_frame, text="Palavras-chave:").grid(row=0, column=0, sticky="w")
        self.keywords_entry = ttk.Entry(search_frame, width=40)
        self.keywords_entry.grid(row=0, column=1, padx=5, pady=2)
        self.keywords_entry.insert(0, "analista de segurança")
        
        # Location
        ttk.Label(search_frame, text="Localização:").grid(row=0, column=2, sticky="w")
        self.location_entry = ttk.Entry(search_frame, width=30)
        self.location_entry.grid(row=0, column=3, padx=5, pady=2)
        self.location_entry.insert(0, "São Paulo")
        
        # Custom URL
        ttk.Label(search_frame, text="URL Personalizada:").grid(row=1, column=0, sticky="w")
        self.custom_url_entry = ttk.Entry(search_frame, width=70)
        self.custom_url_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=2)
        
        # Options frame
        options_frame = ttk.Frame(search_frame)
        options_frame.grid(row=2, column=0, columnspan=4, pady=5)
        
        # Source checkboxes
        self.sources = {
            'LinkedIn': tk.BooleanVar(value=True),
            'Indeed': tk.BooleanVar(value=True),
            'Glassdoor': tk.BooleanVar(value=True)
        }
        
        for i, (source, var) in enumerate(self.sources.items()):
            ttk.Checkbutton(options_frame, text=source, variable=var).grid(row=0, column=i, padx=5)
        
        # Remote only checkbox
        self.remote_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Apenas Remoto", variable=self.remote_only).grid(row=0, column=len(self.sources), padx=5)
        
        # Search button and progress
        self.search_button = ttk.Button(search_frame, text="Buscar", command=self.start_search)
        self.search_button.grid(row=3, column=3, pady=5)
        
        self.progress = ttk.Progressbar(search_frame, mode='indeterminate', length=300)
        self.progress.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)
        
        # Results tree
        self.create_results_tree()
        
        # Status
        self.status_var = tk.StringVar()
        ttk.Label(self.main_frame, textvariable=self.status_var).grid(row=2, column=0)
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def create_results_tree(self):
        columns = ('título', 'empresa', 'local', 'tipo', 'salário', 'fonte', 'remoto')
        self.tree = ttk.Treeview(self.main_frame, columns=columns, show='headings', height=15)
        
        # Headings
        for col in columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=120)
        
        # Scrollbars
        ysb = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        
        # Grid
        self.tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        ysb.grid(row=1, column=1, sticky="ns")
        xsb.grid(row=2, column=0, sticky="ew")
        
        # Bind events
        self.tree.bind('<Double-1>', self.open_job_url)
        self.tree.bind('<Button-3>', self.show_job_details)

    def start_search(self):
        keywords = self.keywords_entry.get()
        location = self.location_entry.get()
        custom_url = self.custom_url_entry.get()
        
        if not keywords and not custom_url:
            messagebox.showwarning("Aviso", "Digite palavras-chave ou uma URL personalizada para buscar")
            return
        
        self.search_button.state(['disabled'])
        self.progress.start()
        self.tree.delete(*self.tree.get_children())
        self.status_var.set("Iniciando busca...")
        
        threading.Thread(target=self.search_jobs, args=(keywords, location, custom_url), daemon=True).start()

    def search_jobs(self, keywords, location, custom_url):
        try:
            # Get selected sources
            selected_sources = {name: var.get() for name, var in self.sources.items()}
            
            # Filter job sites based on selection
            self.scraper.job_sites = {k: v for k, v in self.scraper.job_sites.items() if selected_sources.get(k, False)}
            
            all_jobs = []
            if custom_url:
                # Scrape custom URL
                all_jobs.extend(self.scraper.scrape_custom_url(custom_url))
            else:
                # Scrape jobs
                all_jobs.extend(self.scraper.scrape_jobs(keywords, location))
            
            # Filter remote jobs if needed
            if self.remote_only.get():
                all_jobs = [job for job in all_jobs if job.get('remote', False)]
            
            # Save and display results
            self.scraper.save_to_db(all_jobs)
            self.root.after(0, lambda: self.display_results(all_jobs))
            
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Erro na busca: {str(e)}"))
        finally:
            self.root.after(0, self.cleanup)

    def display_results(self, jobs):
        self.tree.delete(*self.tree.get_children())
        for job in jobs:
            self.tree.insert('', 'end', values=(
                job['title'],
                job['company'],
                job['location'],
                job.get('job_type', 'Não especificado'),
                job.get('salary', 'Não especificado'),
                job['source'],
                'Sim' if job.get('remote', False) else 'Não'
            ), tags=(job['url'],))
        
        self.status_var.set(f"Encontradas {len(jobs)} vagas")

    def open_job_url(self, event):
        item = self.tree.selection()[0]
        url = self.tree.item(item)['tags'][0]
        webbrowser.open(url)

    def show_job_details(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            job_info = self.tree.item(item)
            details_window = tk.Toplevel(self.root)
            details_window.title("Detalhes da Vaga")
            details_window.geometry("600x500")
            
            # Create a frame with scrollbar
            frame = ttk.Frame(details_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Add text widget with scrollbar
            text = tk.Text(frame, wrap=tk.WORD, padx=10, pady=10)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
            text.configure(yscrollcommand=scrollbar.set)
            
            # Pack widgets
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Get values
            values = job_info['values']
            details = f"""
Título: {values[0]}
Empresa: {values[1]}
Local: {values[2]}
Tipo de Trabalho: {values[3]}
Salário: {values[4]}
Fonte: {values[5]}
Remoto: {values[6]}
URL: {job_info['tags'][0]}

Requisitos encontrados:
{self._get_job_requirements(job_info['tags'][0])}
"""
            text.insert('1.0', details)
            text.config(state='disabled')

    def _get_job_requirements(self, url):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT requirements, description FROM jobs WHERE url = ?', (url,))
            result = cursor.fetchone()
            if result:
                requirements, description = result
                if requirements:
                    return requirements
                elif description:
                    return "Descrição completa:\n" + description
            return "Requisitos não encontrados"

    def show_error(self, message):
        self.status_var.set(message)
        messagebox.showerror("Erro", message)

    def cleanup(self):
        self.search_button.state(['!disabled'])
        self.progress.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = JobSearchApp(root)
    root.mainloop()