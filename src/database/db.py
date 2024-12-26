import logging
import sqlite3
from contextlib import contextmanager
from typing import List

from ..config import settings
from ..models.job import Job

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.db_url = settings.DATABASE_URL.replace("sqlite:///", "")
        self._create_tables()

    def _create_tables(self):
        """Criar tabelas necessárias no banco de dados"""
        with self.get_connection() as conn:
            conn.execute(
                """
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
                    search_id TEXT,
                    version TEXT,
                    UNIQUE(url, source)
                )
            """
            )

    @contextmanager
    def get_connection(self):
        """Context manager para conexão com o banco de dados"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_url)
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def save_jobs(self, jobs: List[Job], search_id: str, version: str):
        """Salvar lista de empregos no banco de dados"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for job in jobs:
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO jobs 
                        (title, company, location, description, url, source, 
                         date_added, posted_date, job_type, salary, requirements, 
                         remote, search_id, version)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            job.title,
                            job.company,
                            job.location,
                            job.description,
                            job.url,
                            job.source,
                            job.date_added.isoformat(),
                            job.posted_date,
                            job.job_type,
                            job.salary,
                            job.requirements,
                            job.remote,
                            search_id,
                            version,
                        ),
                    )
                except sqlite3.Error as e:
                    logger.error(f"Error saving job {job.title}: {str(e)}")

    def get_jobs(self, search_id: str) -> List[dict]:
        """Recuperar empregos por ID de busca"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE search_id = ?", (search_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
