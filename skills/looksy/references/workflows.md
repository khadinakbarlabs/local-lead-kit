# Research areas and goal-driven workflows

Looksy can plan research across the areas below. Every catalog Actor and operation card belongs to at least one area; sources can belong to several areas. These are advertised capabilities, not a claim that every provider, output, live source or authenticated route has been tested. Catalog browsing and composing a workflow do not start collection or incur paid runs.

Start with the full question: who/what, market, geography, time period, desired count, decision, spending cap and report format. A recipe is a candidate plan. The assistant adapts it to that question and checks source fit before proposing a run.

## Research menu

| Area | Example outcome | Exact catalog task to inspect first |
|---|---|---|
| Products and marketplaces | Compare products, sellers, positioning and assortment in a chosen market. | `amazon-product-search-scraper` |
| Price and stock research | Compare matched competitor products with currency and availability context. | `amazon-competitor-price-tracker` |
| Competitor and market intelligence | Build a sourced competitor brief from traffic and technology observations. | `similarweb-traffic-rank-scraper` |
| SEO keywords and demand | Cluster relevant keywords by intent and observed demand. | `dataforseo-keyword-research` |
| Backlinks and link opportunities | Inspect referring links and prioritize supported link opportunities. | `website-backlink-checker` |
| SERPs and rank tracking | Measure search positions with a reproducible market and device context. | `keyword-rank-tracker` |
| AI visibility and citations | Compare brand mentions and cited sources across requested AI queries. | `ai-search-visibility-tracker` |
| AI content detection | Review detector observations for supplied authorized text without treating scores as proof. | `ai-content-detector` |
| Humanization and writing | Revise authorized copy for audience and tone while preserving factual meaning. | `ai-text-humanizer` |
| Newsletter and content planning | Turn dated source themes into a sourced newsletter outline and publishing calendar. | `substack-posts-scraper` |
| Advertising intelligence | Compare public Meta advertiser creatives and messaging themes. | `meta-ad-library-scraper` |
| B2B company research | Build a bounded company/account list with verified provider and contact provenance. | `apollo-alternative` |
| Startups, funding and launches | Find relevant startup launches and triangulate reported company facts. | `producthunt-scraper-pro` |
| Contact discovery and enrichment | Find source-backed business contacts and report field-level uncertainty. | `bulk-website-contact-extractor` |
| Email, phone and identity checks | Review supplied addresses or numbers with source-specific validation limits. | `phone-number-lookup-api` |
| Local business research | Find local businesses and enrich their public website contacts. | `google-maps-leads-scraper` |
| Maps, geocoding and directions | Resolve approved locations and compare supported routes. | `geocoding-api-byok` |
| Public social intelligence | Summarize sampled public Facebook posts and discussion themes. | `facebook-post-search-scraper` |
| Creator and influencer research | Compare relevant creators using observed audience and content evidence. | `social-media-influencer-scraper` |
| Community conversation analysis | Analyze themes and questions in a permitted Discord sample. | `discord-message-scraper` |
| Video and YouTube analysis | Combine transcripts and comments into a sourced video/audience brief. | `youtube-channel-videos-scraper` |
| Images, OCR and visual evidence | Extract supported text and inspect images against the research question. | `google-lens-ocr-api` |
| News, events and publications | Assemble dated news and relevant event evidence. | `google-news-scraper` |
| Jobs and career markets | Compare role demand, employers and advertised pay from a bounded sample. | `google-jobs-scraper` |
| Reviews and reputation | Identify review themes with supporting source examples and sample limits. | `trustpilot-reviews-scraper` |
| SEO and site audits | Prioritize site issues supported by page and performance evidence. | `complete-seo-audit` |
| Website and technology research | Check advertised website technology and supporting evidence. | `website-tech-stack-detector` |
| Developer and application ecosystems | Summarize supported repository activity and relevant software evidence. | `github-deep-scraper` |
| Finance, forex and financial events | Build a dated asset and financial-event brief with explicit supported coverage. | `yahoo-finance-scraper` |
| Crypto and on-chain intelligence | Compare bounded crypto observations with exchange and timestamp context. | `coinmarketcap-crypto-scraper` |
| Hotels and hospitality | Compare dated stays and guest feedback for approved destinations. | `booking-scraper-pro` |
| Travel, transport and dining | Compare supported fares and destination activities with dated availability. | `google-flights-scraper` |
| Housing and real estate | Compare bounded residential listings with location and asking-price evidence. | `zillow-search-scraper` |
| Government and public databases | Research authorized public tenders and corporate-record evidence by jurisdiction. | `sam-gov-scraper` |
| Authorized private sources | Check permission and supported access before analyzing private community evidence. | `discord-message-scraper` |
| Culture, music, sports and specialist sources | Build a sourced specialist brief from a supported book, music or sports operation. | `spotify-all-in-one-scraper` |

