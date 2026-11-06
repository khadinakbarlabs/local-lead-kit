# Connect Looksy through Apify

Use the assistant you already have. Add an Apify-hosted research pack, sign in with Apify, then describe the result you want. Your assistant provides the AI.

Looksy Agent is an independent project by Khadin Akbar Labs. These URLs connect directly to Apify's official MCP service. Apify handles sign-in and executes the selected Actors under your account.

## Choose a pack

The count is the number of selected Actor entries, not the total number of MCP tools. Apify can add supporting run and storage tools. Pack selection does not restrict account permissions, and the generic `call-actor` helper can accept other Actor names. Keep Looksy workflows within the catalog and the scope you authorized.

| Research pack | Selected Actors | Connector URL |
| --- | --- | --- |
| Leads | 12 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/google-maps-leads-scraper,khadinakbar/google-maps-extractor,khadinakbar/google-maps-reviews-scraper,khadinakbar/bulk-website-contact-extractor,khadinakbar/contact-details-scraper,khadinakbar/email-address-validator,khadinakbar/linkedin-profile-search-scraper,khadinakbar/linkedin-profile-details-scraper,khadinakbar/linkedin-email-finder,khadinakbar/linkedin-profile-email-scraper,khadinakbar/phone-number-lookup-api,khadinakbar/youtube-channel-email-extractor&telemetry-enabled=false` |
| SEO and AI visibility | 17 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/scrape-google-serp,khadinakbar/google-serp-all-in-one-scraper,khadinakbar/dataforseo-keyword-research,khadinakbar/keyword-search-volume-api,khadinakbar/google-trends-scraper,khadinakbar/accuranker-alternative,khadinakbar/local-rank-tracker,khadinakbar/complete-seo-audit,khadinakbar/website-seo-spider,khadinakbar/backlink-opportunity-finder,khadinakbar/website-backlink-checker,khadinakbar/ai-search-visibility-tracker,khadinakbar/ai-search-brand-monitor,khadinakbar/ai-citations-tracker,khadinakbar/ai-overviews-tracker,khadinakbar/google-ai-mode-scraper,khadinakbar/google-ai-overviews-scraper&telemetry-enabled=false` |
| Social and video | 15 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/instagram-profile-scraper,khadinakbar/instagram-posts-scraper,khadinakbar/instagram-niche-influencer-finder,khadinakbar/instagram-hashtag-scraper,khadinakbar/tiktok-trending-videos-scraper,khadinakbar/tiktok-trending-hashtags-scraper,khadinakbar/tiktok-profile-scraper,khadinakbar/tiktok-video-search-scraper,khadinakbar/youtube-search-scraper,khadinakbar/youtube-channel-search-scraper,khadinakbar/youtube-transcript-extractor,khadinakbar/reddit-posts-comments-scraper,khadinakbar/reddit-comments-search-scraper,khadinakbar/linkedin-post-search-scraper,khadinakbar/linkedin-profile-posts-scraper&telemetry-enabled=false` |
| Ads and ecommerce | 10 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/facebook-ads-library-scraper,khadinakbar/meta-ad-library-scraper,khadinakbar/google-ads-transparency-scraper,khadinakbar/tiktok-ads-library-scraper,khadinakbar/pinterest-ads-library-scraper,khadinakbar/amazon-product-search-scraper,khadinakbar/amazon-search-scraper,khadinakbar/amazon-reviews-scraper,khadinakbar/capterra-reviews-scraper,khadinakbar/software-reviews-all-in-one-scraper&telemetry-enabled=false` |
| All research areas | 36 | `https://mcp.apify.com/?tools=fetch-actor-details,call-actor,get-actor-run,get-dataset-items,khadinakbar/google-maps-leads-scraper,khadinakbar/google-maps-reviews-scraper,khadinakbar/bulk-website-contact-extractor,khadinakbar/email-address-validator,khadinakbar/linkedin-email-finder,khadinakbar/linkedin-profile-search-scraper,khadinakbar/linkedin-company-search-scraper,khadinakbar/linkedin-post-search-scraper,khadinakbar/phone-number-lookup-api,khadinakbar/scrape-google-serp,khadinakbar/dataforseo-keyword-research,khadinakbar/google-trends-scraper,khadinakbar/accuranker-alternative,khadinakbar/complete-seo-audit,khadinakbar/backlink-opportunity-finder,khadinakbar/ai-search-visibility-tracker,khadinakbar/ai-citations-tracker,khadinakbar/google-ai-mode-scraper,khadinakbar/ai-content-detector,khadinakbar/ai-text-humanizer,khadinakbar/facebook-ads-library-scraper,khadinakbar/google-ads-transparency-scraper,khadinakbar/tiktok-ads-library-scraper,khadinakbar/youtube-search-scraper,khadinakbar/youtube-transcript-extractor,khadinakbar/youtube-channel-email-extractor,khadinakbar/instagram-profile-scraper,khadinakbar/instagram-niche-influencer-finder,khadinakbar/tiktok-trending-videos-scraper,khadinakbar/tiktok-profile-scraper,khadinakbar/reddit-posts-comments-scraper,khadinakbar/amazon-product-search-scraper,khadinakbar/amazon-reviews-scraper,khadinakbar/capterra-reviews-scraper,khadinakbar/jobs-scraper,khadinakbar/zillow-all-in-one-scraper&telemetry-enabled=false` |

