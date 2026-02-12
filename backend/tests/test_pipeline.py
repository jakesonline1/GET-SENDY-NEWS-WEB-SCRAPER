import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import ContentPack, ContentPackStatus
from app.plugins.defaults import BasicSocialGenerator
from app.plugins.interfaces import EnrichmentResult, IngestedItem
from app.services.pipeline import dedupe_by_source, set_status


def test_dedupe_by_source():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(ContentPack(source_id='abc', title='t', summary='s', status=ContentPackStatus.NEW))
    db.commit()

    assert dedupe_by_source(db, IngestedItem(source_id='abc', title='x', summary='y', location_name=None)) is True
    assert dedupe_by_source(db, IngestedItem(source_id='def', title='x', summary='y', location_name=None)) is False


def test_status_transitions():
    pack = ContentPack(source_id='x', title='t', summary='s', status=ContentPackStatus.NEW)
    set_status(pack, ContentPackStatus.ENRICHED)
    set_status(pack, ContentPackStatus.DRAFT_READY)
    set_status(pack, ContentPackStatus.IN_REVIEW)
    set_status(pack, ContentPackStatus.APPROVED)

    assert pack.status == ContentPackStatus.APPROVED


def test_generator_output_validation():
    generator = BasicSocialGenerator()
    item = IngestedItem(source_id='a', title='Sample Story', summary='summary', location_name='Nairobi')
    enrichment = EnrichmentResult(
        tags=['sport', 'location'],
        why_tagged={'sport': 'x'},
        latitude=-1.2,
        longitude=36.8,
        weather_context={'forecast_summary': 'Sunny'},
        weather_coverage_notes='Best-effort',
        breaking=False,
    )

    draft = generator.generate(item, enrichment)
    assert len(draft.headline_options) == 5
    assert len(draft.carousel_outline) == 5
    assert isinstance(draft.cover_spec, dict)
    assert draft.caption_short
    assert draft.caption_long

    json.dumps(draft.headline_options)
    json.dumps(draft.cover_spec)
    json.dumps(draft.carousel_outline)