## Ask for the result you need

- “Compare 30 matched competitor SKUs on Amazon and eBay in the UK. Separate VAT, shipping, variants and missing prices. Show the plan and maximum cost first.”
- “Research SEO keywords, backlinks and US mobile SERPs for my bakery. Turn the evidence into a prioritized plan and CSV.”
- “Compare my brand's AI visibility and cited sources for these prompts. Keep unsupported platforms and missing answers explicit.”
- “Review these authorized articles with an AI content detector, explain uncertainty, then propose a separate factual revision in my voice.”
- “Plan four newsletter issues for independent retailers using recent Substack topics, search questions and public Reddit discussion. Cite the evidence and give me an editorial calendar.”
- “Compare Meta, TikTok, LinkedIn and Pinterest ad messaging for these advertisers. Do not infer spend or campaign results from ad-library records.”
- “Research 25 B2B accounts and recent Product Hunt launches. Check whether the advertised Apollo/Lusha alternative actually supports the fields I need before proposing collection.”
- “Summarize customer questions from public Facebook posts, TikTok comments and Reddit threads; report sampling dates and coverage.”
- “Analyze messages from this Discord channel that I administer. First confirm a supported, authorized access route; summarize themes without unnecessary personal details.”
- “Compare YouTube transcripts and comments for these videos, extract OCR from the authorized images, and distinguish quotations from your conclusions.”
- “Compare forex and financial-event sources for my requested pairs and dates. Mark unsupported pairs/event types unknown rather than substituting equity data.”
- “Find hotels for these dates, compare flights and local activities, and provide dated observations with currency and availability limits.”
- “Compare Zillow homes in these neighborhoods and calculate driving routes from verified addresses. Distinguish asking prices from completed transactions.”
- “Research procurement records and corporate registries in these jurisdictions. Use only the named supported public databases.”

## How the assistant generates a workflow

1. **Intake.** Preserve the entire original request. Reuse supplied subjects, cities, dates, count, budget and requested artifact; ask for missing critical distinctions only. A saved report or supplied file should use the existing-data route first.
2. **Choose and adapt.** Browse research areas or compose candidates. Explain why exact task cards fit the question. Multi-source questions can combine recipes, reorder independent branches or omit irrelevant steps. A template is not a fixed automatic pipeline.
3. **Validate contracts.** Read every chosen task card and the current live schema. Advertised input fields do not prove any output field. Verify operation selectors, authentication, source/provider, required inputs and field semantics. Mark unsupported sources, entities and fields unknown.
4. **Preview bounded approval.** Present exact input drafts, per-step limits, source access, current prices, any separate platform usage, maximum total cost and requested deliverable. Obtain approval for that bounded plan before any paid collection. New scope or spend needs a revised preview.
5. **Collect and inspect.** Collect only approved scope. Read actual rows, output/summary, failures and truncation; a successful run status alone does not establish useful data. Preserve source URLs and dates. Stop dependent work if required data or access is missing.
6. **Map and join.** Use each step's handoff instructions. Pass only observed values into supported fields. Join normalized URLs, verified IDs and compatible market/date/variant keys; report duplicate, unmatched and missing rows. Independent branches can reuse intake rather than pretend one source emitted another source's input.
7. **Analyze and export.** Answer the original decision with supporting evidence and uncertainty. Use authorized local analysis for collected data. Produce the requested table/brief, plus source, date, scope, coverage, missing fields and limitations. See [export formats](export-formats.md) for destination-specific contact files.
8. **Reopen.** Reopen the saved artifact and check it contains the requested answer and fields. Save a private notebook brief/checkpoint when requested. On return, reopen cached evidence before proposing new paid work. No schedule runs automatically.

## Recipe reference

Recipes include an outcome, intake, ordered exact task IDs, dependencies, handoff instructions, artifact, quality/coverage rules and access constraints. Before replacing a task, inspect the replacement's contract; a matching brand name does not prove equivalence.

