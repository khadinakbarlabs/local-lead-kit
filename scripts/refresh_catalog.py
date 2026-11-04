"""Refresh from the public Apify Store only; no credentials or account exports."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import ssl
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OWNER = 'khadinakbar'
# Order determines the primary shelf; additional matches remain searchable.
SHELVES = {
    'ai-visibility': r'ai.citation|ai.search.brand|ai.seo.tracker|ai.visibility|brand.visibility|ai.overview|answer.engine|generative.engine|llm.(?:mention|citation|visibility)|chatgpt.(?:search|rank|citation)|ai.search.(?:visibility|rank|track|monitor)',
    'rank-tracking': r'rank.track|rank.check|serp|search.engine.results|google.search.results|keyword.rank|local.rank',
    'keyword-research': r'keyword|search.volume|related.search|autocomplete|search.suggest|google.trends',
    'seo': r'\bseo\b|backlink|domain.authority|site.audit|sitemap|indexation|internal.link|page.speed|core.web.vital|broken.link',
    'writing': r'humani[sz]|paraphras|rewrit|proofread|grammar|ai.text.detec|content.writ',
    'maps-and-local': r'(?:google|apple).maps|google.my.business|local.business|places.search|business.listing|local.citation|yellow.pages|yelp',
    'prospecting': r'lead.gen|leads|prospect|company.enrich|contact|email|funding|investor|b2b',
    'reviews': r'reviews?|trustpilot|reputation|ratings?',
    'social-and-video': r'tiktok|linkedin|youtube|instagram|facebook|twitter|threads|pinterest|social.media|snapchat|reddit|twitch|bluesky|discord',
    'commerce': r'amazon|ebay|alibaba|aliexpress|ecommerce|e.commerce|shopify|product|walmart|etsy|shopping|marketplace|retail',
    'jobs-and-property': r'jobs?|career|salary|real.estate|property|zillow|realtor',
    'travel-and-places': r'hotel|booking|flight|travel|airbnb|tripadvisor|restaurant|tourism',
    'developers-and-web': r'github|website|web.crawl|web.scrap|domain|http|\bapi\b|extractor|crawler',
    'other': r'(?!)',
}

FALLBACK = {'SEO_TOOLS':'seo','REAL_ESTATE':'jobs-and-property','JOBS':'jobs-and-property','TRAVEL':'travel-and-places','ECOMMERCE':'commerce','SOCIAL_MEDIA':'social-and-video','VIDEOS':'social-and-video','NEWS':'news-and-media','LEAD_GENERATION':'prospecting','DEVELOPER_TOOLS':'developers-and-web','AI':'ai-and-automation','AUTOMATION':'ai-and-automation'}

def shelves(slug,title,categories):
    labels=[k for k,pattern in SHELVES.items() if re.search(pattern,slug+' '+title,re.I)]
    return labels or list(dict.fromkeys(FALLBACK[c] for c in FALLBACK if c in categories)) or ['other']

def fetch():
    context = ssl.create_default_context(cafile='/etc/ssl/cert.pem' if Path('/etc/ssl/cert.pem').exists() else None)
    offset, rows = 0, {}
    while True:
        url = f'https://api.apify.com/v2/store?username={OWNER}&limit=100&offset={offset}'
        with urlopen(url, context=context, timeout=40) as response:
            data = json.load(response)['data']
        page = data['items']
        for item in page:
            if item['username'] != OWNER or not re.fullmatch(r'[a-zA-Z0-9-]+', item['name']):
                raise ValueError('Unexpected Store identity')
            slug = item['name']
            labels = shelves(slug,item['title'],item.get('categories',[]))
            rows[item['id']] = dict(id=item['id'], slug=f'{OWNER}/{slug}', title=item['title'], description=item.get('description',''),
                                     shelves=labels or ['other'], categories=item.get('categories', []))
        offset += len(page)
        if offset >= data['total']: break
        if not page: raise ValueError('Incomplete Store response')
    if len(rows) != data['total']: raise ValueError('Store changed during refresh; retry before publishing')
    return {'source': f'https://apify.com/{OWNER}', 'updated': datetime.now(timezone.utc).date().isoformat(),
            'actors': sorted(rows.values(), key=lambda r:r['slug'])}

if __name__ == '__main__':
    data = fetch()
    (ROOT/'looksy/catalog.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print(len(data['actors']), 'public Store entries')
