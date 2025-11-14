"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogpost" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

class Project(BaseModel):
    """Projects collection schema (collection name: "project")"""
    title: str = Field(..., description="Project title")
    slug: str = Field(..., description="URL friendly unique slug")
    summary: str = Field(..., description="Short TL;DR summary")
    description: Optional[str] = Field(None, description="Longer description / case study")
    tech: List[str] = Field(default_factory=list, description="Technologies used")
    role: Optional[str] = Field(None, description="Role in the project")
    timeline: Optional[str] = Field(None, description="Timeline string e.g. 2023 Q1-Q3")
    logo_url: Optional[HttpUrl] = Field(None, description="Logo or hero image URL")
    demo_url: Optional[HttpUrl] = Field(None, description="Live demo URL")
    repo_url: Optional[HttpUrl] = Field(None, description="Repository URL")
    tags: List[str] = Field(default_factory=list)
    featured: bool = Field(default=False)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BlogPost(BaseModel):
    """Blog posts collection schema (collection name: "blogpost")"""
    title: str
    slug: str
    excerpt: str
    content: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    read_time: int = Field(3, ge=1, description="Estimated read time in minutes")
    cover_url: Optional[HttpUrl] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TechItem(BaseModel):
    """Tech stack items (collection name: "techitem")"""
    name: str
    category: Optional[str] = None
    level: Optional[str] = Field(None, description="Proficiency level or years")
    icon: Optional[str] = Field(None, description="Icon name or URL")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