| Recipe | Intake | Ordered tasks |
|---|---|---|
| Product and marketplace landscape (`product-market`) | marketplace; category or product URLs; country/currency; sample size | `amazon-product-search-scraper` → `amazon-product-details-scraper` |
| eBay listing comparison (`ebay-comparison`) | eBay query or listing URLs; market; condition; item cap | `ebay-product-listing-scraper` → `ebay-all-in-one-scraper` |
| Competitor price comparison (`price-comparison`) | product identifiers; seller URLs; market/currency; observation date | `amazon-competitor-price-tracker` → `price-from-url-api` |
| Competitor landscape (`competitor-landscape`) | company/domain; competitor list; market; date window | `similarweb-traffic-rank-scraper` → `website-tech-stack-detector` |
| Keyword and topic opportunity plan (`keyword-plan`) | seed topics; country/language; domain; keyword cap | `dataforseo-keyword-research` → `keyword-search-volume-api` |
| Backlink and outreach evidence (`backlink-audit`) | domain; competitors; market; link cap | `website-backlink-checker` → `backlink-opportunity-finder` |
| SERP and rank baseline (`serp-baseline`) | domain; queries; country/language; device; observation date | `keyword-rank-tracker` → `scrape-google-serp` |
| AI visibility and citation brief (`ai-citation-brief`) | brand/domain; competitors; prompt set; supported platforms; market | `ai-search-visibility-tracker` → `ai-citations-tracker` |
| AI content detection review (`detector-review`) | authorized text; language; purpose; sample scope | `ai-content-detector` |
| Humanize and fact-check copy (`humanize-copy`) | authorized text; audience; tone; facts and quotations to preserve | `ai-text-humanizer` |
| Newsletter and editorial plan (`newsletter-plan`) | audience; newsletter topic; reference publications; date window; cadence | `substack-posts-scraper` → `google-trends-scraper` → `dataforseo-keyword-research` |
| Meta ad creative research (`meta-ads`) | advertiser/page; country; date window; creative cap | `meta-ad-library-scraper` |
| TikTok advertising research (`tiktok-ads`) | advertiser/query; market; dates; ad cap | `tiktok-ads-library-scraper` |
| LinkedIn ad research (`linkedin-ads`) | advertiser; market; dates; ad cap | `linkedin-ad-library-search-scraper` |
| Pinterest ad research (`pinterest-ads`) | advertiser/query; market; dates; ad cap | `pinterest-ads-library-scraper` |
| Google ad transparency research (`google-ads`) | advertiser/domain; region; dates; ad cap | `google-ads-transparency-scraper` |
| B2B account and Apollo alternative research (`b2b-account-list`) | industry; region; company criteria; requested fields; record cap | `apollo-alternative` → `bulk-website-contact-extractor` |
| Startup and Product Hunt landscape (`startup-launches`) | sector; launch period; region; company cap | `producthunt-scraper-pro` → `crunchbase-company-api` |
| Public business contact research (`contact-research`) | authorized business URLs or accounts; permitted email/phone fields; region; record cap | `bulk-website-contact-extractor` → `email-address-validator` |
| Email and phone validation (`phone-validation`) | authorized email/phone list; country format; allowed checks; count | `phone-number-lookup-api` → `email-address-validator` |
| Local business prospect brief (`local-lead-map`) | business type; cities or boundaries; count; requested fields | `google-maps-leads-scraper` → `bulk-website-contact-extractor` |
| Map and directions brief (`route-planning`) | origin/destination or addresses; travel mode; departure context; route cap | `geocoding-api-byok` → `google-maps-directions-api` |
| Public Facebook conversation brief (`facebook-social`) | public page/query; date window; language; post/comment cap | `facebook-post-search-scraper` → `facebook-comments-scraper` |
| TikTok audience and topic brief (`tiktok-social`) | query/accounts; market; date window; video/comment cap | `tiktok-search-scraper` → `tiktok-comments-scraper` |
| Reddit audience research (`reddit-social`) | topic/subreddits; time window; post/comment cap; language | `reddit-posts-search-scraper` → `reddit-comments-scraper` |
| Creator and influencer shortlist (`creator-shortlist`) | niche; platform; market/language; creator count; criteria | `social-media-influencer-scraper` → `youtube-channel-statistics-scraper` |
| Authorized Discord conversation analysis (`discord-conversations`) | authorized server/channel; supported access route; date window; message cap; privacy scope | `discord-message-scraper` |
| YouTube video and audience analysis (`youtube-analysis`) | video/channel URLs; language; date window; video/comment cap | `youtube-channel-videos-scraper` → `youtube-transcript-extractor` → `youtube-comments-scraper` |
| OCR and visual evidence review (`ocr-evidence`) | authorized image URLs/files in supported format; language; image cap; target fields | `google-lens-ocr-api` → `google-lens-visual-search` |
| News and event research brief (`news-events-brief`) | topic; market; date range; publication/event scope; cap | `google-news-scraper` → `10times-events-scraper` |
| Jobs and hiring market brief (`jobs-market`) | role; locations; seniority; date range; job cap | `google-jobs-scraper` → `linkedin-jobs-scraper` |
| Review and reputation audit (`review-themes`) | company/product URLs; platforms; language; date range; review cap | `trustpilot-reviews-scraper` → `brand-sentiment-analyzer` |
| Technical SEO and performance audit (`site-audit`) | domain; page cap; crawl boundaries; device/market | `complete-seo-audit` → `google-pagespeed-insights` |
| Website technology and evidence audit (`website-evidence`) | approved domains; requested technology fields; page cap | `website-tech-stack-detector` → `website-stack-evidence-audit` |
| Repository and app ecosystem brief (`repository-brief`) | repository URLs; requested operation; date range; record cap | `github-deep-scraper` |
| Financial, forex and earnings research (`finance-events`) | ticker/pair; exchange; time window; currency; event types; record cap | `yahoo-finance-scraper` → `earnings-call-transcript-api` |
| Crypto market and wallet brief (`crypto-market`) | assets/contracts; chain/exchange; time window; count | `coinmarketcap-crypto-scraper` → `dexscreener-realtime-monitor` |
| Hotel and short-stay comparison (`hotel-comparison`) | destination; dates; guests; budget/currency; property cap | `booking-scraper-pro` → `booking-reviews-scraper` |
| Flight and destination options (`travel-options`) | origin/destination; travel dates; passengers; currency; option cap | `google-flights-scraper` → `getyourguide-scraper` |
| Zillow and real estate comparison (`property-comparison`) | market/area; property type; budget/currency; features; listing cap | `zillow-search-scraper` → `zillow-all-in-one-scraper` |
| Government and public database brief (`public-records`) | jurisdiction; company/topic; date range; record type; cap | `sam-gov-scraper` → `companies-house-uk-scraper` |
| Authorized private-source research plan (`private-source-plan`) | source/account; explicit user authority; supported authentication; permitted channels/fields; scope and retention | `discord-message-scraper` |
| Music, culture and sports research (`culture-brief`) | specific domain/source; entity/query; dates; requested fields; cap | `spotify-all-in-one-scraper` |

