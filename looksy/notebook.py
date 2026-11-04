"""Private, offline handoffs between sessions and agent hosts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4
from .core import atomic_json
from .tasks import library


def brief_path(ws, key):
    if not re.fullmatch('[a-f0-9]{12}',key):
        raise ValueError('Choose a saved brief ID from history.')
    return ws/'briefs'/f'{key}.json'


def save(ws, task, goal, deliverable, next_step, plan=None):
    if task not in library():raise ValueError('Select an exact task ID.')
    for text in (goal, deliverable, next_step):
        if not isinstance(text,str) or not 1<=len(text.strip())<=4000:
            raise ValueError('Use a short goal, deliverable, and next step.')
    if plan:
        from .toolbox import load_plan
        scope=load_plan(ws,plan)
        card=library()[task]
        if scope['slug']!=card['actor'] or any(scope['input'].get(k)!=v for k,v in card['preset'].items()):
            raise ValueError('The saved plan does not match the selected task and operation.')
    key=uuid4().hex[:12]
    brief={'id':key,'created':datetime.now(timezone.utc).isoformat(timespec='seconds'),
           'task':task,'goal':goal,'deliverable':deliverable,'next_step':next_step,'plan':plan}
    atomic_json(brief_path(ws,key),brief)
    return brief


def history(ws):
    return sorted((json.loads(p.read_text()) for p in (ws/'briefs').glob('*.json')),
                  key=lambda x:x['created'],reverse=True)


def reopen(ws,key):
    brief=json.loads(brief_path(ws,key).read_text())
    card=library().get(brief['task'])
    return {**brief,'task_details':card,'cached_result':bool(brief['plan'] and (ws/brief['plan']/'result.json').exists())}


def evidence(ws,plan):
    from .toolbox import load_plan
    scope=load_plan(ws,plan)
    data=json.loads((ws/plan/'result.json').read_text())
    return scope,data


def compare(ws,left,right):
    if left==right:raise ValueError('Compare two distinct saved observations.')
    first,a=evidence(ws,left);second,b=evidence(ws,right)
    if (first['actor_id'],first['input'])!=(second['actor_id'],second['input']):
        raise ValueError('These runs used different Actors or inputs. Keep their scopes separate.')
    def snapshot(scope,data):
        return {'observation':scope.get('observation'),'status':data['status'],'rows_read':len(data['items']),
                'truncated':data['additional_rows'],'build':scope['options']['build']}
    def fingerprints(rows):
        return {hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False).encode()).hexdigest() for r in rows}
    old,new=fingerprints(a['items']),fingerprints(b['items'])
    return {'scope':first['slug'],'first':snapshot(first,a),'second':snapshot(second,b),
            'distinct_row_values_only_in_first':len(old-new),'distinct_row_values_only_in_second':len(new-old),
            'interpretation':'Counts compare exact saved row values, not entity additions or rank movement. Check both result files, source coverage, build and truncation before interpreting changes.'}


def report(ws, key):
    scope,data=evidence(ws,key)
    slug=scope['slug'].split('/')[1]
    task=library().get(slug,{})
    rows=data.get('items',[])
    fields=sorted({field for row in rows[:20] if isinstance(row,dict) for field in row})
    urls=[]
    for row in rows[:20]:
        if isinstance(row,dict):
            for value in row.values():
                if isinstance(value,str) and value.startswith(('https://','http://')) and value not in urls:
                    urls.append(value)
    return {'actor':scope['slug'],'source':task.get('source'),'status':data['status'],'rows_read':len(rows),
            'additional_rows':data['additional_rows'],'observation':scope.get('observation'),
            'returned_fields':fields,'sample_source_urls':urls[:8],'has_output':bool(data.get('output')),
            'has_run_summary':bool(data.get('run_summary')),'result_file':str(ws/key/'result.json'),
            'suggested_columns':task.get('report'),'guidance':'Answer the requested question first. Inspect the private evidence file for actual values, demo or partial flags, and coverage. Label missing values and cite a returned source or the exact run. Suggest one useful next observation.'}
