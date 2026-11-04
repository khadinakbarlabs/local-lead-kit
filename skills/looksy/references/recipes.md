# Research recipes

Choose the smallest sequence that delivers the requested artifact. Each named Actor has a task card. Validate the current inputs for that card and review the observed result before continuing. Keep the same market, dates and filters when a comparison depends on them.

| User outcome | Steps | Final artifact | Return visit |
|---|---|---|---|
| Find local customers | Use Local Leads to search Maps for the business type and cities. If requested, extract public contact details from returned business sites and validate the addresses. | Private CSV with business, source and contact coverage. Report actual count versus target. | Reopen the campaign to review a shortlist or extend to a new territory. |
| Prioritize SEO opportunities | Use `dataforseo-keyword-research` for the seed terms, then `keyword-rank-tracker` for the selected terms and domain. | Keyword, reported demand, observed position, market, and source. Avoid opportunity scores without stated criteria. | Save the original inputs and compare the next dated rank snapshot. |
| Check brand visibility in AI answers | Use `ai-search-visibility-tracker` and, if citation evidence is requested, `ai-citations-tracker`. Keep prompts and platforms consistent. | Prompt-by-platform mentions and cited domains. Separate cited, mentioned, missing, and simulated. | Reuse the prompt set to check changes. |
| Understand what YouTube viewers ask | Use `youtube-transcript-extractor` and `youtube-comments-scraper` on the same videos. | Topic, example viewer question, whether the transcript covers it, and video source. Show language and sample size. | Reopen the brief before researching the next video. |
| Compare a product's price and buyer feedback | Use `amazon-competitor-price-tracker` and `amazon-reviews-scraper` for the same product and market. | Observed offers with date/currency, repeated review themes, and sampling limits. | Compare like-for-like offers at a later observation. |
| Research a software project | Use `github-deep-scraper` and inspect its published issues, releases, or contributor modes as needed. | A release or issue brief with original repository links. Distinguish open issues from confirmed defects. | Return to the same repository and filters. |
| Compare flights | Use `google-flights-scraper` with airports, travel dates, and passenger scope. | Returned itineraries, observed fares, currency and stops. State the observation time. | Recheck the same itinerary when the user requests fresh prices. |
| Rewrite a draft | Use `ai-text-humanizer` with the authorized draft and desired tone. | Revised copy plus material edits, with factual claims preserved. | Save the brief’s tone and format, not the original text unless needed. |

For any other supported request, find an individual task first. A multi-step recipe is optional. If a step returns no usable output, report the gap before considering a paid follow-up.
