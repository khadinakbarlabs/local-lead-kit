"""A single goal-to-task router shared by every Looksy host."""
from collections import Counter, defaultdict
from functools import lru_cache
import json
from math import log
from pathlib import Path
import re
from urllib.parse import quote

ROOT = Path(__file__).parent
ROUTING = json.loads((ROOT / 'routing.json').read_text())
# Rules classify the subject of the request; the public listing and default build
# supply the actual task, required inputs and any documented operation selectors.
GROUPS = [
 ('Writing and language','Rewrite and review copy','humanizer|content-detector|paraphrase|proofread'),
 ('Search and visibility','AI mentions and citations','ai-citation|ai-overview|ai-search-(brand|visibility)|llm-visibility|ai-seo-tracker|profound-ai'),
 ('Search and visibility','Search positions and results','rank-tracker|accuranker|serp|rank-check|bing-search|google-search-results'),
 ('Search and visibility','Keyword demand and ideas','keyword-(difficulty|research|discovery|planner|fanout|search-volume)|keywords?-(explorer|overview)|longtail|autocomplete|search-volume|google-trends|answerthepublic|dataforseo-keyword|domain-keyword'),
 ('Search and visibility','Site health and links','backlink|seo-audit|seo-spider|broken-link|domain-authority|sitemap|screamingfrog|internal-link|core-web'),
 ('Business and leads','Local business discovery','google-maps|apple-maps|yellow-pages|local-business|naver-map|google-places'),
 ('Business and leads','Contacts and enrichment','contact|email|enrichment|apollo-alternative|clearbit|cognism|hunter-io|snov|zoominfo'),
 ('Business and leads','Companies and funding','funding|investor|crunchbase|companies-house|startup|company-search|business-directory|venture-capital'),
 ('Market intelligence','Reviews and reputation','reviews?-|ratings?-|trustpilot|sentiment|reputation'),
 ('Market intelligence','Ads and campaigns','ad-library|ad-spy|ads-library|ads-scraper|creative-center|advertis|commercial-content'),
 ('Commerce','Prices and availability','price-history|price-track|competitor-price|stock-monitor|price-comparison|inventory'),
 ('Property and careers','Jobs and pay','(?:^|-)jobs?(?:-|$)|salary|salaries|career|glassdoor|indeed'),
 ('Property and careers','Housing and rentals','real-estate|property|properties|zillow|redfin|rightmove|realtor|fsbo|apartments|homes-|rentals|airdna'),
 ('Travel and places','Flights and transport','flight|car-rental|aviation'),
 ('Travel and places','Stays and destinations','hotel|airbnb|booking-|expedia|tripadvisor|getyourguide|agoda|tourism'),
 ('Travel and places','Food and local places','restaurant|food-delivery|just-eat|doordash|ubereats|grubhub|opentable'),
 ('Commerce','Vehicle listings','autotrader|cargurus|carfax|car-listings|car-sales|cars-com|vehicle|carmarket'),
 ('Finance and public records','Markets and companies','crypto|stock-market|stocks-|stock-trades|stock-screener|earnings-call|coinmarketcap|dexscreener|financial|sec-filings|finviz|forex'),
 ('Finance and public records','Government and records','public-record|court|government|legislation|patent|tenders?|procurement|congress'),
 ('Media and creators','Video and channels','youtube|tiktok|twitch|douyin|dailymotion|vimeo|video-|videos-|shorts'),
 ('Media and creators','Social accounts and posts','instagram|linkedin|facebook|twitter|reddit|threads|pinterest|bluesky|snapchat|discord|telegram|mastodon|social-media'),
 ('Media and creators','News and publications','news|newsletter|podcast|spotify|article|publication|press-release'),
 ('Commerce','Products and sellers','amazon|ebay|shopify|alibaba|aliexpress|etsy|walmart|product|marketplace|bestbuy|1688|ecommerce|retail|costco'),
 ('Web and developer tools','Sites and repositories','github|gitlab|website|web-crawl|firecrawl|screenshot|domain-|dns|whois|html|site-scraper|web-scrap|apify-store'),
]
SHELF_PATHS={
 'ai-visibility':('Search and visibility','AI mentions and citations'),
 'rank-tracking':('Search and visibility','Search positions and results'),
 'keyword-research':('Search and visibility','Keyword demand and ideas'),
 'seo':('Search and visibility','SEO research'),
 'writing':('Writing and language','Rewrite and review copy'),
 'maps-and-local':('Business and leads','Local business discovery'),
 'prospecting':('Business and leads','Business sources'),
 'reviews':('Market intelligence','Reviews and reputation'),
 'social-and-video':('Media and creators','Social and video sources'),
 'commerce':('Commerce','Shopping sources'),
 'jobs-and-property':('Property and careers','Employment and housing sources'),
 'travel-and-places':('Travel and places','Destinations and services'),
 'news-and-media':('Media and creators','News and publications'),
 'developers-and-web':('Web and developer tools','Web data services'),
 'ai-and-automation':('Web and developer tools','Specialist tools'),
 'other':('Web and developer tools','Specialist sources'),
}
# These cards are editorial shortcuts to exact published Actors. Required API
# fields always come from the published contract, not from the conversational brief.
GUIDED={
 'google-maps-leads-scraper':('Find local businesses on Google Maps','business type, cities, target count','business, website, source, contact coverage','local leads find clients near me business list roofing companies prospects csv'),
 'bulk-website-contact-extractor':('Find public contacts on business websites','business website URLs','website, public contact, source','company websites email addresses contact enrichment'),
 'email-address-validator':('Check a list of email addresses','addresses and permitted checks','address, reported check, uncertainty','validate email address list check'),
 'dataforseo-keyword-research':('Find keywords and search demand','seed terms, market, language','keyword, market, reported volume, intent','keyword ideas search demand search volume terms search phrases'),
 'keyword-rank-tracker':('Check where a website ranks','domain, keywords, market, device','term, observed position, matching URL, observation date','where does my website rank rankings organic position search tracking baseline'),
 'complete-seo-audit':('Audit a website for SEO issues','website and page limit','issue, affected URL, supporting evidence, priority','audit website site health technical seo fix pages'),
 'ai-search-visibility-tracker':('Check brand mentions in AI search','domain, brand, prompts or topics, platforms','prompt, platform, observed mention, linked source','is my brand mentioned ai answers visibility competitor share'),
 'ai-citations-tracker':('Find sources cited in AI answers','prompts and tracked domains','prompt, cited URL, domain, evidence status','which sources get cited ai citations cite chatgpt answer links'),
 'ai-text-humanizer':('Rewrite copy in a natural voice','authorized text, audience and tone','revised text, substantive edits, preserved facts','humanize rewrite natural less robotic copy sounds human'),
 'youtube-channel-email-extractor':('Find contact details for YouTube channels','channel URLs or niche and desired count','channel, public contact, source, missing values','youtube creators emails channels contact details'),
 'amazon-competitor-price-tracker':('Compare competitor prices on Amazon','products, market and observation date','product, seller, observed price, source, date','amazon competitor prices compare sku tracking'),
 'google-flights-scraper':('Compare flight fares for a route','origin, destination, travel date, passengers','route, fare, currency, stops and source date','flight prices airline tickets flights travel airfare'),
 'youtube-transcript-extractor':('Read transcripts from YouTube videos','video URLs and preferred language','video, language, returned transcript and missing coverage','youtube transcripts subtitles captions video text'),
 'youtube-comments-scraper':('Read YouTube comments and replies','video URL and scope','video, comment, reply relationship and source','youtube comments audience feedback questions'),
 'website-backlink-checker':('Review a website’s backlink sources','domain and scope','source page, target, returned link details','backlinks referring domains links to my website'),
}
FAMILY_BRIEFS = {
    'AI mentions and citations': ('brand, prompts, platforms and competitors', 'prompt, platform, mention, cited URL and coverage'),
    'Search positions and results': ('domain or query, market, language and device', 'query, observed position, URL, market and date'),
    'Keyword demand and ideas': ('seed topic, language, country and result limit', 'keyword, observed volume, intent and data availability'),
    'SEO research': ('domain, competitor or URL, market and scope', 'observed metric, affected URL, source and missing data'),
    'Site health and links': ('site URL, crawl depth or page cap', 'affected page, issue, evidence and priority'),
    'Rewrite and review copy': ('authorized text, tone and audience', 'requested text, material edits and preserved facts'),
    'Local business discovery': ('business type, location and target count', 'business, location, site, source and coverage'),
    'Contacts and enrichment': ('authorized business sources and fields needed', 'entity, public contact field, source and verification limits'),
    'Companies and funding': ('industry, region, company or funding criteria', 'company, reported funding or corporate facts, source and date'),
    'Business sources': ('business type, source and market', 'entity, matching criteria, source and observed details'),
    'Reviews and reputation': ('entity or product, platform, language and sample size', 'review theme, supporting example, source and sampling window'),
    'Ads and campaigns': ('advertiser, market, platform and dates', 'advertiser, creative, observed dates and source'),
    'Prices and availability': ('product identifiers, market, currency and comparison period', 'item, seller, observed price, currency, availability and timestamp'),
    'Products and sellers': ('product query or listing URL, market and filters', 'item, seller, price, currency and listing source'),
    'Shopping sources': ('marketplace, item or category, and geography', 'listing, observed attributes, price when returned and source'),
    'Vehicle listings': ('make, model, geography and price range', 'vehicle, mileage, asking price, currency and listing URL'),
    'Jobs and pay': ('role, geography, seniority and time window', 'role, employer, location, posted pay when available and URL'),
    'Housing and rentals': ('area, property type, budget and currency', 'listing, area, price, property features and source URL'),
    'Employment and housing sources': ('role or property, location, scope and filters', 'matching record, observed attributes, date and source'),
    'Flights and transport': ('origin, destination, dates and traveler count', 'route, travel dates, fare, currency and observed availability'),
    'Stays and destinations': ('destination, dates, guests and preferences', 'property or destination, observed price, currency, terms and source'),
    'Food and local places': ('location, cuisine or venue, and filters', 'place, location, returned menu or venue details and source'),
    'Destinations and services': ('destination, service and travel dates', 'option, dated observations, geographic coverage and source'),
    'Markets and companies': ('asset or company, period, exchange and currency', 'instrument, observation, time, currency and source'),
    'Government and records': ('jurisdiction, entity and date window', 'public record, jurisdiction, observed date and source'),
    'Video and channels': ('channel, video URL or topic, language and sample size', 'video or channel, requested metric or text, date and source'),
    'Social accounts and posts': ('platform, account or query, period and result limit', 'account or post, requested field, timestamp and source'),
    'Social and video sources': ('platform, source, topic and observation window', 'record, source, returned engagement or content fields and coverage'),
    'News and publications': ('subject, publication or query, language and date range', 'headline or item, publisher, publication date, source and coverage'),
    'Sites and repositories': ('site or repository, operation and depth or limit', 'resource, requested fields, source, checkpoint and coverage'),
    'Web data services': ('source, desired operation and scope', 'resource, requested fields, evidence and gaps'),
    'Specialist tools': ('specific tool, target, desired output and bounds', 'artifact or record, source, observed result and limitations'),
    'Specialist sources': ('source, question and intended use', 'source-specific facts, evidence and coverage'),
}