## Access and evidence limits

Public social sources do not grant access to private groups, accounts, messages or deleted content. Private research requires explicit user authority and a supported authentication route. Credentials belong in supported secure mechanisms, never in exported reports. A task named `lusha-alternative` exists in the catalog; direct Lusha service access and data equivalence are unverified. The same provider check applies to other named alternatives. Forex pairs and economic-event coverage must be confirmed in the live schema; equity/crypto support does not establish forex support.

Contact discovery reports field-level provenance and uncertainty; lookup or validation does not prove consent, current employment or number ownership. AI detector scores do not establish authorship or misconduct. Humanization should preserve facts and required attribution. Ads observations do not establish spend, conversion or profitability. Finance, travel, housing and price observations need timestamps, geography, currency and availability context.

## Programmatic planning surface

`areas()` returns a list of `{id, label, description, task_ids, count}`. Membership is multi-label and task IDs are exact library keys.

`compose(goal, area=None, limit=3)` returns `{goal, area, candidates, instruction, execution, capability_evidence, unknowns}`. Each candidate contains `{id, area, title, goal, intake, steps, artifact, quality_rules, access_constraints}` plus retrieval terms. Each step has `{id, task_id, purpose, depends_on, handoff}`. `execution` is always `planning_only`; these functions neither connect services nor start paid work. The full original goal remains available for adaptation. Invalid areas, empty goals and limits outside 1–10 fail explicitly.

## Additional social and conversation recipes

- **Instagram content and audience analysis** uses supported public post/Reels evidence and sampled comments, preserving post relationships, dates and coverage. Adapt the findings into an original content plan.
- **Public Telegram discussion research** discovers public channels and reads a selected supported message sample, retaining source links and dates. Private membership alone does not establish a supported collection route.
