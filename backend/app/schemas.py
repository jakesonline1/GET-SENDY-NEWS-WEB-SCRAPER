from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from .models import ContentPackStatus, Role


class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Role = Role.REVIEWER


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: Role

    class Config:
        from_attributes = True


class CreativeDraftOut(BaseModel):
    id: int
    generator_name: str
    headline_options: Any
    cover_spec: Any
    caption_short: str
    caption_long: str
    carousel_outline: Any

    class Config:
        from_attributes = True


class AttributionOut(BaseModel):
    required_credit_line: str
    notes: str
    safe_to_repost: str

    class Config:
        from_attributes = True


class AssetOut(BaseModel):
    url: str
    type: str
    provider: str
    creator_handle: str | None
    local_storage_path: str | None
    rights_status: str

    class Config:
        from_attributes = True


class ContentPackOut(BaseModel):
    id: int
    source_id: str
    title: str
    summary: str
    bullets: Any
    tags: Any
    why_tagged: Any
    location_name: str | None
    latitude: float | None
    longitude: float | None
    weather_context: Any
    weather_coverage_notes: str
    breaking: bool
    distance_km: float | None
    status: ContentPackStatus
    reviewer_notes: str
    created_at: datetime
    drafts: list[CreativeDraftOut] = []
    assets: list[AssetOut] = []
    attribution: AttributionOut | None = None


class ContentPackUpdate(BaseModel):
    summary: str | None = None
    bullets: list[str] | None = None
    tags: list[str] | None = None
    reviewer_notes: str | None = None
    status: ContentPackStatus | None = None


class RejectIn(BaseModel):
    reviewer_notes: str = Field(min_length=3)