STOP=set('the a an me us our i we my of on for with at in by from please show find tell how do does is to and get can you use give want would could should an set unrelated research compare give that this about what where which it more some up as be have has their they them into looksy'.split())
ALIASES={'customers':'leads','clients':'leads','citations':'cited','rankings':'rank','ranking':'rank','prices':'price','websites':'website','channels':'channel','companies':'business','keywords':'keyword','reviews':'review','jobs':'job','cryptocurrency':'crypto','cryptocurrencies':'crypto','releases':'release','issues':'issue','stocks':'stock','emails':'email','flights':'flight','fares':'price','fare':'price','airfare':'flight','transcripts':'transcript','sources':'source','properties':'property','rentals':'rental','comments':'comment','journalists':'journalist','cites':'cited','citations':'cited'}
def terms(text):
    return {ALIASES.get(w,w) for w in re.findall(r'[a-z0-9]+',text.lower()) if w not in STOP and not w.isdigit()}
def group(row):
    slug=row['slug'].split('/')[1]
    for category,family,pattern in GROUPS:
        if re.search(pattern,slug): return category,family
    return SHELF_PATHS[row['shelves'][0]]
def operation_scope(card, operation):
    text=label(operation).lower()
    destinations=[
        ('backlink','Search and visibility','Site health and links'),
        ('keyword','Search and visibility','Keyword demand and ideas'),
        ('serp','Search and visibility','Search positions and results'),
        ('review','Market intelligence','Reviews and reputation'),
        ('enrich emails','Business and leads','Contacts and enrichment'),
        ('public contacts','Business and leads','Contacts and enrichment'),
    ]
    for word,category,family in destinations:
        if word in text and not (word=='review' and 'github' in card['actor']):
            return {**card,'category':category,'subcategory':family,'report':FAMILY_BRIEFS[family][1]}
    return card

