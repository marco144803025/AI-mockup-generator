from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from bson import ObjectId

class Template(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    figma_url: str
    html_export: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict] = None
    tags: Optional[List[str]] = None
    globals_css: Optional[str] = None
    style_css: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True 