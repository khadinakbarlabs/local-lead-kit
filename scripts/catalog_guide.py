"""Render the full Markdown directory directly from the published catalog."""
import json
from pathlib import Path
from collections import defaultdict
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from looksy.tasks import library,tree

def main():
    data=json.loads((ROOT/'looksy/catalog.json').read_text()); shelves=defaultdict(list)
    for row in data['actors']: shelves[row['shelves'][0]].append(row)
    template=(ROOT/'scripts/catalog-template.html').read_text()
    cards=list(library().values())
    actors={c['actor']:{'description':c['description'],'source':c['source']} for c in cards}
    ordered=sorted(cards,key=lambda c:(not bool(c['aliases']),bool(c['preset']),c['category'],c['task']))
    tasks=[dict(id=c['id'],actor=c['actor'],category=c['category'],family=c['subcategory'],task=c['task'],report=c['report'],
                search=' '.join([c['task'],c['actor'],c['category'],c['subcategory'],c['aliases'],c['description']]).lower().replace('-',' ')) for c in ordered]
    safe=json.dumps({'actors':actors,'tasks':tasks},ensure_ascii=True,separators=(',',':')).replace('<',r'\u003c')
    (ROOT/'docs/catalog.html').write_text(template.replace('__INVENTORY__',safe).replace('__MARK__',(ROOT/'docs/brand/mark.svg').read_text()))
    outline=['# Looksy task library',f"{len(cards):,} task entries from {len(actors)} public Actors. Expand a category to see its subcategories and individual tasks. The Field Guide adds search, saved tasks and copyable requests."]
    for category,families in tree().items():
        outline.extend(['<details>','<summary>'+category+'</summary>',''])
        for family,count in families.items():
            subset=[c for c in cards if c['category']==category and c['subcategory']==family]
            outline.append(f'### {family} ({count})')
            for c in subset:
                title=c['task'].replace('[','\\[').replace(']','\\]')
                outline.append(f"- [{title}]({c['source']})")
        outline.append('</details>')
    (ROOT/'docs/tasks.md').write_text('\n'.join(outline)+'\n')
    sections=[f"# Looksy · Actor directory\n\n{len(data['actors'])} public [Store listings]({data['source']}) on {data['updated']}. Each Actor appears once below. The agent’s search also uses secondary shelves and Store categories. A listing is discovery evidence, not a successful test run."]
    sections+=[' · '.join(f'[{k} ({len(rows)})](#{k})' for k,rows in sorted(shelves.items()))]
    for k,rows in sorted(shelves.items()):
        sections.append('## '+k+'\n\n'+'\n'.join('- ['+r['title'].replace('[','\\[').replace(']','\\]')+'](https://apify.com/'+r['slug']+')' for r in rows))
    (ROOT/'docs/directory.md').write_text('\n\n'.join(sections)+'\n')
if __name__=='__main__':main()
