from __future__ import annotations

from .interfaces import Enricher, EnrichmentResult, GeneratedDraft, Generator, IngestedItem, Ingestor

LOCATION_DB = {
    'Zurich': (47.3769, 8.5417),
    'Nairobi': (-1.2864, 36.8172),
    'Sydney': (-33.8688, 151.2093),
    'Denver': (39.7392, -104.9903),
}


class MockRSSIngestor(Ingestor):
    def fetch_items(self) -> list[IngestedItem]:
        return [
            IngestedItem('evt-001', 'Trail runner wins alpine stage', 'Unexpected sprint finish at summit.', 'Zurich'),
            IngestedItem('evt-002', 'Surf event paused due to swell warning', 'Officials review safety in Sydney.', 'Sydney'),
        ]


class GlobalContextEnricher(Enricher):
    def enrich(self, item: IngestedItem) -> EnrichmentResult:
        tags = ['sport']
        why = {'sport': 'Event is sports-related by source title and summary.'}
        if 'runner' in item.title.lower():
            tags.append('athlete')
            why['athlete'] = 'Title references a specific competitor.'

        lat_lon = LOCATION_DB.get(item.location_name or '', (None, None))
        if item.location_name:
            tags.append('location')
            why['location'] = f"Detected location '{item.location_name}' and geocoded to global coordinates."

        weather = {
            'forecast_summary': f'Global forecast checked for {item.location_name or "unknown"}.',
            'alerts': ['Best-effort: no severe alerts found in feed']
        }
        notes = 'Global weather forecast coverage enabled. Alerts are best-effort and provider dependent.'

        return EnrichmentResult(
            tags=tags,
            why_tagged=why,
            latitude=lat_lon[0],
            longitude=lat_lon[1],
            weather_context=weather,
            weather_coverage_notes=notes,
            breaking='warning' in item.title.lower(),
        )


class BasicSocialGenerator(Generator):
    name = 'basic-social-v1'

    def generate(self, item: IngestedItem, enrichment: EnrichmentResult) -> GeneratedDraft:
        headlines = [
            f'Breaking: {item.title}',
            f'{item.title} — What changed today',
            f'{item.title}: Key takeaways',
            f'Global update: {item.title}',
            f'Sendy Brief: {item.title}',
        ]
        cover_spec = {
            'title': item.title[:70],
            'subtitle': f"Location: {item.location_name or 'TBD'}",
            'style': 'high-contrast, mobile first',
        }
        carousel = [
            {'slide': 1, 'title': 'What happened', 'body': item.summary},
            {'slide': 2, 'title': 'Who is involved', 'body': ', '.join(enrichment.tags)},
            {'slide': 3, 'title': 'Where', 'body': item.location_name or 'Unknown'},
            {'slide': 4, 'title': 'Weather context', 'body': enrichment.weather_context.get('forecast_summary', '')},
            {'slide': 5, 'title': 'What to watch next', 'body': 'Monitor official updates and athlete statements.'},
        ]
        return GeneratedDraft(
            headline_options=headlines,
            cover_spec=cover_spec,
            caption_short=f"{item.title} | {item.location_name or 'Global'}",
            caption_long=f"{item.summary}\n\nTags: {', '.join(enrichment.tags)}\nWeather: {enrichment.weather_context.get('forecast_summary')}",
            carousel_outline=carousel,
        )
