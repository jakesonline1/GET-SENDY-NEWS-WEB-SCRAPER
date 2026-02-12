import json

from sqlalchemy.orm import Session

from ..models import Attribution, ContentPack, ContentPackStatus, CreativeDraft
from ..plugins.defaults import BasicSocialGenerator, GlobalContextEnricher, MockRSSIngestor
from ..plugins.interfaces import Enricher, Generator, IngestedItem, Ingestor

ALLOWED_TRANSITIONS = {
    ContentPackStatus.NEW: {ContentPackStatus.ENRICHED},
    ContentPackStatus.ENRICHED: {ContentPackStatus.DRAFT_READY},
    ContentPackStatus.DRAFT_READY: {ContentPackStatus.IN_REVIEW},
    ContentPackStatus.IN_REVIEW: {ContentPackStatus.APPROVED},
    ContentPackStatus.APPROVED: {ContentPackStatus.ARCHIVED, ContentPackStatus.ASSETS_PENDING, ContentPackStatus.SCHEDULED},
    ContentPackStatus.ASSETS_PENDING: {ContentPackStatus.SCHEDULED},
    ContentPackStatus.SCHEDULED: {ContentPackStatus.POSTED},
    ContentPackStatus.POSTED: {ContentPackStatus.ARCHIVED},
}


def set_status(pack: ContentPack, target: ContentPackStatus):
    if pack.status == target:
        return
    allowed = ALLOWED_TRANSITIONS.get(pack.status, set())
    if target not in allowed:
        raise ValueError(f'Invalid status transition: {pack.status} -> {target}')
    pack.status = target


def dedupe_by_source(db: Session, item: IngestedItem) -> bool:
    return db.query(ContentPack).filter(ContentPack.source_id == item.source_id).first() is not None


def run_ingestion(db: Session, ingestor: Ingestor | None = None):
    ingestor = ingestor or MockRSSIngestor()
    created = 0
    for item in ingestor.fetch_items():
        if dedupe_by_source(db, item):
            continue
        db.add(
            ContentPack(source_id=item.source_id, title=item.title, summary=item.summary, location_name=item.location_name)
        )
        created += 1
    db.commit()
    return created


def run_enrichment_and_generation(db: Session, enricher: Enricher | None = None, generator: Generator | None = None):
    enricher = enricher or GlobalContextEnricher()
    generator = generator or BasicSocialGenerator()

    packs = db.query(ContentPack).filter(ContentPack.status.in_([ContentPackStatus.NEW, ContentPackStatus.ENRICHED])).all()
    for pack in packs:
        item = IngestedItem(pack.source_id, pack.title, pack.summary, pack.location_name)
        enrichment = enricher.enrich(item)

        pack.tags = json.dumps(enrichment.tags)
        pack.why_tagged = json.dumps(enrichment.why_tagged)
        pack.latitude = enrichment.latitude
        pack.longitude = enrichment.longitude
        pack.weather_context = json.dumps(enrichment.weather_context)
        pack.weather_coverage_notes = enrichment.weather_coverage_notes
        pack.breaking = enrichment.breaking

        if pack.status == ContentPackStatus.NEW:
            set_status(pack, ContentPackStatus.ENRICHED)

        draft = generator.generate(item, enrichment)
        db.add(
            CreativeDraft(
                content_pack=pack,
                generator_name=generator.name,
                headline_options=json.dumps(draft.headline_options),
                cover_spec=json.dumps(draft.cover_spec),
                caption_short=draft.caption_short,
                caption_long=draft.caption_long,
                carousel_outline=json.dumps(draft.carousel_outline),
            )
        )
        if not pack.attribution:
            db.add(Attribution(content_pack=pack, required_credit_line='TBD by reviewer', notes='Verify source rights.', safe_to_repost='unknown'))

        set_status(pack, ContentPackStatus.DRAFT_READY)

    db.commit()