## Add the connection

For Claude web or Desktop, open Settings → Connectors and add a custom connector. For ChatGPT, use the custom app or connector controls available to your account. Client plans, developer-mode availability and administrator policy can affect access. Paste a URL above, name the connection **Looksy via Apify**, and complete Apify sign-in.

For a local coding agent, ask **“Connect Looksy through Apify.”** The plugin's `connect` tool returns instructions for the current client. Claude Code and Codex use the remote name `looksy-apify` so it can coexist with the local `looksy` server.

```sh
# Replace <connector-url> with one complete URL from the table.
claude mcp add --transport http looksy-apify "<connector-url>"
# Then use /mcp, choose looksy-apify, and authenticate in your browser.

codex mcp add looksy-apify --url "<connector-url>"
codex mcp login looksy-apify
```

For Cursor, add a remote MCP server with the chosen URL and complete sign-in using the client's controls. After connecting, verify access with an authenticated read. Seeing tool names alone does not establish authorization. [Apify's current connection instructions](https://docs.apify.com/mcp)

## Start research

> Find up to 25 roofing companies in Austin with websites, phone numbers and sources. Show the exact inputs and costs before running.

The assistant inspects the selected Actor, input fields and pricing, reviews the plan with you, starts the approved run and reads the actual results. `call-actor` limits belong in `callOptions`, following its current schema. The event cap is per run and may exclude platform usage. Charges can apply to empty or failed runs. Preserve the run ID and inspect it before retrying an interrupted request.

The hosted service excludes full-permission Actors. A local route must not be used to bypass that restriction. Only use sources and data you are authorized to process. [Execution safeguards](apify-integration.md)

## Local dashboard and API-key option

The installed plugin also provides a private local dashboard. Say **“Open my Looksy dashboard”** when you want local settings, saved history or Local Leads. The dashboard verifies a local Apify key and offers a skippable AI-provider step. Enter keys in the private form, never in chat. Hosted sign-in remains in your assistant and does not populate local dashboard credentials.

The local plugin supplies Looksy's workflow guidance and saved files. A hosted-only connection supplies Apify tools, with workflows led by your current assistant. [Install the plugin](../README.md#install-looksy-agent)

## Privacy and access

Generated URLs opt out of Apify MCP telemetry using its documented option. Apify and your assistant still apply their operational, billing and data-retention policies. Manage hosted authorization through your assistant and Apify account settings. Account access can be revoked independently of local files. [Privacy](../PRIVACY.md)
