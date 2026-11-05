# Connect Looksy anywhere

Looksy picks the lowest-friction connection automatically. Your assistant checks in this order:

1. **Already connected?** If the assistant already lists Apify tools (`call-actor`, `fetch-actor-details`, or tools named `khadinakbar--…`), Looksy uses them. Nothing to set up.
2. **Web and desktop apps** (claude.ai, Claude Desktop, ChatGPT, any app that accepts a remote MCP connector): add one connector URL below and **sign in with Apify**. No API key to copy.
3. **Local agents** (Claude Code, Codex, Cursor): the Looksy plugin uses a key already in `APIFY_TOKEN`, or the one saved in your private dashboard.
4. **Nothing yet?** Only then does Looksy ask you to add a key: say **"Open my Looksy dashboard"** and paste it there. Never paste keys into chat.

## Connector URLs (sign in with Apify, no key)

Add a custom connector, paste one URL, name it **Looksy**, click **Connect** and sign in with Apify.

| Pack | Tools | URL |
| --- | --- | --- |
| **Leads** | 12 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/google-maps-leads-scraper,khadinakbar/google-maps-extractor,khadinakbar/google-maps-reviews-scraper,khadinakbar/bulk-website-contact-extractor,khadinakbar/contact-details-scraper,khadinakbar/email-address-validator,khadinakbar/linkedin-profile-search-scraper,khadinakbar/linkedin-profile-details-scraper,khadinakbar/linkedin-email-finder,khadinakbar/linkedin-profile-email-scraper,khadinakbar/phone-number-lookup-api,khadinakbar/youtube-channel-email-extractor` |
| **SEO and AI visibility** | 17 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/scrape-google-serp,khadinakbar/google-serp-all-in-one-scraper,khadinakbar/dataforseo-keyword-research,khadinakbar/keyword-search-volume-api,khadinakbar/google-trends-scraper,khadinakbar/accuranker-alternative,khadinakbar/local-rank-tracker,khadinakbar/complete-seo-audit,khadinakbar/website-seo-spider,khadinakbar/backlink-opportunity-finder,khadinakbar/website-backlink-checker,khadinakbar/ai-search-visibility-tracker,khadinakbar/ai-search-brand-monitor,khadinakbar/ai-citations-tracker,khadinakbar/ai-overviews-tracker,khadinakbar/google-ai-mode-scraper,khadinakbar/google-ai-overviews-scraper` |
| **Social and video** | 15 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/instagram-profile-scraper,khadinakbar/instagram-posts-scraper,khadinakbar/instagram-niche-influencer-finder,khadinakbar/instagram-hashtag-scraper,khadinakbar/tiktok-trending-videos-scraper,khadinakbar/tiktok-trending-hashtags-scraper,khadinakbar/tiktok-profile-scraper,khadinakbar/tiktok-video-search-scraper,khadinakbar/youtube-search-scraper,khadinakbar/youtube-channel-search-scraper,khadinakbar/youtube-transcript-extractor,khadinakbar/reddit-posts-comments-scraper,khadinakbar/reddit-comments-search-scraper,khadinakbar/linkedin-post-search-scraper,khadinakbar/linkedin-profile-posts-scraper` |
| **Ads and ecommerce** | 10 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/facebook-ads-library-scraper,khadinakbar/meta-ad-library-scraper,khadinakbar/google-ads-transparency-scraper,khadinakbar/tiktok-ads-library-scraper,khadinakbar/pinterest-ads-library-scraper,khadinakbar/amazon-product-search-scraper,khadinakbar/amazon-search-scraper,khadinakbar/amazon-reviews-scraper,khadinakbar/capterra-reviews-scraper,khadinakbar/software-reviews-all-in-one-scraper` |
| **Everything (best tool per job)** | 36 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/google-maps-leads-scraper,khadinakbar/google-maps-reviews-scraper,khadinakbar/bulk-website-contact-extractor,khadinakbar/email-address-validator,khadinakbar/linkedin-email-finder,khadinakbar/linkedin-profile-search-scraper,khadinakbar/linkedin-company-search-scraper,khadinakbar/linkedin-post-search-scraper,khadinakbar/phone-number-lookup-api,khadinakbar/scrape-google-serp,khadinakbar/dataforseo-keyword-research,khadinakbar/google-trends-scraper,khadinakbar/accuranker-alternative,khadinakbar/complete-seo-audit,khadinakbar/backlink-opportunity-finder,khadinakbar/ai-search-visibility-tracker,khadinakbar/ai-citations-tracker,khadinakbar/google-ai-mode-scraper,khadinakbar/ai-content-detector,khadinakbar/ai-text-humanizer,khadinakbar/facebook-ads-library-scraper,khadinakbar/google-ads-transparency-scraper,khadinakbar/tiktok-ads-library-scraper,khadinakbar/youtube-search-scraper,khadinakbar/youtube-transcript-extractor,khadinakbar/youtube-channel-email-extractor,khadinakbar/instagram-profile-scraper,khadinakbar/instagram-niche-influencer-finder,khadinakbar/tiktok-trending-videos-scraper,khadinakbar/tiktok-profile-scraper,khadinakbar/reddit-posts-comments-scraper,khadinakbar/amazon-product-search-scraper,khadinakbar/amazon-reviews-scraper,khadinakbar/capterra-reviews-scraper,khadinakbar/jobs-scraper,khadinakbar/zillow-all-in-one-scraper` |

- **claude.ai and Claude Desktop:** Settings → Connectors → Add custom connector.
- **ChatGPT:** add it as a custom connector or app in settings (some plans need developer mode).
- **Claude Code / Codex / Cursor:** you can add the same URL as a remote MCP server, or install the Looksy plugin.

Each connector exposes only Looksy tools plus `fetch-actor-details` (inputs and price), `call-actor` (run with a `maxTotalChargeUsd` cap), `get-actor-run` and `get-dataset-items` (results). Runs are billed to your own Apify account at each tool's published price per result.

The connector is Apify's hosted MCP server (`mcp.apify.com`); Apify handles the sign-in. Revoke access any time in Apify Console.

## Example first request

> Use Looksy to find 25 roofing companies in Austin, TX with phone, website and rating. Show the price before running.
