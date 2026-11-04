# Pick a job

Use the exact catalog slug under `khadinakbar/` for these starting points. Always inspect the current fields before constructing input. The full directory also includes e-commerce, jobs, property, social platforms, travel, news, public web data and more.

| Ask for this | Start with | What to return |
|---|---|---|
| Find keywords for a product or service | `dataforseo-keyword-research` | A shortlist grouped by intent, with reported demand, country and language. Leave missing volume unknown. |
| Audit a website | `complete-seo-audit` | The top fixes, affected URLs, and how many pages were checked. |
| Track organic rankings | `keyword-rank-tracker` | A dated baseline for one domain, keyword set, location and device. Compare like-for-like snapshots; “not observed” is not rank zero. |
| See if AI search mentions my site | `ai-search-visibility-tracker` | A platform-by-query comparison; distinguish mentions from links and missing coverage from a negative result. |
| Find which sources AI answers cite | `ai-citations-tracker` | Source URLs by prompt and tracked domain. Inspect demo flags; never present simulated results as real. |
| Rewrite my copy in a natural voice | `ai-text-humanizer` | A revision beside the authorized original. Preserve facts and names; flag changes in meaning. |
| Build a local business list | Maps app: `google-maps-leads-scraper` → optionally `bulk-website-contact-extractor` → `email-address-validator` | A private CSV with businesses, public contacts and coverage notes. |
| Research a different platform or market | Use `menu`, then `find` | Show the matching Store listing, input needed and what its results can establish. |

## Two useful combinations

**Search opportunity brief.** Find relevant keywords, let the user choose a shortlist, then check where their domain ranks. Preserve the same country and language across steps. Return a table of term, reported demand, observed rank and source. Each paid step needs its own exact plan.

**Brand visibility check.** Use a consistent prompt set for the brand and its competitors. Run visibility and citation research separately; report which platforms returned evidence, where the brand appeared, and which URLs were actually cited. Do not treat missing responses as losses.

For repeat observations, give the plan an explicit `--observation YYYY-MM-DD`. The same plan resumes the same run. A new observation requires a new approval; no background schedule is installed.
