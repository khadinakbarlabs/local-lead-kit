"""Render the full Markdown directory directly from the published catalog."""
import json
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
def main():
    data=json.loads((ROOT/'local_lead_kit/catalog.json').read_text()); shelves=defaultdict(list)
    for row in data['actors']: shelves[row['shelves'][0]].append(row)
    template=(ROOT/'scripts/catalog-template.html').read_text()
    safe=json.dumps(data['actors'],ensure_ascii=True).replace('<',r'\u003c')
    (ROOT/'docs/catalog.html').write_text(template.replace('__INVENTORY__',safe).replace('__MARK__',(ROOT/'docs/brand/mark.svg').read_text()))
    sections=[f"# Actorfield · Actor directory\n\n{len(data['actors'])} public [Store listings]({data['source']}) on {data['updated']}. Each Actor appears once below. The agent’s search also uses secondary shelves and Store categories. A listing is discovery evidence, not a successful test run."]
    sections+=[' · '.join(f'[{k} ({len(rows)})](#{k})' for k,rows in sorted(shelves.items()))]
    for k,rows in sorted(shelves.items()):
        sections.append('## '+k+'\n\n'+'\n'.join('- ['+r['title'].replace('[','\\[').replace(']','\\]')+'](https://apify.com/'+r['slug']+')' for r in rows))
    (ROOT/'docs/directory.md').write_text('\n\n'.join(sections)+'\n')
if __name__=='__main__':main()
