# Execution and quality

The source registry pins these exact Apify Actors:

- [Google Maps Leads Scraper](https://apify.com/khadinakbar/google-maps-leads-scraper)
- [Bulk Website Contact Extractor](https://apify.com/khadinakbar/bulk-website-contact-extractor)
- [Email Address Validator](https://apify.com/khadinakbar/email-address-validator)

Every new campaign inspects the current default builds and input schemas. A changed build or price after planning requires another review. Each paid start has a positive `maxTotalChargeUsd`, timeout, memory limit and pinned build. The sum of durable reservations stays within the approved campaign allowance. [Apify's run API](https://docs.apify.com/api/v2/actors-runs-post) documents this control across pricing models. Account receipts remain authoritative; assistant-model usage is separate.

Discovery uses the user's territories with optional contact enrichment explicitly disabled. Websites are deduplicated by host, extracted in batches of at most 50, and email checks in batches of at most 250. A maximum of five extracted addresses per requested business is submitted for validation; additional returned addresses remain unconfirmed. No automatic identical-query repeats are used to fill a target.

Run IDs and start reservations are written before continuing. An unknown paid start keeps its reservation and stops; do not automatically repeat it. Known runs can be observed again. A stale lock after a process crash needs deliberate inspection, not blind deletion or another paid start. Raw stage evidence is saved privately. Importing finished runs is read-only and is useful when the needed result already exists.

Partial discovery, unreachable sites, no email found, unchecked addresses, extraction artifacts and failed runs are different states. Useful saved data stays available when a stage stops. A failed upstream with no useful data is not an empty-market success. SMTP probing is off, so no mailbox is confirmed in this edition. Public source context and basic email checks do not establish permission or willingness to receive outreach.
