from celery import Celery

from .config import settings
from .database import SessionLocal
from .services.pipeline import run_enrichment_and_generation, run_ingestion

celery = Celery('worker', broker=settings.redis_url, backend=settings.redis_url)
celery.conf.beat_schedule = {
    'ingest-every-5-min': {
        'task': 'app.celery_app.ingest_and_generate',
        'schedule': 300.0,
    }
}


@celery.task(name='app.celery_app.ingest_and_generate')
def ingest_and_generate():
    db = SessionLocal()
    try:
        run_ingestion(db)
        run_enrichment_and_generation(db)
    finally:
        db.close()
