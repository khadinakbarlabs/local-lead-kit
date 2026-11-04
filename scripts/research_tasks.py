"""Read public default-build contracts. No token or paid Actor run is involved."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
from pathlib import Path
import re
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SELECTORS = {'operation','operations','task','tasks','action','actions','mode','modes','scrapemode','searchtype','datatype','scrapetype','requesttype','endpoint','endpoints','tool','tools'}
ENRICH = re.compile(r"^(include|scrape|enrich|extract|fetch)(Reviews|Replies|Comments|Variants|Posts|Emails|Contacts|Company|JobDetails|FullText|Stories|RelatedSearches|Competitors|ProductDetails|Officers|TechnologySignals|PublishedContacts|Profiles|Videos|Transcript|Subtitles|Backlinks|Ratings)$",re.I)
TLS = ssl.create_default_context(cafile='/etc/ssl/cert.pem' if Path('/etc/ssl/cert.pem').exists() else None)

def inspect(row):
    slug = row['slug']
    url = 'https://api.apify.com/v2/acts/'+slug.replace('/','~')+'/builds/default/openapi.json'
    for attempt in range(3):
        try:
            with urlopen(url,context=TLS,timeout=16) as response:
                doc=json.load(response)
            schema=doc['components']['schemas']['inputSchema']
            properties=schema.get('properties',{})
            selectors={}
            for name,spec in properties.items():
                if re.sub('[^a-z]','',name.lower()) not in SELECTORS:continue
                values=spec.get('enum') or (spec.get('items') or {}).get('enum') or []
                if values and all(isinstance(v,str) and len(v)<=120 for v in values):
                    selectors[name]=values
            return slug,dict(source=url,default_schema=True,required=schema.get('required',[]),fields=list(properties),selectors=selectors,
                             array_selectors=[k for k in selectors if properties[k].get('type')=='array'],
                             enrichments=[k for k,v in properties.items() if ENRICH.match(k) and v.get('type')=='boolean'])
        except HTTPError as error:
            if error.code not in (408,429,500,502,503,504):break
            time.sleep(min(12,2**attempt*2))
        except (KeyError,TypeError,ValueError):break
        except (OSError,URLError):time.sleep(attempt+1)
    return slug,dict(source=url,default_schema=False,required=[],fields=[],selectors={})

if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('--cache',type=Path);a=args.parse_args()
    catalog=json.loads((ROOT/'looksy/catalog.json').read_text())
    cache=a.cache
    if cache:cache.mkdir(exist_ok=True,parents=True)
    def get(row):
        path=cache/(row['id']+'.json') if cache else None
        if path and path.exists():
            cached=json.loads(path.read_text())
            if cached.get('default_schema') and ('enrichments' in cached or not any(ENRICH.match(k) for k in cached['fields'])):return row['slug'],cached
        slug,data=inspect(row)
        if path:path.write_text(json.dumps(data))
        return slug,data
    with ThreadPoolExecutor(max_workers=6) as pool:
        contracts=dict(pool.map(get,catalog['actors']))
    public={'date':date.today().isoformat(),'contracts':contracts}
    (ROOT/'looksy/capabilities.json').write_text(json.dumps(public,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Checked',len(contracts),'public listings;',sum(r['default_schema'] for r in contracts.values()),'default input schemas available.')
