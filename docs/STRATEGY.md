# Looksy strategy (2026-11-05)

## One line

**Looksy is the treg.to model for Apify: one plugin turns any AI assistant into an SEO expert, an SDR, a market researcher or a social media analyst — 650+ data tools, ask for the job, see the price before the call, pay per result.**

## What treg.to gets right (and what we copy)

| treg.to pattern | Why it works | Looksy version |
| --- | --- | --- |
| "Ask for the job, not the tool" | Agents don't know vendor names; users don't either | `find_tools("google maps leads for roofers")` returns ranked tools for the job |
| Evidence per provider: price, success rate, speed, last OK | Agent picks on data, not a guess | Every tool carries price per result, 30-day success rate, runs, users, last run (public Apify Store stats) |
| Price shown before the call, cost reported after | Removes fear of runaway bills | `get_tool` shows event prices; `run_tool` needs a hard `max_charge_usd` cap; results report the actual charge |
| One credential | Zero setup friction | One Apify key, saved once in the private dashboard or `APIFY_TOKEN` |
| MCP + CLI + `llms.txt` | Works in every agent from one line | Native MCP server bundled in the plugin + `docs/llms.txt`: "set up Looksy - …/llms.txt" |
| Use-case pages and workflows with per-row price | SEO surface + conversion | Each workflow recipe gets a public page with the prompt, steps, tools and cost per row |
| Rankings page (most used / most reliable) | Social proof, freshness | Public "most reliable tools this month" page generated from Store stats |
| "Report a doorway, not an install log" | First-run retention | After setup the agent proposes three concrete jobs, one tailored to the user's work |

## Where we differ on purpose

* **Bring-your-own Apify key, not a prepaid balance.** No billing infrastructure to run; Apify meters usage. Revenue comes from Pay-Per-Event charges on the Actors.
* **Curated, single-publisher catalog.** Every tool is a maintained khadinakbar Actor with a known contract: one maintainer, one output style, one billing style. That is the quality story, and it keeps usage on our Actors.
* **Deliverables, not raw JSON.** treg relays provider bodies verbatim. Looksy ships workflow recipes that end in a CSV, a brief or a CRM-ready export.

## Product priorities

1. **MCP server (0.6.0).** `find_tools`, `list_jobs`, `get_tool`, `run_tool`, `get_run`, `account`. Zero dependencies, stdio, registered in the Claude Code / Codex / Cursor manifests. Biggest gap today: agents have to discover and shell out to scripts.
2. **Evidence-ranked catalog (0.6.0).** Refresh pulls price, success rate, runs and users from the public Store API. Ranking = relevance, then reliability and adoption, cheapest on ties.
3. **Jobs layer (0.6.0).** Named jobs (`maps.leads`, `serp.organic`, `email.verify`, `keywords.volume`, `ai.visibility` …) map to an ordered list of tools, so the agent never guesses.
4. **One-line setup:** `llms.txt` + README "Give this to your agent" block.
5. **Public use-case and rankings pages** generated from the catalog (SEO + YouTube description links). Next.
6. **Hosted remote MCP** so ChatGPT and claude.ai users connect without installing anything. Needs hosting; later.
7. **YouTube content** built on the jobs list once 1–5 are live: one video per job, description links the job page and the Actors used.

## Success metrics

* Installs → first successful paid run in the first session (activation).
* Runs per active user per week (retention).
* Share of runs that succeed on the first tool picked (routing quality).
