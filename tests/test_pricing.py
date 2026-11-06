from datetime import datetime, timezone
import unittest

from looksy.pricing import PricingError, current_ppe_pricing


def price_fixture(**updates):
    return {'pricingModel': 'PAY_PER_EVENT', 'startedAt': '2026-01-01T00:00:00Z',
            'minimalMaxTotalChargeUsd': None, 'isPPEPlatformUsagePaidByUser': True,
            'pricingPerEvent': {'actorChargeEvents': {'result': {
                'eventTitle': 'Result', 'eventDescription': 'Each returned result',
                'eventPriceUsd': 0.01, 'isOneTimeEvent': False}}}, **updates}


class PricingTests(unittest.TestCase):
    def normalize(self, prices):
        return current_ppe_pricing(prices, now=datetime(2026, 11, 7, tzinfo=timezone.utc))

    def test_selects_latest_effective_record_and_preserves_complete_pricing(self):
        old=price_fixture()
        current=price_fixture(startedAt='2026-10-01T00:00:00Z',minimalMaxTotalChargeUsd=0.5,
                              isPPEPlatformUsagePaidByUser=False)
        future=price_fixture(startedAt='2027-01-01T00:00:00Z')
        result=self.normalize([future,old,current])
        for key,value in current.items():self.assertEqual(result[key],value)
        self.assertEqual(result['events']['result']['price_usd'],0.01)
        self.assertEqual(result['events']['result']['eventDescription'],'Each returned result')
        result['pricingPerEvent']['actorChargeEvents']['result']['eventPriceUsd']=123
        self.assertEqual(current['pricingPerEvent']['actorChargeEvents']['result']['eventPriceUsd'],0.01)

    def test_tier_prices_remain_explicit_and_never_become_a_guessed_flat_price(self):
        price=price_fixture()
        event=price['pricingPerEvent']['actorChargeEvents']['result']
        del event['eventPriceUsd']
        event['eventTieredPricingUsd']={'FREE':{'tieredEventPriceUsd':0.02},'BRONZE':{'tieredEventPriceUsd':0.01}}
        result=self.normalize([price])
        self.assertIsNone(result['events']['result']['price_usd'])
        self.assertEqual(result['events']['result']['eventTieredPricingUsd'],event['eventTieredPricingUsd'])
        self.assertTrue(result['requires_tier_review'])

    def test_unknown_or_malformed_pricing_does_not_become_free(self):
        bad=[]
        for value in [None,'true',0]:
            bad.append(price_fixture(isPPEPlatformUsagePaidByUser=value))
        for value in ['0.5',True,-1,float('nan'),float('inf')]:
            bad.append(price_fixture(minimalMaxTotalChargeUsd=value))
        missing=price_fixture();del missing['isPPEPlatformUsagePaidByUser'];bad.append(missing)
        for value in [None,'0.01',True,-1,float('nan'),float('inf')]:
            price=price_fixture();price['pricingPerEvent']['actorChargeEvents']['result']['eventPriceUsd']=value;bad.append(price)
        price=price_fixture();price['pricingPerEvent']['actorChargeEvents']['result']['eventTieredPricingUsd']={'FREE':{'tieredEventPriceUsd':0.1}};bad.append(price)
        price=price_fixture();event=price['pricingPerEvent']['actorChargeEvents']['result'];del event['eventPriceUsd'];event['eventTieredPricingUsd']={'FREE':{}};bad.append(price)
        for price in bad:
            with self.subTest(price=price),self.assertRaises(PricingError):self.normalize([price])

    def test_unknown_effective_date_does_not_silently_fall_back_to_old_price(self):
        for value in [None,'invalid','2026-01-01T00:00:00']:
            with self.subTest(value=value),self.assertRaises(PricingError):
                self.normalize([price_fixture(),price_fixture(startedAt=value)])
        with self.assertRaises(PricingError):self.normalize([price_fixture(startedAt='2027-01-01T00:00:00Z')])
        with self.assertRaises(PricingError):self.normalize([price_fixture(),price_fixture(minimalMaxTotalChargeUsd=5)])


if __name__=='__main__':unittest.main()
