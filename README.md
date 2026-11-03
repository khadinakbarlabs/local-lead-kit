# Local Lead Kit

**Choose a niche, territories and a target. Get a business research list you can inspect.**

Local Lead Kit is an open-source local app with a Codex/Claude skill. It prepares larger business campaigns, collects public website contact details through preconfigured Apify Actors, preserves coverage and review flags, exports CSV files, and lets your active assistant add source-cited research notes.

![Illustrative local businesses](local_lead_kit/static/neighborhood.png)

## Use it in Codex

Add `khadinakbarlabs/local-lead-kit` as a plugin marketplace in Codex, then install **Local Lead Kit**. The equivalent CLI commands are:

```sh
codex plugin marketplace add khadinakbarlabs/local-lead-kit
codex plugin add local-lead-kit@local-lead-kit-marketplace
```

Reload the host, choose the Local Lead Kit skill, and ask it to open the app. It guides the one-time Apify connection and opens a private local browser session. Enter the campaign information in the app; no long workflow prompt is required.

## Use it in Claude Code

```text
/plugin marketplace add khadinakbarlabs/local-lead-kit
/plugin install local-lead-kit@local-lead-kit-marketplace
```

Then use `/local-lead-kit:local-lead-kit` or ask Claude to open Local Lead Kit. This package requires a coding-agent host with local shell/browser access and Python 3.11 or newer. It is not a hosted cloud-chat app or an approved plugin-directory listing.

## What to enter

1. **Niche:** for example, roofing contractors.
2. **Territories:** one or several cities you actually serve.
3. **Target:** 250, 500, 1,000, or a custom value up to the current schema limit of 5,000.
4. **Run allowance:** review the current source prices and approve the specific plan before collection.
5. **Optional AI review:** describe your offer so the assistant can add useful evidence-led notes.

Targets are goals, not guaranteed result counts or market sizes. The app retains actual counts, partial coverage, missing contacts and uncertain addresses. The recorded trial used for the tutorial returned 18 businesses and 15 unique addresses; it does not establish that a 500- or 1,000-result campaign has been verified.

## What you receive

- Business rows with location, website, Maps context and contact coverage.
- Public website contact rows with validation reasons and extraction review flags.
- A searchable local results app and spreadsheet-safe CSV exports.
- Optional AI notes with confidence, cited sources and a next research step.
- Private run checkpoints so a known run can be observed again without another paid start.

The configured sources are [Google Maps Leads Scraper](https://apify.com/khadinakbar/google-maps-leads-scraper), [Bulk Website Contact Extractor](https://apify.com/khadinakbar/bulk-website-contact-extractor), and [Email Address Validator](https://apify.com/khadinakbar/email-address-validator). They are checked against their current builds and schemas before use. Source selection is visible; the package does not silently switch publishers.

SMTP and catch-all probing are disabled in this edition. Basic checks do not confirm an individual mailbox. A public address or an AI note does not establish buying intent or permission to send a message. The app sends no outreach.

## Standalone local app

```sh
git clone https://github.com/khadinakbarlabs/local-lead-kit.git
cd local-lead-kit
python3 -m local_lead_kit serve
```

Use your own Apify account and a securely configured `APIFY_TOKEN`. If the environment needs a private file, ask your assistant to prepare an empty owner-readable file, add the value yourself outside chat, then launch:

```sh
python3 -m local_lead_kit --env-file .env.local serve
```

The app prints a private, single-use launch link. Open it once; the ordinary local app URL replaces it after authentication. Keep launch links and keys out of recordings and public issues. A host's separate MCP OAuth session does not automatically populate the app's API credential.

No Python runtime dependencies, installer hooks, hosted MCP endpoint, publisher proxy or extra model API key are required. Apify collection is billed to your own account. Optional AI review uses your active Codex/Claude session and its normal usage. Keep that assistant active until the requested review is complete.

Data defaults to a private `local-lead-kit` folder under your home data directory. Select a different private folder with `--workspace`. Stop the local server when finished; any cloud run already started must still be checked by its saved run ID.

## Existing results and recovery

The CLI can import three known finished run IDs read-only, inspect campaign status, export results through the app, and apply the active assistant's analysis. See the bundled [skill](skills/local-lead-kit/SKILL.md) and [execution guide](skills/local-lead-kit/references/execution.md).

Uncertain paid starts keep their reservation and stop for inspection. They are never automatically repeated. Known runs can be observed again. A failed or incomplete upstream is not presented as a complete empty-market result.

## Development and verification

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
python3 scripts/package_release.py
```

The tests exercise the worker with offline fixtures, authorization, reservations, duplicate handling, partial failures, paging and exports. Real build/schema/pricing reads and the saved tutorial-run import were checked separately. See [validation](docs/validation.md); native installation, live collection, and marketplace approval are distinct evidence.

[Privacy](PRIVACY.md) · [Security](SECURITY.md) · [Terms](TERMS.md) · [Support](SUPPORT.md) · [Architecture](docs/architecture.md) · [Art attribution](docs/art.md)
