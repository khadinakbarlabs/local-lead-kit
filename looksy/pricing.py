"""Preserve effective Apify PPE terms without inventing a caller's tier or costs."""
from copy import deepcopy
from datetime import datetime, timezone
import math


class PricingError(ValueError):
    """Current pricing cannot be safely interpreted."""


def finite_amount(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def current_ppe_pricing(records, *, now=None):
    """Return the complete effective record plus backward-compatible display fields.

    Apify's Actor API defines eventPriceUsd and eventTieredPricingUsd as mutually
    exclusive. Tier maps are retained; a missing flat price is never treated as
    zero or replaced with an arbitrary tier's rate.
    """
    now = now or datetime.now(timezone.utc)
    if not isinstance(records, list) or not records:
        raise PricingError('Current Actor pricing could not be verified.')
    effective = []
    for record in records:
        try:
            started = datetime.fromisoformat(record['startedAt'].replace('Z', '+00:00'))
            if started.tzinfo is None:
                raise ValueError('Missing time zone')
        except (AttributeError, KeyError, TypeError, ValueError):
            raise PricingError('The effective pricing date could not be verified; inspect the Actor in Apify.') from None
        if started <= now:
            effective.append((started, record))
    if not effective:
        raise PricingError('Current Actor pricing could not be verified.')
    latest = max(started for started, _ in effective)
    selected = [record for started, record in effective if started == latest]
    if any(record != selected[0] for record in selected[1:]):
        raise PricingError('Conflicting effective prices need review in Apify.')
    price = deepcopy(selected[0])
    if price.get('pricingModel') != 'PAY_PER_EVENT':
        raise PricingError('The current pricing model needs review before this resource can run it.')
    if type(price.get('isPPEPlatformUsagePaidByUser')) is not bool:
        raise PricingError('The platform usage payer is unknown; review current pricing in Apify.')
    if 'minimalMaxTotalChargeUsd' not in price:
        raise PricingError('The minimum event cap is unknown; review current pricing in Apify.')
    minimum = price['minimalMaxTotalChargeUsd']
    if minimum is not None and not finite_amount(minimum):
        raise PricingError('The minimum event cap is invalid; review current pricing in Apify.')
    per_event = price.get('pricingPerEvent')
    raw_events = per_event.get('actorChargeEvents') if isinstance(per_event, dict) else None
    if not isinstance(raw_events, dict) or not raw_events:
        raise PricingError('The current event prices could not be inspected.')
    events = {}
    tiered = False
    for name, raw in raw_events.items():
        if not isinstance(name, str) or not name or not isinstance(raw, dict):
            raise PricingError('The current event prices could not be inspected.')
        flat = 'eventPriceUsd' in raw
        tiers = 'eventTieredPricingUsd' in raw
        if flat == tiers:
            raise PricingError('An event must have a verified flat price or a tier price map.')
        if flat and not finite_amount(raw['eventPriceUsd']):
            raise PricingError('An event price is unknown or invalid; review current pricing in Apify.')
        if tiers:
            tier_map = raw['eventTieredPricingUsd']
            if not isinstance(tier_map, dict) or not tier_map or any(
                not isinstance(tier, str) or not tier or not isinstance(entry, dict)
                or not finite_amount(entry.get('tieredEventPriceUsd'))
                for tier, entry in tier_map.items()
            ):
                raise PricingError('An event tier price is unknown or invalid; review current pricing in Apify.')
            tiered = True
        events[name] = {**deepcopy(raw), 'price_usd': raw.get('eventPriceUsd'),
                        'title': raw.get('eventTitle', name)}
    return {**price, 'model': price['pricingModel'], 'started_at': price['startedAt'],
            'events': events, 'requires_tier_review': tiered}
