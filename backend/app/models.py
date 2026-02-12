from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Role(str, Enum):
    ADMIN = 'admin'
    REVIEWER = 'reviewer'


class ContentPackStatus(str, Enum):
    NEW = 'NEW'
    ENRICHED = 'ENRICHED'
    DRAFT_READY = 'DRAFT_READY'
    IN_REVIEW = 'IN_REVIEW'
    APPROVED = 'APPROVED'
    ARCHIVED = 'ARCHIVED'
    ASSETS_PENDING = 'ASSETS_PENDING'
    SCHEDULED = 'SCHEDULED'
    POSTED = 'POSTED'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(SQLEnum(Role), default=Role.REVIEWER)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ContentPack(Base):
    __tablename__ = 'content_packs'

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text, default='')
    bullets: Mapped[str] = mapped_column(Text, default='[]')
    tags: Mapped[str] = mapped_column(Text, default='[]')
    why_tagged: Mapped[str] = mapped_column(Text, default='{}')
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_context: Mapped[str] = mapped_column(Text, default='{}')
    weather_coverage_notes: Mapped[str] = mapped_column(Text, default='')
    breaking: Mapped[bool] = mapped_column(Boolean, default=False)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[ContentPackStatus] = mapped_column(SQLEnum(ContentPackStatus), default=ContentPackStatus.NEW, index=True)
    reviewer_notes: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    drafts: Mapped[list['CreativeDraft']] = relationship(back_populates='content_pack', cascade='all, delete-orphan')
    assets: Mapped[list['Asset']] = relationship(back_populates='content_pack', cascade='all, delete-orphan')
    attribution: Mapped['Attribution | None'] = relationship(back_populates='content_pack', uselist=False, cascade='all, delete-orphan')


class CreativeDraft(Base):
    __tablename__ = 'creative_drafts'

    id: Mapped[int] = mapped_column(primary_key=True)
    content_pack_id: Mapped[int] = mapped_column(ForeignKey('content_packs.id'), index=True)
    generator_name: Mapped[str] = mapped_column(String(255))
    headline_options: Mapped[str] = mapped_column(Text)
    cover_spec: Mapped[str] = mapped_column(Text)
    caption_short: Mapped[str] = mapped_column(Text)
    caption_long: Mapped[str] = mapped_column(Text)
    carousel_outline: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    content_pack: Mapped[ContentPack] = relationship(back_populates='drafts')


class AssetType(str, Enum):
    VIDEO = 'video'
    IMAGE = 'image'


class Asset(Base):
    __tablename__ = 'assets'

    id: Mapped[int] = mapped_column(primary_key=True)
    content_pack_id: Mapped[int] = mapped_column(ForeignKey('content_packs.id'), index=True)
    url: Mapped[str] = mapped_column(Text)
    type: Mapped[AssetType] = mapped_column(SQLEnum(AssetType))
    provider: Mapped[str] = mapped_column(String(255))
    creator_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    local_storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    rights_status: Mapped[str] = mapped_column(String(100), default='manual')

    content_pack: Mapped[ContentPack] = relationship(back_populates='assets')


class Attribution(Base):
    __tablename__ = 'attribution'

    id: Mapped[int] = mapped_column(primary_key=True)
    content_pack_id: Mapped[int] = mapped_column(ForeignKey('content_packs.id'), unique=True, index=True)
    required_credit_line: Mapped[str] = mapped_column(Text, default='')
    notes: Mapped[str] = mapped_column(Text, default='')
    safe_to_repost: Mapped[str] = mapped_column(String(20), default='unknown')

    content_pack: Mapped[ContentPack] = relationship(back_populates='attribution')
