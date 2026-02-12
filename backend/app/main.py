import json
import logging
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .auth import create_access_token, hash_password, verify_password
from .database import Base, SessionLocal, engine, get_db
from .models import ContentPack, ContentPackStatus, Role, User
from .schemas import ContentPackOut, ContentPackUpdate, LoginIn, RejectIn, TokenOut, UserCreate, UserOut
from .services.pipeline import run_enrichment_and_generation, run_ingestion, set_status

app = FastAPI(title='Get Sendy Pipeline API')
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def wait_for_db(max_attempts: int = 30, delay_seconds: int = 2) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            time.sleep(delay_seconds)


def ensure_seed_users(db: Session) -> None:
    if not db.query(User).filter(User.email == 'admin@getsendy.dev').first():
        db.add(User(email='admin@getsendy.dev', password_hash=hash_password('password123'), role=Role.ADMIN))
    if not db.query(User).filter(User.email == 'reviewer@getsendy.dev').first():
        db.add(User(email='reviewer@getsendy.dev', password_hash=hash_password('password123'), role=Role.REVIEWER))
    db.commit()


@app.on_event('startup')
def startup():
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_seed_users(db)
    except Exception:
        logger.exception('Failed to seed startup users')
    finally:
        db.close()


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/auth/register', response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email already exists')
    user = User(email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post('/auth/login', response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    return TokenOut(access_token=create_access_token(user.email))


def serialize_pack(pack: ContentPack) -> dict:
    return {
        'id': pack.id,
        'source_id': pack.source_id,
        'title': pack.title,
        'summary': pack.summary,
        'bullets': json.loads(pack.bullets),
        'tags': json.loads(pack.tags),
        'why_tagged': json.loads(pack.why_tagged),
        'location_name': pack.location_name,
        'latitude': pack.latitude,
        'longitude': pack.longitude,
        'weather_context': json.loads(pack.weather_context),
        'weather_coverage_notes': pack.weather_coverage_notes,
        'breaking': pack.breaking,
        'distance_km': pack.distance_km,
        'status': pack.status,
        'reviewer_notes': pack.reviewer_notes,
        'created_at': pack.created_at,
        'drafts': [
            {
                'id': d.id,
                'generator_name': d.generator_name,
                'headline_options': json.loads(d.headline_options),
                'cover_spec': json.loads(d.cover_spec),
                'caption_short': d.caption_short,
                'caption_long': d.caption_long,
                'carousel_outline': json.loads(d.carousel_outline),
            }
            for d in pack.drafts
        ],
        'assets': pack.assets,
        'attribution': pack.attribution,
    }


@app.get('/content-packs', response_model=list[ContentPackOut])
def list_content_packs(
    status: ContentPackStatus | None = None,
    breaking: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ContentPack)
    if status:
        query = query.filter(ContentPack.status == status)
    if breaking is not None:
        query = query.filter(ContentPack.breaking == breaking)
    packs = query.order_by(ContentPack.created_at.desc()).all()
    return [serialize_pack(p) for p in packs]


@app.get('/content-packs/{pack_id}', response_model=ContentPackOut)
def get_content_pack(pack_id: int, db: Session = Depends(get_db)):
    pack = db.query(ContentPack).filter(ContentPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail='Not found')
    return serialize_pack(pack)


@app.patch('/content-packs/{pack_id}', response_model=ContentPackOut)
def update_content_pack(pack_id: int, payload: ContentPackUpdate, db: Session = Depends(get_db)):
    pack = db.query(ContentPack).filter(ContentPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail='Not found')

    if payload.summary is not None:
        pack.summary = payload.summary
    if payload.bullets is not None:
        pack.bullets = json.dumps(payload.bullets)
    if payload.tags is not None:
        pack.tags = json.dumps(payload.tags)
    if payload.reviewer_notes is not None:
        pack.reviewer_notes = payload.reviewer_notes
    if payload.status is not None:
        try:
            set_status(pack, payload.status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    db.refresh(pack)
    return serialize_pack(pack)


@app.post('/content-packs/{pack_id}/approve', response_model=ContentPackOut)
def approve_content_pack(pack_id: int, db: Session = Depends(get_db)):
    pack = db.query(ContentPack).filter(ContentPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail='Not found')
    try:
        set_status(pack, ContentPackStatus.APPROVED)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(pack)
    return serialize_pack(pack)


@app.post('/content-packs/{pack_id}/reject', response_model=ContentPackOut)
def reject_content_pack(pack_id: int, payload: RejectIn, db: Session = Depends(get_db)):
    pack = db.query(ContentPack).filter(ContentPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail='Not found')
    pack.reviewer_notes = payload.reviewer_notes
    if pack.status == ContentPackStatus.DRAFT_READY:
        set_status(pack, ContentPackStatus.IN_REVIEW)
    db.commit()
    db.refresh(pack)
    return serialize_pack(pack)


@app.get('/content-packs/{pack_id}/export')
def export_handoff(pack_id: int, db: Session = Depends(get_db)):
    pack = db.query(ContentPack).filter(ContentPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail='Not found')
    return {'handoff_package': serialize_pack(pack), 'units': {'distance': 'km', 'ui_toggle_supported': 'miles'}}


@app.post('/pipeline/run')
def run_pipeline(db: Session = Depends(get_db)):
    created = run_ingestion(db)
    run_enrichment_and_generation(db)
    return {'created_content_packs': created}
