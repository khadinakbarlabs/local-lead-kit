"""Goal-driven research templates, grounded in exact advertised task cards.

This module is a planning surface: it neither connects accounts nor starts runs.
Input contracts describe advertised capabilities; returned fields require inspection.
"""
from functools import lru_cache
import json
from pathlib import Path
import re

from .tasks import library, terms

DATA = Path(__file__).with_name('workflows.json')
WORKFLOW_ANCHORS = {
    'youtube', 'instagram', 'telegram', 'amazon', 'discord', 'facebook', 'tiktok', 'linkedin', 'pinterest',
    'reddit', 'ebay', 'zillow', 'forex', 'crypto', 'apollo', 'lusha',
    'spotify', 'github', 'substack', 'beehiiv',
}



@lru_cache(maxsize=1)
def _definitions():
    return json.loads(DATA.read_text())


def areas():
    """Return multi-label research areas, including every catalog operation card."""
    cards = library()
    result = []
    matched = set()
    definitions = _definitions()['areas']
    for definition in definitions:
        if definition.get('fallback'):
            continue
        patterns = definition['patterns']
        task_ids = sorted(key for key, card in cards.items()
                          if any(re.search(pattern, card['actor'].split('/')[-1])
                                 for pattern in patterns))
        matched.update(task_ids)
        result.append({**{k: definition[k] for k in ('id', 'label', 'description')},
                       'task_ids': task_ids, 'count': len(task_ids)})
    for definition in definitions:
        if definition.get('fallback'):
            task_ids = sorted(set(cards) - matched)
            result.append({**{k: definition[k] for k in ('id', 'label', 'description')},
                           'task_ids': task_ids, 'count': len(task_ids)})
    return result


def recipes():
    """Return templates only after checking all references against this library."""
    definitions = _definitions()
    cards = library()
    area_ids = {area['id'] for area in definitions['areas']}
    for recipe in definitions['recipes']:
        if recipe['area'] not in area_ids:
            raise ValueError('Unknown research area: ' + recipe['area'])
        seen = set()
        for step in recipe['steps']:
            if step['task_id'] not in cards:
                raise ValueError('Unknown catalog task: ' + step['task_id'])
            if not set(step['depends_on']).issubset(seen):
                raise ValueError('Workflow dependencies must precede their consumer')
            seen.add(step['id'])
    # Callers can adapt the returned templates without mutating cached definitions.
    return json.loads(json.dumps(definitions['recipes']))


def compose(goal, area=None, limit=3):
    """Find templates and preserve the whole goal for an assistant to adapt.

    This is retrieval, not autonomous research execution or an access guarantee.
    An unsupported specific source is surfaced instead of silently substituted.
    """
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError('A non-empty research goal is required')
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10:
        raise ValueError('limit must be an integer from 1 to 10')
    known_areas = {row['id']: row for row in areas()}
    if area is not None and area not in known_areas:
        raise ValueError('Unknown research area: ' + str(area))
    words = terms(goal)
    candidates = []
    # Explicit source/subject anchors keep generic words such as 'analysis' or
    # 'market' from suggesting unrelated collections. Alternatives remain
    # candidates, subject to their explicit provider/access checks below.
    anchors = words & WORKFLOW_ANCHORS
    for recipe in recipes():
        if area is not None and recipe['area'] != area:
            continue
        title_words = terms(recipe['title'] + ' ' + recipe['goal'])
        alias_words = terms(recipe['queries'])
        if anchors and not anchors.intersection(title_words | alias_words):
            continue
        matched = words & (title_words | alias_words)
        score = sum(4 if word in title_words else 2 for word in matched)
        score += sum(12 for pattern in recipe.get('match_patterns', [])
                     if re.search(pattern, goal, re.I))
        if not score and area is None:
            continue
        candidates.append((score, recipe))
    candidates.sort(key=lambda row: (-row[0], row[1]['id']))
    unknowns = []
    # An alternative's name does not establish direct access to the named service.
    if re.search(r'\blusha\b', goal, re.I):
        unknowns.append('Direct Lusha service access is unverified. The catalog has lusha-alternative; inspect its live contract and actual provider before proposing it as a substitute.')
    if re.search(r'\bforex\b|foreign exchange|economic calendar', goal, re.I):
        unknowns.append('Forex pair and economic-event coverage must be checked in the selected live contract; stock or crypto coverage does not establish forex support.')
    if re.search(r'\bprivate\b|behind.*login|authenticated|internal discord', goal, re.I):
        unknowns.append('Private-source access requires user authorization and a supported authentication route. No template grants access or bypasses restrictions.')
    return {
        'goal': goal,
        'area': area,
        'candidates': [recipe for _, recipe in candidates[:limit]],
        'instruction': _definitions()['composition_instruction'],
        'execution': 'planning_only',
        'capability_evidence': 'Catalog cards advertise inputs and intended use; outputs, live availability and access are unverified until inspected.',
        'unknowns': unknowns,
    }
