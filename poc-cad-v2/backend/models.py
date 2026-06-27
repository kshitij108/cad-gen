from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    password: str
    company_name: str
    nature_of_business: str
    website: Optional[str] = None
    address: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Job(BaseModel):
    job_type: str
    status: str
    progress: int = 0

class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    cad_specification: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    job_type: str
    created_at: Optional[str] = None

class Project(BaseModel):
    name: str
    description: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str

class PromptRequest(BaseModel):
    prompt: str
    company_name: Optional[str] = None
