[![Looksy Agent research guide](docs/brand/guide-preview.png)](https://khadinakbarlabs.github.io/looksy/)

# Looksy Agent

**Research workflows powered by Apify, inside your AI assistant.**

Connect your Apify account, describe the result you want, review the plan and costs, and let your assistant collect and analyze the evidence. Looksy organizes the khadinakbar Actor catalog into leads, SEO, AI visibility, ecommerce, advertising, social media and other research workflows.

Looksy is an independent project by Khadin Akbar Labs. Apify operates the hosted connection and account sign-in. The Looksy plugin adds workflow guidance, local research history, exports and a local MCP server. Marketplace approval and Apify endorsement require their own review.

## Connect Looksy

1. Open the [connection guide](docs/connect.md) and choose a research pack.
2. Add its Apify-hosted URL to your assistant and sign in with Apify.
3. Ask for an outcome, such as **“Find up to 25 roofers in Austin and prepare a spreadsheet with websites and sources. Show me the plan and costs first.”**

Your existing assistant provides the AI. The hosted connection works with clients that support Apify's remote MCP and sign-in. Availability depends on the client, account and administrator settings. Local coding agents can also [install the plugin](#install-looksy-agent) for saved workflows and the dashboard.

[Connect and choose a pack](docs/connect.md) · [Explore the research guide](https://khadinakbarlabs.github.io/looksy/) · [Apify integration safeguards](docs/apify-integration.md)

## Give this to your agent

```text
set up Looksy - https://khadinakbarlabs.github.io/looksy/llms.txt
```

The agent checks the available connection, helps you sign in, then returns to your request. API-key setup in the private dashboard is available when needed.

## Choose the work

| What you need | Ask your assistant |
| --- | --- |
| New research | “Find potential clients in my city and show the sources.” |
| Analyze existing data | “Turn my Apify CSV into a competitor report.” |
| Resume saved work | “Open my last Looksy research brief and its next step.” |

The bundled catalog is a dated snapshot. It currently organizes 659 Actors into 36 research areas, 45 workflow recipes and 1,091 task entries. Availability, permissions, prices and useful output must be checked for each selected Actor. Snapshot metrics help discovery and do not establish current reliability.

## Research areas

| Area | Example outcomes |
| --- | --- |
| Ecommerce and products | Product discovery, supplier research, marketplace comparisons, eBay and Shopify catalog research, observed prices and availability |
| SEO and search | Website audits, keyword demand, ranking baselines, backlinks, search results and search traffic estimates with their coverage limits |
| AI visibility and writing | Brand mentions, AI citations, reported content-detection signals and humanization of authorized drafts |
| Advertising | Meta, Facebook, Instagram, TikTok, LinkedIn and other supported ad-library research, creative and landing-page comparisons |
| B2B, startups and leads | Local businesses, company research, Product Hunt, hiring signals, public contact details and enrichment |
| Social and content | Facebook, Instagram, TikTok, Reddit and other supported social sources, content planning, newsletters and social intelligence |
| Conversations and video | Authorized Discord/community research, discussion themes, YouTube questions, transcripts, video-analysis modes and OCR |
| Travel and hospitality | Flights, hotels, activities, guest reviews, Maps places and directions |
| Careers and property | Job hunting, posted compensation, housing, rentals, Zillow and market-specific real-estate listings |
| Markets and public records | Crypto, supported stocks/forex lookups, financial events, company filings, government sources and source-backed research |
| Contact checks | Supported email and phone lookups with explicit uncertainty and source context |

Each task card links to its advertised source and inputs. Coverage depends on the selected Actor, geography, source access and current contract. Private sources require your authorization and a supported connection. Named alternatives to Apollo, Lusha or another service have their own contracts and data sources.

## Build a workflow around the outcome

Ask **“Use Looksy Agent to design a workflow for [goal], using [market and scope], and deliver [format].”**

Looksy Agent uses research templates as a starting point, gathers missing inputs, checks source fit and plans the steps. It carries actual observed identifiers and URLs between steps, analyzes the evidence, then prepares the requested output and a saved next step.

| Outcome | Research sequence | Deliverable |
| --- | --- | --- |
| Find relevant local clients | Business discovery → public website contacts → address checks → review | Prospect spreadsheet with sources and missing fields |
| Prepare an SEO roadmap | Site/keyword research → observed rankings → prioritized findings | Keyword-to-page plan and audit backlog |
| Measure AI visibility | Fixed buyer prompts → supported provider results → mentions and cited URLs | Dated evidence matrix and reusable baseline |
| Research a product market | Comparable listings → exact variants/prices → buyer reviews | Product comparison and buyer-needs brief |
| Plan content | Relevant posts/videos → available transcripts and discussion → original analysis | Source-linked topic plan and content brief |
| Analyze community discussions | Authorized messages/threads → preserved context → themes and questions | Conversation research report with sampling coverage |

[Workflow design and research coverage](skills/looksy/references/workflows.md) · [Example deliverables](skills/looksy/references/examples.md)

## Install Looksy Agent

The local plugin requires Python 3.11 or newer. Its install identifier remains `looksy`.

| Assistant | Install |
| --- | --- |
| Claude Code | `/plugin marketplace add khadinakbarlabs/looksy`, then `/plugin install looksy@looksy-marketplace`. Open a fresh session. |
| Codex | `codex plugin marketplace add khadinakbarlabs/looksy`, then `codex plugin add looksy@looksy-marketplace`. Open a fresh session. |
| Cursor | Use the Cursor archive from the release and the client's local plugin installation flow. |
| Other MCP clients | Run `python3 <plugin-root>/skills/looksy/scripts/mcp.py` as a local stdio server. |

[Download version 0.7.0](https://github.com/khadinakbarlabs/looksy/releases/tag/v0.7.0) · [Connection instructions](docs/connect.md)

## Local MCP tools

| Tool | Purpose |
| --- | --- |
| `connect` | Connection status and Apify sign-in instructions for your assistant |
| `find_tools` | Candidate Actors with dated catalog evidence |
| `list_jobs` | Research jobs, examples and suggested follow-up steps |
| `get_tool` | Current published input schema, permissions and event pricing |
| `run_tool` | Preview a specific run, then execute the reviewed plan with its approval token |
| `get_run` | Observe the same run, available charges and paginated results |
| `account` | Verify local account access and inspect reported usage |

The first `run_tool` call prepares a plan. After the user approves the exact input and cost scope, the assistant repeats it with the returned approval token. Reusing an approved plan observes its existing run. An uncertain start stays held for inspection. For separately requested fresh collection, supply a new `request_id` label, review its new plan and approve it. Never change the label to bypass an uncertain start. Remote Apify tools have their own schemas and controls, so the assistant must apply the same review process before calling them.

## Review scope and costs

Installation and offline catalog browsing are free. Apify bills collection to the connected user's account under the selected Actor's current contract. Review event prices, startup or minimum charges, input, exact build, runtime limit and any separate platform usage before starting.

**The event cap is per run. Platform usage can be additional.** Unknown charges stay unknown, and run-time totals remain provisional until reconciled with Apify billing. Empty or failed runs can still have charges. Useful rows, source coverage and quality are checked separately from the run status. [Cost and execution details](docs/apify-integration.md)

## Open your private dashboard

Ask **“Open my Looksy dashboard.”** The installed plugin starts the dashboard on your device and opens a private launch link.

The local dashboard has two setup steps. First, verify the required Apify API key. Second, choose **Use current assistant** or save an optional Claude, OpenRouter, OpenAI or Gemini key. The hosted Apify sign-in connects your assistant independently and does not copy its credentials into the local dashboard.

Use **Settings** to manage local connections and **History** to reopen local briefs or campaigns. Research takes place in your assistant. Local Leads has a dedicated campaign review and CSV export flow. On Windows, use the dashboard or `APIFY_TOKEN` for local credentials.

[Preview the dashboard](docs/brand/dashboard-setup.png) · [Private dashboard instructions](skills/looksy/references/connection.md)

## Prepare data for your other tools

Local Leads exports research CSV files and prepares Instantly, Smartlead and HubSpot import formats. The toolbox supports CSV/JSON, explicit field mapping and an email exclusion list. Export receipts show included, duplicate and missing-email counts. Unknown names stay blank and source context is retained.

Review the destination mapping and authorize the exact action before any external upload or outreach. Contact checks do not establish consent or guarantee deliverability. [Export formats](skills/looksy/references/export-formats.md)

## Return to your work

Ask **“Save this as a Looksy brief with the next step.”** Briefs and cached results stay in the private local workspace. A supported assistant on the same device can reopen them. Remote Apify results remain available under the user's account and its retention settings. Cloud runs continue independently of your chat or dashboard.

[Privacy](PRIVACY.md) · [Security](SECURITY.md) · [Support](SUPPORT.md) · [Validation](docs/validation.md) · [License](LICENSE)