def label(value):
    words=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',value).replace('_',' ').replace('-',' ')
    return words[:1].upper()+words[1:]
@lru_cache(maxsize=1)
def library():
    contracts=json.loads((ROOT/'capabilities.json').read_text())['contracts']
    rows=json.loads((ROOT/'catalog.json').read_text())['actors']
    cards={}
    for row in rows:
        slug=row['slug'].split('/')[1]
        category,family=group(row)
        c=contracts[row['slug']]
        guide=GUIDED.get(slug)
        # Store summaries describe advertised use. The live schema is still needed before a run.
        shared={'actor':row['slug'],'category':category,'subcategory':family,'description':row['description'],
                'source':'https://apify.com/'+row['slug'],'contract':c['source'] if c['default_schema'] else None,
                'required_fields':c['required'],'input_fields':c['fields'],'options':c['selectors'],
                'intake':guide[1] if guide else FAMILY_BRIEFS[family][0],
                'report':guide[2] if guide else FAMILY_BRIEFS[family][1]}
        cards[slug]={**shared,'id':slug,'task':guide[0] if guide else row['title'],'aliases':guide[3] if guide else '', 'preset':{}}
        for field,values in c['selectors'].items():
            for value in values:
                # Generic modes are options on the parent card. Treat only named
                # operations and clearly actionable modes as separate tasks.
                if value.lower() in {'balanced','deep','precision','quick','premium','free_tier','bulk','global','both','standard','advanced','simple'}:continue
                if re.search(r'^(auto|default|demo|test|all|other|sample)$',value,re.I):continue
                key=slug+'#'+field+'='+quote(value,safe='')
                cards[key]={**operation_scope(shared,value),'id':key,'task':label(value)+' · '+row['title'].split(' — ')[0], 'aliases':'',
                            'preset':{field:([value] if field in c.get('array_selectors',[]) else value)}}
        for field in c.get('enrichments',[]):
            key=slug+'#'+field+'=true'
            cards[key]={**operation_scope(shared,field),'id':key,'task':label(field)+' · '+row['title'].split(' — ')[0],
                        'aliases':'','preset':{field:True}}
    return cards

