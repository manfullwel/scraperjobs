import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import webbrowser
import requests
from bs4 import BeautifulSoup
import json
import threading
import re
from urllib.parse import quote, urlencode
import time
import random

class JobSearcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers',
            'DNT': '1'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.common_pentesting_skills = [
            "penetration testing", "ethical hacking", "vulnerability assessment",
            "kali linux", "metasploit", "burp suite", "wireshark", "nmap",
            "python", "bash scripting", "network security", "web application security",
            "OWASP", "security assessment", "red teaming", "social engineering",
            "incident response", "malware analysis", "reverse engineering",
            "CISSP", "CEH", "OSCP", "security+", "network+",
            "risk assessment", "security auditing", "compliance"
        ]
        
        self.level_keywords = {
            'entry': ['entry level', 'junior', 'associate', '0-2 years', 'entry-level', 'graduate'],
            'mid': ['mid level', 'intermediate', '2-5 years', '3-5 years', 'mid-level'],
            'senior': ['senior', 'lead', '5+ years', '6+ years', 'principal', 'architect']
        }

    def detect_level(self, text):
        text_lower = text.lower()
        for level, keywords in self.level_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return level.capitalize()
        return "Not Specified"

    def extract_skills_from_text(self, text):
        found_skills = []
        text_lower = text.lower()
        for skill in self.common_pentesting_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills

    def search_linkedin(self, query, location):
        jobs = []
        try:
            # Using LinkedIn's API-like endpoint
            params = {
                'keywords': query,
                'location': location,
                'f_TPR': 'r86400',  # Last 24 hours
                'position': 1,
                'pageNum': 0,
                'start': 0
            }
            
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{urlencode(params)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_cards = soup.find_all('div', class_='base-card')[:10]
            
            for card in job_cards:
                try:
                    title_elem = card.find('h3', class_='base-search-card__title')
                    company_elem = card.find('h4', class_='base-search-card__subtitle')
                    location_elem = card.find('span', class_='job-search-card__location')
                    link_elem = card.find('a', class_='base-card__full-link')
                    
                    if all([title_elem, company_elem, location_elem, link_elem]):
                        job_url = link_elem['href'].split('?')[0]
                        
                        # Get detailed job info
                        time.sleep(random.uniform(1, 2))  # Random delay to avoid rate limiting
                        job_response = self.session.get(job_url)
                        job_soup = BeautifulSoup(job_response.text, 'html.parser')
                        
                        description = job_soup.find('div', class_='description__text')
                        description_text = description.get_text() if description else ""
                        
                        level = self.detect_level(description_text)
                        skills = self.extract_skills_from_text(description_text)
                        
                        jobs.append({
                            'title': title_elem.get_text().strip(),
                            'company': company_elem.get_text().strip(),
                            'location': location_elem.get_text().strip(),
                            'url': job_url,
                            'skills': ', '.join(skills) if skills else 'No specific skills listed',
                            'level': level,
                            'source': 'LinkedIn'
                        })
                except Exception as e:
                    print(f"Error processing LinkedIn job: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error searching LinkedIn: {e}")
        return jobs

    def search_indeed(self, query, location):
        jobs = []
        try:
            # Using Indeed's mobile API endpoint for better results
            params = {
                'q': query,
                'l': location,
                'filter': '0',
                'sort': 'date',
                'limit': '10'
            }
            
            url = f"https://www.indeed.com/m/jobs?{urlencode(params)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_cards = soup.find_all('div', class_='job_seen_beacon')[:10]
            
            for card in job_cards:
                try:
                    title = card.find(['h2', 'h3'], class_=['jobTitle', 'title'])
                    company = card.find(['span', 'div'], class_=['company', 'companyName'])
                    location = card.find(['div', 'span'], class_=['companyLocation', 'location'])
                    
                    if all([title, company, location]):
                        job_link = card.find('a', href=True)
                        job_url = 'https://www.indeed.com' + job_link['href'] if job_link else ''
                        
                        # Get detailed job info
                        time.sleep(random.uniform(1, 2))
                        if job_url:
                            job_response = self.session.get(job_url)
                            job_soup = BeautifulSoup(job_response.text, 'html.parser')
                            description = job_soup.find('div', class_='jobsearch-jobDescriptionText')
                            description_text = description.get_text() if description else ""
                            
                            level = self.detect_level(description_text)
                            skills = self.extract_skills_from_text(description_text)
                            
                            jobs.append({
                                'title': title.get_text().strip(),
                                'company': company.get_text().strip(),
                                'location': location.get_text().strip(),
                                'url': job_url,
                                'skills': ', '.join(skills) if skills else 'No specific skills listed',
                                'level': level,
                                'source': 'Indeed'
                            })
                except Exception as e:
                    print(f"Error processing Indeed job: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error searching Indeed: {e}")
        return jobs

    def search_monster(self, query, location):
        jobs = []
        try:
            # Using Monster's search API
            params = {
                'q': query,
                'where': location,
                'page': '1'
            }
            
            url = f"https://www.monster.com/jobs/search?{urlencode(params)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Monster's new layout uses React/JavaScript, so we'll parse their job cards
            job_cards = soup.find_all('section', class_='card-content')[:10]
            
            for card in job_cards:
                try:
                    title = card.find(['h2', 'h3'], class_='title')
                    company = card.find(['div', 'span'], class_='company')
                    location = card.find(['div', 'span'], class_='location')
                    
                    if all([title, company, location]):
                        job_link = card.find('a', href=True)
                        job_url = job_link['href'] if job_link else ''
                        
                        # Get detailed job info
                        time.sleep(random.uniform(1, 2))
                        if job_url:
                            job_response = self.session.get(job_url)
                            job_soup = BeautifulSoup(job_response.text, 'html.parser')
                            description = job_soup.find('div', class_='job-description')
                            description_text = description.get_text() if description else ""
                            
                            level = self.detect_level(description_text)
                            skills = self.extract_skills_from_text(description_text)
                            
                            jobs.append({
                                'title': title.get_text().strip(),
                                'company': company.get_text().strip(),
                                'location': location.get_text().strip(),
                                'url': job_url,
                                'skills': ', '.join(skills) if skills else 'No specific skills listed',
                                'level': level,
                                'source': 'Monster'
                            })
                except Exception as e:
                    print(f"Error processing Monster job: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error searching Monster: {e}")
        return jobs

class PenTestingJobTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Penetration Testing Career Tracker")
        self.job_searcher = JobSearcher()
        
        # Create database
        self.conn = sqlite3.connect('pentesting_jobs.db')
        self.create_table()
        
        # Main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Search Frame
        self.search_frame = ttk.LabelFrame(self.main_frame, text="Job Search", padding="5")
        self.search_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Job Source Selection
        ttk.Label(self.search_frame, text="Job Sources:").grid(row=0, column=0, sticky=tk.W)
        self.sources_frame = ttk.Frame(self.search_frame)
        self.sources_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        
        self.source_vars = {
            'LinkedIn': tk.BooleanVar(value=True),
            'Indeed': tk.BooleanVar(value=False),
            'Monster': tk.BooleanVar(value=False)
        }
        
        for i, (source, var) in enumerate(self.source_vars.items()):
            ttk.Checkbutton(self.sources_frame, text=source, variable=var).grid(row=0, column=i, padx=5)
        
        # Search Fields
        ttk.Label(self.search_frame, text="Keywords:").grid(row=1, column=0, sticky=tk.W)
        self.keywords_entry = ttk.Entry(self.search_frame, width=30)
        self.keywords_entry.grid(row=1, column=1, padx=5)
        self.keywords_entry.insert(0, "penetration tester")
        
        ttk.Label(self.search_frame, text="Location:").grid(row=1, column=2, sticky=tk.W)
        self.location_search_entry = ttk.Entry(self.search_frame, width=30)
        self.location_search_entry.grid(row=1, column=3, padx=5)
        
        # Level Filter
        ttk.Label(self.search_frame, text="Level:").grid(row=2, column=0, sticky=tk.W)
        self.level_var = tk.StringVar(value="Any")
        level_choices = ["Any", "Entry", "Mid", "Senior"]
        self.level_combobox = ttk.Combobox(self.search_frame, textvariable=self.level_var, values=level_choices, state="readonly")
        self.level_combobox.grid(row=2, column=1, padx=5, sticky=tk.W)
        
        # Status Label
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self.search_frame, textvariable=self.status_var)
        self.status_label.grid(row=2, column=2, columnspan=2, sticky=tk.W)
        
        self.search_button = ttk.Button(self.search_frame, text="Search Jobs", command=self.search_jobs)
        self.search_button.grid(row=3, column=3, padx=5, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.search_frame, length=200, mode='determinate', variable=self.progress_var)
        self.progress.grid(row=4, column=0, columnspan=4, pady=5, sticky=(tk.W, tk.E))
        
        # Results area
        self.results_text = tk.Text(self.main_frame, width=80, height=20)
        self.results_text.grid(row=1, column=0, columnspan=4, pady=10)
        
        # Add scrollbar to results
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.results_text.yview)
        scrollbar.grid(row=1, column=4, sticky="ns")
        self.results_text.configure(yscrollcommand=scrollbar.set)

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                level TEXT,
                skills TEXT,
                url TEXT,
                source TEXT,
                date_added TEXT
            )
        ''')
        self.conn.commit()

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def search_jobs(self):
        keywords = self.keywords_entry.get()
        location = self.location_search_entry.get()
        selected_level = self.level_var.get()
        
        if not keywords or not location:
            messagebox.showwarning("Input Required", "Please enter both keywords and location")
            return
        
        self.progress_var.set(0)
        self.search_button.config(state='disabled')
        self.results_text.delete("1.0", tk.END)
        
        def search_thread():
            all_jobs = []
            active_sources = [source for source, var in self.source_vars.items() if var.get()]
            
            if not active_sources:
                self.root.after(0, lambda: messagebox.showwarning("Source Required", "Please select at least one job source"))
                self.search_button.config(state='normal')
                return
            
            progress_step = 100 / len(active_sources)
            current_progress = 0
            
            for source in active_sources:
                self.update_status(f"Searching {source}...")
                
                if source == 'LinkedIn':
                    jobs = self.job_searcher.search_linkedin(keywords, location)
                elif source == 'Indeed':
                    jobs = self.job_searcher.search_indeed(keywords, location)
                elif source == 'Monster':
                    jobs = self.job_searcher.search_monster(keywords, location)
                
                all_jobs.extend(jobs)
                current_progress += progress_step
                self.progress_var.set(current_progress)
            
            # Filter by level if specified
            if selected_level != "Any":
                all_jobs = [job for job in all_jobs if job['level'] == selected_level]
            
            self.progress_var.set(100)
            self.update_status(f"Found {len(all_jobs)} jobs")
            self.root.after(0, lambda: self.display_search_results(all_jobs))
        
        threading.Thread(target=search_thread, daemon=True).start()

    def display_search_results(self, jobs):
        self.results_text.delete("1.0", tk.END)
        if not jobs:
            self.results_text.insert(tk.END, "No jobs found. Try different keywords, location, or job sources.\n")
        else:
            for job in jobs:
                job_info = f"""
Source: {job['source']}
Title: {job['title']}
Company: {job['company']}
Level: {job['level']}
Location: {job['location']}
Required Skills: {job['skills']}
URL: {job['url']}
------------------------
"""
                self.results_text.insert(tk.END, job_info)
        
        self.search_button.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = PenTestingJobTracker(root)
    root.mainloop()