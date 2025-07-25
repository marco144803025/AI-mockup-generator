from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class TemplateCreate(BaseModel):
    name: str
    figma_url: str
    html_export: Optional[str] = None
    globals_css: Optional[str] = None
    style_css: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Optional[Dict] = None
    tags: Optional[List[str]] = None

class TemplateRead(TemplateCreate):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 