def tree():
    paths=defaultdict(Counter)
    for card in library().values():paths[card['category']][card['subcategory']]+=1
    return {k:dict(sorted(v.items())) for k,v in sorted(paths.items())}

@lru_cache(maxsize=1)
def search_index():
    documents={}
    frequencies=Counter()
    for card in library().values():
        primary=terms(card['task']+' '+card['actor']+' '+card['aliases'])
        facets=terms(card['category']+' '+card['subcategory'])
        described=terms(card['description'])
        documents[card['id']]=(primary,facets,described)
        frequencies.update(primary|facets|described)
    return documents,{w:1+log((len(documents)+1)/(n+1)) for w,n in frequencies.items()}

def browse(query='',category=None,family=None,limit=6):
    all_cards=library()
    if query in all_cards:return [all_cards[query]]
    if action_for(query):
        return []
    words=terms(query); candidates=[]
    if query.strip() and not words:
        return []
    preferred = next((rule['task'] for rule in ROUTING['preferred']
                      if re.search(rule['pattern'], query, re.I)), None)
    docs,weights=search_index()
    requested_sources = words & {'github','youtube','instagram','linkedin','amazon','tiktok','facebook','reddit','crypto','flight','apify','ebay','airbnb','zillow','pinterest','shopify','telegram'}
    if preferred and not requested_sources.issubset(set().union(*docs[preferred])):
        preferred = None
    for card in all_cards.values():
        if category and card['category']!=category or family and card['subcategory']!=family:continue
        primary,facets,described=docs[card['id']]
        matched=words & (primary|facets|described)
        if words and not matched:continue
        anchors=words & {'github','youtube','instagram','linkedin','amazon','tiktok','facebook','reddit','crypto','flight','apify','ebay','airbnb','zillow','pinterest','shopify','telegram'}
        if anchors and not anchors.issubset(primary|facets|described):continue
        if words and not (words & (primary|facets)) and (len(matched)<2 or len(matched)/len(words)<0.5):continue
        score=sum(weights[w]*(5 if w in primary else 2 if w in facets else 1) for w in matched)
        score*=len(matched)/max(1,len(words)) if words else 1
        if card['aliases'] and matched:score+=3
        if card['preset']:
            operation=terms(card['task'].split(' · ')[0])
            score+=sum(weights.get(w,1) for w in words&operation)-0.75
        candidates.append((score,card))
    if preferred in all_cards:
        card = all_cards[preferred]
        if (not category or card['category'] == category) and (not family or card['subcategory'] == family):
            candidates = [(score, item) for score, item in candidates if item['id'] != preferred]
            candidates.append((1000000, card))
    candidates.sort(key=lambda t:(-t[0],t[1]['id']))
    return [card for _,card in candidates[:limit]]


def action_for(query):
    """Recognize operations on existing work before searching collection tools."""
    return next((rule for rule in ROUTING['actions']
                 if re.search(rule['pattern'], query, re.I)), None)


def route(query, limit=3):
    action = action_for(query)
    return {
        'request': query,
        'intent': action['intent'] if action else 'new_collection',
        'instruction': action['instruction'] if action else 'Inspect candidate fit, preserve the request, then preview scope and costs.',
        'tasks': browse(query, limit=limit),
    }
