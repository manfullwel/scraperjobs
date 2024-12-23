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

class JobSearcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def search_indeed(self, query, location):
        jobs = []
        try:
            url = f"https://www.indeed.com/jobs?q={query}&l={location}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards[:5]:  # Limit to 5 results
                title = card.find('h2', class_='jobTitle')
                company = card.find('span', class_='companyName')
                location = card.find('div', class_='companyLocation')
                
                if title and company and location:
                    jobs.append({
                        'title': title.get_text().strip(),
                        'company': company.get_text().strip(),
                        'location': location.get_text().strip(),
                        'url': 'https://www.indeed.com' + card.find('a')['href'] if card.find('a') else '',
                        'source': 'Indeed'
                    })
        except Exception as e:
            print(f"Error searching Indeed: {e}")
        return jobs

    def search_linkedin(self, query, location):
        jobs = []
        try:
            url = f"https://www.linkedin.com/jobs/search?keywords={query}&location={location}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_cards = soup.find_all('div', class_='base-card')
            
            for card in job_cards[:5]:
                title = card.find('h3', class_='base-search-card__title')
                company = card.find('h4', class_='base-search-card__subtitle')
                location = card.find('span', class_='job-search-card__location')
                
                if title and company and location:
                    jobs.append({
                        'title': title.get_text().strip(),
                        'company': company.get_text().strip(),
                        'location': location.get_text().strip(),
                        'url': card.find('a')['href'] if card.find('a') else '',
                        'source': 'LinkedIn'
                    })
        except Exception as e:
            print(f"Error searching LinkedIn: {e}")
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
        self.search_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.search_frame, text="Keywords:").grid(row=0, column=0, sticky=tk.W)
        self.keywords_entry = ttk.Entry(self.search_frame, width=30)
        self.keywords_entry.grid(row=0, column=1, padx=5)
        self.keywords_entry.insert(0, "penetration tester")
        
        ttk.Label(self.search_frame, text="Location:").grid(row=0, column=2, sticky=tk.W)
        self.location_search_entry = ttk.Entry(self.search_frame, width=30)
        self.location_search_entry.grid(row=0, column=3, padx=5)
        
        self.search_button = ttk.Button(self.search_frame, text="Search Jobs", command=self.search_jobs)
        self.search_button.grid(row=0, column=4, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.search_frame, length=200, mode='determinate', variable=self.progress_var)
        self.progress.grid(row=1, column=0, columnspan=5, pady=5, sticky=(tk.W, tk.E))
        
        # Job Entry Fields
        ttk.Label(self.main_frame, text="Company:").grid(row=2, column=0, sticky=tk.W)
        self.company_entry = ttk.Entry(self.main_frame, width=40)
        self.company_entry.grid(row=2, column=1, columnspan=2, pady=5)
        
        ttk.Label(self.main_frame, text="Position:").grid(row=3, column=0, sticky=tk.W)
        self.position_entry = ttk.Entry(self.main_frame, width=40)
        self.position_entry.grid(row=3, column=1, columnspan=2, pady=5)
        
        ttk.Label(self.main_frame, text="Location:").grid(row=4, column=0, sticky=tk.W)
        self.location_entry = ttk.Entry(self.main_frame, width=40)
        self.location_entry.grid(row=4, column=1, columnspan=2, pady=5)
        
        ttk.Label(self.main_frame, text="Required Skills:").grid(row=5, column=0, sticky=tk.W)
        self.skills_text = tk.Text(self.main_frame, width=40, height=4)
        self.skills_text.grid(row=5, column=1, columnspan=2, pady=5)
        
        ttk.Label(self.main_frame, text="Job URL:").grid(row=6, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(self.main_frame, width=40)
        self.url_entry.grid(row=6, column=1, columnspan=2, pady=5)
        
        # Buttons
        ttk.Button(self.main_frame, text="Add Job", command=self.add_job).grid(row=7, column=1, pady=10)
        ttk.Button(self.main_frame, text="View All Jobs", command=self.view_jobs).grid(row=7, column=2, pady=10)
        
        # Results area
        self.results_text = tk.Text(self.main_frame, width=60, height=10)
        self.results_text.grid(row=8, column=0, columnspan=3, pady=10)

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY,
                company TEXT,
                position TEXT,
                location TEXT,
                skills TEXT,
                url TEXT,
                date_added TEXT
            )
        ''')
        self.conn.commit()

    def search_jobs(self):
        keywords = self.keywords_entry.get()
        location = self.location_search_entry.get()
        
        self.progress_var.set(0)
        self.search_button.config(state='disabled')
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Searching for jobs...\n")
        
        def search_thread():
            all_jobs = []
            
            # Search Indeed
            self.progress_var.set(33)
            indeed_jobs = self.job_searcher.search_indeed(keywords, location)
            all_jobs.extend(indeed_jobs)
            
            # Search LinkedIn
            self.progress_var.set(66)
            linkedin_jobs = self.job_searcher.search_linkedin(keywords, location)
            all_jobs.extend(linkedin_jobs)
            
            self.progress_var.set(100)
            
            # Update UI in main thread
            self.root.after(0, lambda: self.display_search_results(all_jobs))
        
        threading.Thread(target=search_thread, daemon=True).start()

    def display_search_results(self, jobs):
        self.results_text.delete("1.0", tk.END)
        if not jobs:
            self.results_text.insert(tk.END, "No jobs found. Try different keywords or location.\n")
        else:
            for job in jobs:
                job_info = f"""
Source: {job['source']}
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
URL: {job['url']}
------------------------
"""
                self.results_text.insert(tk.END, job_info)
        
        self.search_button.config(state='normal')

    def add_job(self):
        company = self.company_entry.get()
        position = self.position_entry.get()
        location = self.location_entry.get()
        skills = self.skills_text.get("1.0", tk.END).strip()
        url = self.url_entry.get()
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO jobs (company, position, location, skills, url, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (company, position, location, skills, url, date_added))
        self.conn.commit()
        
        self.clear_entries()
        self.view_jobs()
    
    def view_jobs(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM jobs')
        jobs = cursor.fetchall()
        
        self.results_text.delete("1.0", tk.END)
        for job in jobs:
            job_info = f"""
Company: {job[1]}
Position: {job[2]}
Location: {job[3]}
Required Skills: {job[4]}
URL: {job[5]}
Date Added: {job[6]}
------------------------
"""
            self.results_text.insert(tk.END, job_info)
    
    def clear_entries(self):
        self.company_entry.delete(0, tk.END)
        self.position_entry.delete(0, tk.END)
        self.location_entry.delete(0, tk.END)
        self.skills_text.delete("1.0", tk.END)
        self.url_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = PenTestingJobTracker(root)
    root.mainloop()