from dataclasses import dataclass
from typing import Protocol


@dataclass
class IngestedItem:
    source_id: str
    title: str
    summary: str
    location_name: str | None


@dataclass
class EnrichmentResult:
    tags: list[str]
    why_tagged: dict[str, str]
    latitude: float | None
    longitude: float | None
    weather_context: dict
    weather_coverage_notes: str
    breaking: bool


@dataclass
class GeneratedDraft:
    headline_options: list[str]
    cover_spec: dict
    caption_short: str
    caption_long: str
    carousel_outline: list[dict]


class Ingestor(Protocol):
    def fetch_items(self) -> list[IngestedItem]: ...


class Enricher(Protocol):
    def enrich(self, item: IngestedItem) -> EnrichmentResult: ...


class Generator(Protocol):
    name: str

    def generate(self, item: IngestedItem, enrichment: EnrichmentResult) -> GeneratedDraft: ...
