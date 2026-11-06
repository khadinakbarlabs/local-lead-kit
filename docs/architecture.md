# Architecture

One canonical skill describes the research workflow. The remote path uses Apify’s official hosted MCP and OAuth directly from the assistant. The local path combines a stdio MCP server with a contained local app. Codex and Claude manifests adapt that source; native release ZIPs include only their own wrapper. The Python app uses the standard library, a private filesystem workspace, a loopback HTTP interface and a fixed-origin Apify client. No hosted publisher backend or installed background scheduler is involved.

The app validates the niche, territories, target and allowance, reads the current exact Actor builds, schemas and event prices, then persists a plan. User approval is tied to that plan's hash. A changed source requires a new review before another paid start.

The worker discovers companies, deduplicates website hosts for bounded extraction, checks unique addresses, and joins results back to stable business locations. Checkpoints preserve known run IDs and reservations. Unknown starts retain their allowance and stop. Failed stages preserve saved useful data and cannot silently advance to another paid source.

The UI keeps actual counts and partial states, paginates results, and exports spreadsheet-safe CSV files. Optional AI review is supplied by the active assistant using a bounded sample and evidence URLs. Its attribution is checked before notes are attached, but source and semantic truth still require review.

Local access uses a private session cookie, request key, strict Host/Origin checks and content policy. Runtime access data and campaign files are excluded from source and release packages. No account credential or customer dataset is shipped.

Version 0.2 adds one shared task router, an offline Store index, the toolbox CLI and four packaging formats (Claude, Codex, Cursor and portable Agent Plugins). To extend coverage, run `python3 scripts/refresh_catalog.py`, regenerate the directory with `python3 scripts/catalog_guide.py`, and review the catalog diff and curated task menu. Refresh uses only the public Store. The original Maps campaign keeps its three verified stages.

## Looksy Agent 0.4

The shared task vocabulary and intent rules are exported into the static guide. Existing-data and saved-research requests are routed before collection discovery. A validated local draft preserves requested campaign fields in the launcher, with HTML-safe bootstrap serialization. Saved campaign editing restores every request field.

Research areas classify the catalog across multiple purposes. Recipe templates bind exact task cards, ordered dependencies, intake and output contracts for the assistant to adapt. The assistant checks actual schemas and intermediate outputs before paid steps. Local exports prepare flat records for destination import screens with review counts and provenance columns. Destination writes depend on explicit authorization and available host connectors.

## Private dashboard

The installed launcher starts a private loopback dashboard. The authenticated browser must verify Apify and choose whether to save an AI-provider connection before entering settings, history or Local Leads. The public static guide points to installation instructions. Credential forms exist only in the private dashboard.

Connection updates are atomic and owner-readable. A fingerprint binds verification to the effective Apify key. Provider calls are opt-in, single-request text operations with a fixed host, selected model and an approved prompt. History joins the existing local notebook and campaign summaries. The default research path stays with the active host assistant.

## Apify connection and local execution

The remote URL selects a research pack. Apify handles authentication and execution, and the assistant handles workflow reasoning. Generic helpers can access more than the selected Actor list when the account permits it, so pack selection is not an authorization boundary. The local dashboard has separate credentials and history.

Local discovery reads the dated catalog. A live preview reads the exact Actor and published build rather than relying on a Store search result. Shared execution checks reject full or unverified permissions, unavailable sources and unsupported pricing. Local MCP prepares a durable account-bound plan, then uses its approval token and start ledger for one run. Read failures preserve the run identity. Results distinguish observed billing, unknown values and provisional totals.
