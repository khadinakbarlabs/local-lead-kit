# Architecture

One canonical skill drives a contained local app. Codex and Claude manifests adapt that source; native release ZIPs include only their own wrapper. The Python app uses the standard library, a private filesystem workspace, a loopback HTTP interface and a fixed-origin Apify client. No hosted publisher backend or installed background scheduler is involved.

The app validates the niche, territories, target and allowance, reads the current exact Actor builds, schemas and event prices, then persists a plan. User approval is tied to that plan's hash. A changed source requires a new review before another paid start.

The worker discovers companies, deduplicates website hosts for bounded extraction, checks unique addresses, and joins results back to stable business locations. Checkpoints preserve known run IDs and reservations. Unknown starts retain their allowance and stop. Failed stages preserve saved useful data and cannot silently advance to another paid source.

The UI keeps actual counts and partial states, paginates results, and exports spreadsheet-safe CSV files. Optional AI review is supplied by the active assistant using a bounded sample and evidence URLs. Its attribution is checked before notes are attached, but source and semantic truth still require review.

Local access uses a private session cookie, request key, strict Host/Origin checks and content policy. Runtime access data and campaign files are excluded from source and release packages. No account credential or customer dataset is shipped.

Version 0.2 adds one shared task router, an offline Store index, the toolbox CLI and four packaging formats (Claude, Codex, Cursor and portable Agent Plugins). To extend coverage, run `python3 scripts/refresh_catalog.py`, regenerate the directory with `python3 scripts/catalog_guide.py`, and review the catalog diff and curated task menu. Refresh uses only the public Store. The original Maps campaign keeps its three verified stages.

## Looksy Agent 0.4

The shared task vocabulary and intent rules are exported into the static guide. Existing-data and saved-research requests are routed before collection discovery. A validated local draft preserves requested campaign fields in the launcher, with HTML-safe bootstrap serialization. Saved campaign editing restores every request field.

Research areas classify the catalog across multiple purposes. Recipe templates bind exact task cards, ordered dependencies, intake and output contracts for the assistant to adapt. The assistant checks actual schemas and intermediate outputs before paid steps. Local exports prepare flat records for destination import screens with review counts and provenance columns. Destination writes depend on explicit authorization and available host connectors.
