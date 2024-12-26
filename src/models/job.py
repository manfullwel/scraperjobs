from datetime import datetime
import uuid
from typing import List, Optional, Union, Dict

from pydantic import BaseModel, Field


class Job(BaseModel):
    """Modelo de vaga de emprego"""
    title: str
    company: str
    location: str
    description: Optional[str] = None
    url: str
    source: str
    remote: bool = False
    salary: Optional[Union[float, str]] = None
    posted_date: Optional[str] = None
    job_type: Optional[str] = None
    requirements: Optional[str] = None
    date_added: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class JobSearch(BaseModel):
    """Modelo de busca de vagas"""
    keywords: str
    location: str
    sources: List[str] = ["adzuna", "linkedin"]
    remote_only: bool = False
    custom_url: Optional[str] = None
    scraper_version: str = "v1"
    search_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class JobSearchResponse(BaseModel):
    """Modelo de resposta da busca"""
    jobs: List[Job]
    total: int
    search_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    app_version: str
    execution_time: float
    api_usage: Optional[Dict] = None
